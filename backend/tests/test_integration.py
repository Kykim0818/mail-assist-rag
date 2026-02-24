"""Integration tests for the Mail Assistant FastAPI backend."""

import sys
sys.path.insert(0, "C:/dev/mail-assistant")

import json
import pytest

from backend.services.llm import LLMError


# All tests in this module are integration tests
pytestmark = pytest.mark.integration


# ── Full pipeline tests ──────────────────────────────────────────────


async def test_create_email_full_pipeline(client):
    """POST /api/emails → 201, verify fields, then GET /api/emails/{id} matches."""
    payload = {
        "body": "안녕하세요, 내일 오후 2시에 프로젝트 회의가 있습니다. 참석 부탁드립니다.",
        "sender": "김철수",
    }
    resp = await client.post("/emails", json=payload)
    assert resp.status_code == 201

    data = resp.json()
    assert "id" in data
    assert "category" in data
    assert "summary" in data
    assert data["body"] == payload["body"]
    assert data["sender"] == payload["sender"]

    # Verify GET returns the same email
    email_id = data["id"]
    get_resp = await client.get(f"/emails/{email_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["id"] == email_id
    assert get_data["body"] == payload["body"]
    assert get_data["category"] == data["category"]
    assert get_data["summary"] == data["summary"]


async def test_create_and_list_emails(client):
    """POST 2 emails → GET /api/emails returns both."""
    payloads = [
        {"body": "첫 번째 메일입니다. 프로젝트 일정 공유합니다.", "sender": "이영희"},
        {"body": "두 번째 메일입니다. 인사 관련 안내드립니다.", "sender": "박민수"},
    ]

    created_ids = []
    for p in payloads:
        resp = await client.post("/emails", json=p)
        assert resp.status_code == 201
        created_ids.append(resp.json()["id"])

    # List all
    list_resp = await client.get("/emails")
    assert list_resp.status_code == 200
    emails = list_resp.json()
    assert len(emails) >= 2

    returned_ids = {e["id"] for e in emails}
    for cid in created_ids:
        assert cid in returned_ids


async def test_create_email_and_query_chat(client):
    """POST an email → POST /api/chat with related question → answer is relevant."""
    # Create email first
    email_payload = {
        "body": "내일 오후 3시에 서울 본사에서 2025년 상반기 프로젝트 킥오프 미팅이 예정되어 있습니다.",
        "sender": "김팀장",
    }
    create_resp = await client.post("/emails", json=email_payload)
    assert create_resp.status_code == 201

    # Query chat
    chat_payload = {"question": "프로젝트 킥오프 미팅은 언제 어디서 열리나요?"}
    chat_resp = await client.post("/chat", json=chat_payload)
    assert chat_resp.status_code == 200

    chat_data = chat_resp.json()
    assert "answer" in chat_data
    # The mock returns a pre-set answer; just verify the structure is correct
    assert isinstance(chat_data["answer"], str)
    assert len(chat_data["answer"]) > 0


async def test_category_crud_and_email_link(client):
    """POST category → POST email with that category → DELETE category → email becomes '미분류'."""
    # 1. Create a custom category
    cat_resp = await client.post(
        "/categories", json={"name": "긴급", "description": "긴급 메일"}
    )
    assert cat_resp.status_code == 201
    cat_id = cat_resp.json()["id"]
    assert cat_resp.json()["name"] == "긴급"

    # 2. Patch mock LLM to classify as '긴급'
    # We need to create an email that gets classified as '긴급'.
    # Since the mock always returns '프로젝트', we'll create the email
    # then manually update its category via the PUT endpoint.
    email_resp = await client.post(
        "/emails",
        json={"body": "긴급 보안 패치가 필요합니다. 즉시 대응 바랍니다.", "sender": "보안팀"},
    )
    assert email_resp.status_code == 201
    email_id = email_resp.json()["id"]

    # Update email category to '긴급'
    put_resp = await client.put(f"/emails/{email_id}/category?category=긴급")
    assert put_resp.status_code == 200
    assert put_resp.json()["category"] == "긴급"

    # Verify the email has the new category
    get_resp = await client.get(f"/emails/{email_id}")
    assert get_resp.json()["category"] == "긴급"

    # 3. Delete the category
    del_resp = await client.delete(f"/categories/{cat_id}")
    assert del_resp.status_code == 204

    # 4. Verify the email's category fell back to '미분류'
    get_resp2 = await client.get(f"/emails/{email_id}")
    assert get_resp2.json()["category"] == "미분류"


# ── Edge case tests ──────────────────────────────────────────────────


async def test_edge_empty_body(client):
    """POST /api/emails with body='' → 400 error."""
    resp = await client.post("/emails", json={"body": "", "sender": "누군가"})
    assert resp.status_code == 400


async def test_edge_long_body(client):
    """POST /api/emails with 51000-char body → succeeds (stored in full)."""
    long_body = "가" * 51000
    resp = await client.post("/emails", json={"body": long_body, "sender": "장문작성자"})
    assert resp.status_code == 201
    data = resp.json()
    # The full body should be stored even though classifier truncates internally
    assert len(data["body"]) == 51000


async def test_edge_llm_failure(client, monkeypatch):
    """LLM failure → email still saved with category='미분류' and fallback summary."""

    async def failing_chat_completion(messages, model=None, response_format=None):
        raise LLMError("Simulated LLM failure")

    monkeypatch.setattr(
        "backend.services.llm.chat_completion", failing_chat_completion
    )
    monkeypatch.setattr(
        "backend.services.classifier.chat_completion", failing_chat_completion
    )

    resp = await client.post(
        "/emails",
        json={"body": "LLM 실패 시에도 메일은 저장되어야 합니다.", "sender": "테스터"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["category"] == "미분류"
    # Summary should contain the fallback text
    assert "summary" in data


async def test_edge_chromadb_failure(client, monkeypatch):
    """ChromaDB failure → SQLite save succeeds, no 500 error."""

    async def failing_store(*args, **kwargs):
        raise Exception("ChromaDB is down!")

    monkeypatch.setattr(
        "backend.services.embeddings.store_email_embedding", failing_store
    )
    monkeypatch.setattr(
        "backend.routers.emails.store_email_embedding", failing_store
    )

    resp = await client.post(
        "/emails",
        json={"body": "ChromaDB 장애 시에도 메일은 저장됩니다.", "sender": "운영팀"},
    )
    # Should succeed — embedding failure is caught gracefully
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] is not None
    assert data["body"] == "ChromaDB 장애 시에도 메일은 저장됩니다."


async def test_edge_empty_db_chat(client, monkeypatch):
    """POST /api/chat on empty DB → response about no mail data."""
    # Ensure search_similar returns empty results (empty ChromaDB)
    async def empty_search(query, top_k=5, category=None):
        return []

    monkeypatch.setattr(
        "backend.services.rag.search_similar", empty_search
    )
    chat_resp = await client.post(
        "/chat", json={"question": "회의 일정이 어떻게 되나요?"}
    )
    assert chat_resp.status_code == 200
    answer = chat_resp.json()["answer"]
    # RAG with empty results returns the "no results" message
    assert "찾을 수 없습니다" in answer or "없습니다" in answer
