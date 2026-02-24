"""Unit tests for backend.services.llm module."""

import sys
sys.path.insert(0, "C:/dev/mail-assistant")

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from backend.services.llm import (
    chat_completion,
    create_embedding,
    RateLimitError,
    AuthenticationError,
    LLMTimeoutError,
    LLMError,
)


class TestChatCompletion:
    """Tests for chat_completion function."""

    async def test_chat_completion_success(self, monkeypatch):
        """Successful API call should return content string."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "안녕하세요, 무엇을 도와드릴까요?"}}]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_post = AsyncMock(return_value=mock_response)
        
        class MockAsyncClient:
            def __init__(self, *args, **kwargs):
                self.post = mock_post
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, *args):
                pass
        
        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)
        
        messages = [{"role": "user", "content": "Hello"}]
        result = await chat_completion(messages)
        
        assert result == "안녕하세요, 무엇을 도와드릴까요?"
        assert mock_post.called

    async def test_chat_completion_rate_limit(self, monkeypatch):
        """HTTP 429 should raise RateLimitError."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.headers = {"retry-after": "60"}
        
        def mock_raise(*args, **kwargs):
            raise httpx.HTTPStatusError("429", request=MagicMock(), response=mock_response)
        
        mock_response.raise_for_status = mock_raise
        mock_post = AsyncMock(return_value=mock_response)
        
        class MockAsyncClient:
            def __init__(self, *args, **kwargs):
                self.post = mock_post
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, *args):
                pass
        
        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)
        
        messages = [{"role": "user", "content": "test"}]
        
        with pytest.raises(RateLimitError) as exc_info:
            await chat_completion(messages)
        
        assert "429" in str(exc_info.value)

    async def test_chat_completion_auth_error(self, monkeypatch):
        """HTTP 401 should raise AuthenticationError."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid token"
        
        def mock_raise(*args, **kwargs):
            raise httpx.HTTPStatusError("401", request=MagicMock(), response=mock_response)
        
        mock_response.raise_for_status = mock_raise
        mock_post = AsyncMock(return_value=mock_response)
        
        class MockAsyncClient:
            def __init__(self, *args, **kwargs):
                self.post = mock_post
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, *args):
                pass
        
        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)
        
        messages = [{"role": "user", "content": "test"}]
        
        with pytest.raises(AuthenticationError) as exc_info:
            await chat_completion(messages)
        
        assert "401" in str(exc_info.value)

    async def test_chat_completion_timeout(self, monkeypatch):
        """Timeout should raise LLMTimeoutError."""
        async def mock_post(*args, **kwargs):
            raise httpx.TimeoutException("Request timed out")
        
        class MockAsyncClient:
            def __init__(self, *args, **kwargs):
                self.post = mock_post
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, *args):
                pass
        
        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)
        
        messages = [{"role": "user", "content": "test"}]
        
        with pytest.raises(LLMTimeoutError):
            await chat_completion(messages)


class TestCreateEmbedding:
    """Tests for create_embedding function."""

    async def test_create_embedding_success(self, monkeypatch):
        """Successful embedding call should return list of vectors."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1, 0.2, 0.3]},
                {"embedding": [0.4, 0.5, 0.6]},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_post = AsyncMock(return_value=mock_response)
        
        class MockAsyncClient:
            def __init__(self, *args, **kwargs):
                self.post = mock_post
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, *args):
                pass
        
        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)
        
        texts = ["first text", "second text"]
        result = await create_embedding(texts)
        
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        assert mock_post.called

    async def test_create_embedding_rate_limit(self, monkeypatch):
        """HTTP 429 should raise RateLimitError."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit"
        mock_response.headers = {}
        
        def mock_raise(*args, **kwargs):
            raise httpx.HTTPStatusError("429", request=MagicMock(), response=mock_response)
        
        mock_response.raise_for_status = mock_raise
        mock_post = AsyncMock(return_value=mock_response)
        
        class MockAsyncClient:
            def __init__(self, *args, **kwargs):
                self.post = mock_post
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, *args):
                pass
        
        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)
        
        with pytest.raises(RateLimitError):
            await create_embedding(["test"])

    async def test_create_embedding_generic_error(self, monkeypatch):
        """HTTP 500 should raise generic LLMError."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        
        def mock_raise(*args, **kwargs):
            raise httpx.HTTPStatusError("500", request=MagicMock(), response=mock_response)
        
        mock_response.raise_for_status = mock_raise
        mock_post = AsyncMock(return_value=mock_response)
        
        class MockAsyncClient:
            def __init__(self, *args, **kwargs):
                self.post = mock_post
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, *args):
                pass
        
        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)
        
        with pytest.raises(LLMError) as exc_info:
            await create_embedding(["test"])
        
        assert "500" in str(exc_info.value)
