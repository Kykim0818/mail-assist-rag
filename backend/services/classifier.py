"""Email classification & summarization service using LLM."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.services.llm import chat_completion, LLMError

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "classify.txt"
_MAX_BODY_LENGTH = 50000


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _parse_llm_response(raw: str) -> dict:
    """Parse LLM JSON response with fallback on failure."""
    try:
        data = json.loads(raw)
        return {
            "category": data.get("category", "미분류"),
            "subject": data.get("subject", ""),
            "summary": data.get("summary", ""),
            "date_extracted": data.get("date_extracted"),
        }
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning("LLM response parse failed: %s", e)
        return {
            "category": "미분류",
            "subject": "",
            "summary": "분류 실패 — LLM 응답을 파싱할 수 없습니다.",
            "date_extracted": None,
        }


async def classify_and_summarize(
    body: str,
    sender: str | None,
    categories: list[str],
) -> dict:
    """Classify and summarize an email using LLM."""
    # Truncate body if too long
    truncated_body = body[:_MAX_BODY_LENGTH]

    prompt_template = _load_prompt()
    prompt = prompt_template.format(categories=", ".join(categories))

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"발신자: {sender or '알 수 없음'}\n\n메일 본문:\n{truncated_body}"},
    ]

    try:
        raw = await chat_completion(
            messages=messages,
            response_format={"type": "json_object"},
        )
        result = _parse_llm_response(raw)
        return result
    except LLMError as e:
        logger.error("LLM call failed during classification: %s", e)
        return {
            "category": "미분류",
            "subject": "",
            "summary": "분류 보류 — LLM 서비스 오류",
            "date_extracted": None,
            "status": "pending",
        }
