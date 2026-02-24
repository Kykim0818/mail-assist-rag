"""Unit tests for backend.services.classifier module."""

import sys
sys.path.insert(0, "C:/dev/mail-assistant")

import pytest
from unittest.mock import AsyncMock

from backend.services.classifier import _parse_llm_response, classify_and_summarize
from backend.services.llm import LLMError


class TestParseResponse:
    """Tests for _parse_llm_response function."""

    async def test_parse_llm_response_valid_json(self):
        """Valid JSON should be parsed correctly."""
        raw = '{"category": "업무", "subject": "회의 요청", "summary": "내일 10시 회의", "date_extracted": "2026-02-25"}'
        result = _parse_llm_response(raw)
        
        assert result["category"] == "업무"
        assert result["subject"] == "회의 요청"
        assert result["summary"] == "내일 10시 회의"
        assert result["date_extracted"] == "2026-02-25"

    async def test_parse_llm_response_invalid_json(self):
        """Invalid JSON should return fallback dict."""
        raw = "This is not JSON at all!"
        result = _parse_llm_response(raw)
        
        assert result["category"] == "미분류"
        assert result["subject"] == ""
        assert "분류 실패" in result["summary"]
        assert result["date_extracted"] is None

    async def test_parse_llm_response_partial_json(self):
        """Partial/missing fields should be handled with defaults."""
        raw = '{"category": "개인"}'
        result = _parse_llm_response(raw)
        
        assert result["category"] == "개인"
        assert result["subject"] == ""
        assert result["summary"] == ""
        assert result["date_extracted"] is None


class TestClassifyAndSummarize:
    """Tests for classify_and_summarize function."""

    async def test_classify_and_summarize_success(self, monkeypatch):
        """Successful LLM call should return parsed result."""
        async def mock_chat_completion(messages, response_format=None):
            return '{"category": "쇼핑", "subject": "주문 완료", "summary": "노트북 주문 확인", "date_extracted": "2026-02-24"}'
        
        monkeypatch.setattr("backend.services.classifier.chat_completion", mock_chat_completion)
        
        result = await classify_and_summarize(
            body="귀하의 주문이 완료되었습니다. 노트북 1대.",
            sender="shop@example.com",
            categories=["업무", "개인", "쇼핑"]
        )
        
        assert result["category"] == "쇼핑"
        assert result["subject"] == "주문 완료"
        assert result["summary"] == "노트북 주문 확인"
        assert result["date_extracted"] == "2026-02-24"
        assert "status" not in result

    async def test_classify_and_summarize_llm_failure(self, monkeypatch):
        """LLM failure should return fallback dict with status=pending."""
        async def mock_chat_completion(messages, response_format=None):
            raise LLMError("API rate limit exceeded")
        
        monkeypatch.setattr("backend.services.classifier.chat_completion", mock_chat_completion)
        
        result = await classify_and_summarize(
            body="Some email body",
            sender="test@example.com",
            categories=["업무", "개인"]
        )
        
        assert result["category"] == "미분류"
        assert result["subject"] == ""
        assert "분류 보류" in result["summary"]
        assert result["date_extracted"] is None
        assert result["status"] == "pending"

    async def test_classify_and_summarize_truncation(self, monkeypatch):
        """Very long body should be truncated before sending."""
        called_with_body = None
        
        async def mock_chat_completion(messages, response_format=None):
            nonlocal called_with_body
            called_with_body = messages[1]["content"]
            return '{"category": "업무", "subject": "긴 메일", "summary": "요약", "date_extracted": null}'
        
        monkeypatch.setattr("backend.services.classifier.chat_completion", mock_chat_completion)
        
        long_body = "x" * 60000  # Exceeds _MAX_BODY_LENGTH (50000)
        result = await classify_and_summarize(
            body=long_body,
            sender="sender@test.com",
            categories=["업무"]
        )
        
        # Verify the body was truncated
        assert len(called_with_body) < len(long_body) + 100  # Account for sender prefix
        assert result["category"] == "업무"
