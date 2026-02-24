"""Shared pytest fixtures for integration tests."""

import sys
sys.path.insert(0, "C:/dev/mail-assistant")

import json
import pytest
import chromadb
import httpx
from httpx import ASGITransport
from unittest.mock import AsyncMock

import backend.db.chromadb as chromadb_module
from backend.config import settings
from backend.db.sqlite import init_db
from backend.main import app


# ── Temp SQLite ──────────────────────────────────────────────────────


@pytest.fixture
async def temp_db(tmp_path, monkeypatch):
    """Create a temporary SQLite database for testing."""
    db_path = str(tmp_path / "test_mail.db")
    monkeypatch.setattr(settings, "DB_PATH", db_path)
    await init_db()
    yield db_path


# ── Temp ChromaDB ────────────────────────────────────────────────────


@pytest.fixture
async def temp_chromadb(monkeypatch):
    """Create an ephemeral ChromaDB client for testing."""
    ephemeral_client = chromadb.EphemeralClient()
    collection = ephemeral_client.get_or_create_collection(
        name="emails",
        metadata={"hnsw:space": "cosine"},
    )

    # Reset module-level globals
    monkeypatch.setattr(chromadb_module, "_client", ephemeral_client)
    monkeypatch.setattr(chromadb_module, "_collection", collection)

    # Patch get_client / get_collection to return our ephemeral instances
    monkeypatch.setattr(chromadb_module, "get_client", lambda: ephemeral_client)
    monkeypatch.setattr(chromadb_module, "get_collection", lambda: collection)

    yield collection


# ── Mock LLM ─────────────────────────────────────────────────────────


def _make_classification_response() -> str:
    """Default mock classification JSON."""
    return json.dumps({
        "category": "프로젝트",
        "subject": "테스트 메일 제목",
        "summary": "테스트 메일 요약입니다.",
        "date_extracted": "2025-01-15",
    })


def _make_rag_response() -> str:
    """Default mock RAG answer."""
    return "메일 #1에 따르면 테스트 관련 내용입니다."


@pytest.fixture
async def mock_llm(monkeypatch):
    """Mock all LLM calls so no real API is hit."""

    call_count = {"chat": 0}

    async def fake_chat_completion(messages, model=None, response_format=None):
        call_count["chat"] += 1
        # If response_format requests JSON → classification
        if response_format and response_format.get("type") == "json_object":
            return _make_classification_response()
        # Otherwise → RAG answer
        return _make_rag_response()

    async def fake_create_embedding(texts, model=None):
        # Return a fake 1536-dim vector for each text
        return [[0.01] * 1536 for _ in texts]

    # Patch at the source module AND at all consumer modules
    monkeypatch.setattr(
        "backend.services.llm.chat_completion", fake_chat_completion
    )
    monkeypatch.setattr(
        "backend.services.llm.create_embedding", fake_create_embedding
    )
    # Also patch in consumer modules where `from ... import` binds a local ref
    monkeypatch.setattr(
        "backend.services.classifier.chat_completion", fake_chat_completion
    )
    monkeypatch.setattr(
        "backend.services.embeddings.create_embedding", fake_create_embedding
    )
    monkeypatch.setattr(
        "backend.services.rag.chat_completion", fake_chat_completion
    )

    yield call_count


# ── ASGI test client ─────────────────────────────────────────────────


@pytest.fixture
async def client(temp_db, temp_chromadb, mock_llm):
    """
    httpx.AsyncClient wired to the FastAPI app.
    Depends on temp_db, temp_chromadb, mock_llm so every test
    gets an isolated environment with mocked externals.
    """
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test/api"
    ) as ac:
        yield ac
