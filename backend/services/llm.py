"""GitHub Models API client — chat completions & embeddings via httpx."""

from __future__ import annotations

import httpx

from backend.config import settings

_BASE_URL = "https://models.github.ai"
_TIMEOUT = 30.0


# ── Custom exceptions ────────────────────────────────────────────────


class LLMError(Exception):
    """Base exception for LLM service errors."""


class RateLimitError(LLMError):
    """Raised on HTTP 429 — rate limit exceeded."""


class AuthenticationError(LLMError):
    """Raised on HTTP 401/403 — bad or missing credentials."""


class LLMTimeoutError(LLMError):
    """Raised when the request times out."""


# ── Helpers ──────────────────────────────────────────────────────────


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }


def _handle_error(exc: httpx.HTTPStatusError) -> None:
    """Translate httpx status errors into domain exceptions."""
    status = exc.response.status_code

    if status == 429:
        retry_after = exc.response.headers.get("retry-after")
        msg = f"Rate limited (429). Retry-After: {retry_after}"
        raise RateLimitError(msg) from exc

    if status in (401, 403):
        raise AuthenticationError(
            f"Authentication failed ({status}): {exc.response.text}"
        ) from exc

    raise LLMError(
        f"HTTP {status}: {exc.response.text}"
    ) from exc


# ── Public API ───────────────────────────────────────────────────────


async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    response_format: dict | None = None,
) -> str:
    """Send a chat-completion request and return the assistant content."""
    body: dict = {
        "model": model or settings.MODEL_NAME,
        "messages": messages,
    }
    if response_format is not None:
        body["response_format"] = response_format

    try:
        async with httpx.AsyncClient(
            base_url=_BASE_URL, timeout=_TIMEOUT, verify=settings.SSL_VERIFY
        ) as client:
            resp = await client.post(
                "/inference/chat/completions",
                headers=_headers(),
                json=body,
            )
            resp.raise_for_status()
    except httpx.TimeoutException as exc:
        raise LLMTimeoutError("Chat completion request timed out") from exc
    except httpx.HTTPStatusError as exc:
        _handle_error(exc)

    return resp.json()["choices"][0]["message"]["content"]


async def create_embedding(
    texts: list[str],
    model: str | None = None,
) -> list[list[float]]:
    """Create embeddings for a list of texts."""
    body: dict = {
        "model": model or settings.EMBEDDING_MODEL,
        "input": texts,
    }

    try:
        async with httpx.AsyncClient(
            base_url=_BASE_URL, timeout=_TIMEOUT, verify=settings.SSL_VERIFY
        ) as client:
            resp = await client.post(
                "/inference/embeddings",
                headers=_headers(),
                json=body,
            )
            resp.raise_for_status()
    except httpx.TimeoutException as exc:
        raise LLMTimeoutError("Embedding request timed out") from exc
    except httpx.HTTPStatusError as exc:
        _handle_error(exc)

    return [item["embedding"] for item in resp.json()["data"]]
