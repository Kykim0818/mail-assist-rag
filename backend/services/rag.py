"""RAG pipeline — answer questions grounded in stored email content."""

from __future__ import annotations

import logging
from pathlib import Path

from backend.services.embeddings import search_similar
from backend.services.llm import LLMError, chat_completion

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "qa.txt"
_MAX_CONTEXT_CHARS = 16_000  # ~8 000 tokens


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _build_context(results: list[dict]) -> tuple[str, list[int]]:
    """Build context string from search results, respecting token limit."""
    context_parts: list[str] = []
    source_ids: set[int] = set()
    total_chars = 0

    for result in results:
        chunk_text = result.get("document", "")
        email_id = result.get("metadata", {}).get("email_id")
        if total_chars + len(chunk_text) > _MAX_CONTEXT_CHARS:
            break
        context_parts.append(f"[메일 #{email_id}] {chunk_text}")
        if email_id is not None:
            source_ids.add(email_id)
        total_chars += len(chunk_text)

    return "\n\n---\n\n".join(context_parts), sorted(source_ids)


async def answer_question(
    question: str,
    chat_history: list[dict] | None = None,
) -> dict:
    """Answer a question using the RAG pipeline."""
    chat_history = chat_history or []

    # Search for relevant email chunks
    results = await search_similar(question, top_k=5)

    if not results:
        return {
            "answer": "관련된 메일 정보를 찾을 수 없습니다. 먼저 메일을 등록해주세요.",
            "source_ids": [],
            "sources": [],
        }

    context, source_ids = _build_context(results)
    prompt_template = _load_prompt()

    messages = [
        {"role": "system", "content": prompt_template.format(context=context)},
        *chat_history,
        {"role": "user", "content": question},
    ]

    try:
        answer = await chat_completion(messages=messages)
        return {
            "answer": answer,
            "source_ids": source_ids,
            "sources": [
                {
                    "email_id": r.get("metadata", {}).get("email_id"),
                    "preview": r.get("document", "")[:100],
                }
                for r in results
                if r.get("metadata", {}).get("email_id") in source_ids
            ],
        }
    except LLMError as e:
        logger.error("RAG answer failed: %s", e)
        return {
            "answer": "죄송합니다. 답변 생성 중 오류가 발생했습니다.",
            "source_ids": [],
            "sources": [],
        }
