"""Unit tests for backend.services.rag module."""

import sys
sys.path.insert(0, "C:/dev/mail-assistant")

import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.services.rag import (
    _build_context,
    answer_question,
)
from backend.services.llm import LLMError


class TestBuildContext:
    """Tests for _build_context function."""

    async def test_build_context_within_limit(self):
        """All results under limit should be included."""
        results = [
            {
                "document": "First email chunk about meetings",
                "metadata": {"email_id": 1}
            },
            {
                "document": "Second email chunk about reports",
                "metadata": {"email_id": 2}
            },
            {
                "document": "Third email chunk from email 1",
                "metadata": {"email_id": 1}
            }
        ]
        
        context, source_ids = _build_context(results)
        
        # All chunks should be included
        assert "First email chunk" in context
        assert "Second email chunk" in context
        assert "Third email chunk" in context
        # Source IDs should be sorted and unique
        assert source_ids == [1, 2]
        # Format should include email markers
        assert "[메일 #1]" in context
        assert "[메일 #2]" in context

    async def test_build_context_exceeds_limit(self):
        """Results exceeding limit should be truncated."""
        # Create results that exceed 16000 chars
        large_chunk = "x" * 12000
        results = [
            {"document": large_chunk, "metadata": {"email_id": 1}},
            {"document": large_chunk, "metadata": {"email_id": 2}},
            {"document": "This should not be included", "metadata": {"email_id": 3}}
        ]
        
        context, source_ids = _build_context(results)
        
        # Context should not exceed limit significantly
        assert len(context) <= 16100  # Small buffer for formatting
        # Third chunk should not be included
        assert "This should not be included" not in context
        # Only first result should be included
        assert 3 not in source_ids

    async def test_build_context_empty_results(self):
        """Empty results should return empty context."""
        context, source_ids = _build_context([])
        
        assert context == ""
        assert source_ids == []

    async def test_build_context_missing_email_id(self):
        """Results with missing email_id should be handled gracefully."""
        results = [
            {"document": "Chunk without email_id", "metadata": {}},
            {"document": "Chunk with email_id", "metadata": {"email_id": 5}}
        ]
        
        context, source_ids = _build_context(results)
        
        # Should not crash
        assert "Chunk without email_id" in context
        assert "Chunk with email_id" in context
        assert source_ids == [5]


class TestAnswerQuestion:
    """Tests for answer_question function."""

    async def test_answer_question_success(self, monkeypatch):
        """Successful flow should return answer with sources."""
        # Mock search_similar
        async def mock_search_similar(query, top_k=5):
            return [
                {
                    "document": "Meeting scheduled for tomorrow at 10 AM",
                    "metadata": {"email_id": 10, "category": "업무"}
                },
                {
                    "document": "Please confirm your attendance",
                    "metadata": {"email_id": 10, "category": "업무"}
                }
            ]
        
        # Mock chat_completion
        async def mock_chat_completion(messages):
            return "내일 오전 10시에 회의가 예정되어 있습니다."
        
        monkeypatch.setattr("backend.services.rag.search_similar", mock_search_similar)
        monkeypatch.setattr("backend.services.rag.chat_completion", mock_chat_completion)
        
        result = await answer_question("내일 회의가 언제인가요?")
        
        assert result["answer"] == "내일 오전 10시에 회의가 예정되어 있습니다."
        assert 10 in result["source_ids"]
        assert len(result["sources"]) > 0
        assert result["sources"][0]["email_id"] == 10

    async def test_answer_question_no_results(self, monkeypatch):
        """No search results should return appropriate message."""
        # Mock search_similar to return empty list
        async def mock_search_similar(query, top_k=5):
            return []
        
        monkeypatch.setattr("backend.services.rag.search_similar", mock_search_similar)
        
        result = await answer_question("존재하지 않는 질문")
        
        assert "관련된 메일 정보를 찾을 수 없습니다" in result["answer"]
        assert result["source_ids"] == []
        assert result["sources"] == []

    async def test_answer_question_llm_failure(self, monkeypatch):
        """LLM failure should return error message."""
        # Mock search_similar
        async def mock_search_similar(query, top_k=5):
            return [
                {"document": "Some content", "metadata": {"email_id": 5}}
            ]
        
        # Mock chat_completion to raise error
        async def mock_chat_completion(messages):
            raise LLMError("API quota exceeded")
        
        monkeypatch.setattr("backend.services.rag.search_similar", mock_search_similar)
        monkeypatch.setattr("backend.services.rag.chat_completion", mock_chat_completion)
        
        result = await answer_question("테스트 질문")
        
        assert "죄송합니다" in result["answer"]
        assert "오류가 발생했습니다" in result["answer"]
        assert result["source_ids"] == []
        assert result["sources"] == []

    async def test_answer_question_with_chat_history(self, monkeypatch):
        """Chat history should be passed to LLM."""
        messages_received = None
        
        async def mock_search_similar(query, top_k=5):
            return [{"document": "content", "metadata": {"email_id": 1}}]
        
        async def mock_chat_completion(messages):
            nonlocal messages_received
            messages_received = messages
            return "답변입니다."
        
        monkeypatch.setattr("backend.services.rag.search_similar", mock_search_similar)
        monkeypatch.setattr("backend.services.rag.chat_completion", mock_chat_completion)
        
        chat_history = [
            {"role": "user", "content": "이전 질문"},
            {"role": "assistant", "content": "이전 답변"}
        ]
        
        result = await answer_question("후속 질문", chat_history=chat_history)
        
        # Verify chat history was included
        assert messages_received is not None
        # Should have system prompt + chat history + current question
        assert len(messages_received) >= 4
        assert messages_received[1] == {"role": "user", "content": "이전 질문"}
        assert messages_received[2] == {"role": "assistant", "content": "이전 답변"}

    async def test_answer_question_source_preview(self, monkeypatch):
        """Sources should include preview text truncated to 100 chars."""
        long_text = "x" * 200
        
        async def mock_search_similar(query, top_k=5):
            return [
                {"document": long_text, "metadata": {"email_id": 99}}
            ]
        
        async def mock_chat_completion(messages):
            return "답변"
        
        monkeypatch.setattr("backend.services.rag.search_similar", mock_search_similar)
        monkeypatch.setattr("backend.services.rag.chat_completion", mock_chat_completion)
        
        result = await answer_question("질문")
        
        # Preview should be truncated
        assert len(result["sources"][0]["preview"]) == 100
        assert result["sources"][0]["preview"] == long_text[:100]
