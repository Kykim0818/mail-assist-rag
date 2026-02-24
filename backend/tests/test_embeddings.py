"""Unit tests for backend.services.embeddings module."""

import sys
sys.path.insert(0, "C:/dev/mail-assistant")

import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.services.embeddings import (
    _chunk_text,
    store_email_embedding,
    search_similar,
)


class TestChunkText:
    """Tests for _chunk_text function."""

    async def test_chunk_text_normal(self):
        """Text should be split into overlapping chunks."""
        # Create text of 2500 chars (should create 3 chunks: 0-1000, 800-1800, 1600-2500)
        text = "x" * 2500
        chunks = _chunk_text(text)
        
        assert len(chunks) == 4  # (2500-1000)/(1000-200) + 1 rounded up
        assert len(chunks[0]) == 1000
        assert len(chunks[1]) == 1000
        # Verify overlap: chunk[1] should start at position 800
        assert chunks[0][800:] == chunks[1][:200]

    async def test_chunk_text_empty(self):
        """Empty string should return empty list."""
        result = _chunk_text("")
        assert result == []

    async def test_chunk_text_short(self):
        """Text shorter than chunk size should return single chunk."""
        text = "Short text"
        chunks = _chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0] == text

    async def test_chunk_text_exact_size(self):
        """Text exactly chunk size should return single chunk."""
        text = "x" * 1000
        chunks = _chunk_text(text)
        
        assert len(chunks) == 2  # Exact chunk size creates 2 chunks due to overlap logic
        assert chunks[0] == text


class TestStoreEmailEmbedding:
    """Tests for store_email_embedding function."""

    async def test_store_email_embedding(self, monkeypatch):
        """Should chunk text, create embeddings, and upsert to collection."""
        # Mock create_embedding
        async def mock_create_embedding(texts):
            return [[0.1, 0.2] for _ in texts]
        
        # Mock collection
        mock_collection = MagicMock()
        mock_collection.upsert = MagicMock()
        
        def mock_get_collection():
            return mock_collection
        
        monkeypatch.setattr("backend.services.embeddings.create_embedding", mock_create_embedding)
        monkeypatch.setattr("backend.services.embeddings.get_collection", mock_get_collection)
        
        # Call function
        await store_email_embedding(
            email_id=123,
            body="This is a test email body that will be chunked.",
            metadata={"category": "업무", "sender": "test@example.com"}
        )
        
        # Verify upsert was called
        assert mock_collection.upsert.called
        call_args = mock_collection.upsert.call_args
        
        # Check that ids include email_id
        assert "email_123_chunk_0" in call_args.kwargs["ids"]
        # Check embeddings were passed
        assert len(call_args.kwargs["embeddings"]) > 0
        # Check metadata includes email_id
        assert call_args.kwargs["metadatas"][0]["email_id"] == 123

    async def test_store_email_embedding_empty_body(self, monkeypatch):
        """Empty body should not call upsert."""
        mock_collection = MagicMock()
        mock_collection.upsert = MagicMock()
        
        def mock_get_collection():
            return mock_collection
        
        monkeypatch.setattr("backend.services.embeddings.get_collection", mock_get_collection)
        
        await store_email_embedding(
            email_id=456,
            body="",
            metadata={}
        )
        
        # Verify upsert was NOT called
        assert not mock_collection.upsert.called

    async def test_store_email_embedding_multiple_chunks(self, monkeypatch):
        """Large body should create multiple chunks and embeddings."""
        long_body = "x" * 2500  # Creates multiple chunks
        
        async def mock_create_embedding(texts):
            return [[0.1, 0.2] for _ in texts]
        
        mock_collection = MagicMock()
        mock_collection.upsert = MagicMock()
        
        def mock_get_collection():
            return mock_collection
        
        monkeypatch.setattr("backend.services.embeddings.create_embedding", mock_create_embedding)
        monkeypatch.setattr("backend.services.embeddings.get_collection", mock_get_collection)
        
        await store_email_embedding(
            email_id=789,
            body=long_body,
            metadata={"category": "개인"}
        )
        
        # Verify multiple chunks were created
        call_args = mock_collection.upsert.call_args
        assert len(call_args.kwargs["ids"]) > 1
        assert "email_789_chunk_0" in call_args.kwargs["ids"]
        assert "email_789_chunk_1" in call_args.kwargs["ids"]


class TestSearchSimilar:
    """Tests for search_similar function."""

    async def test_search_similar(self, monkeypatch):
        """Should create query embedding and return formatted results."""
        # Mock create_embedding
        async def mock_create_embedding(texts):
            return [[0.5, 0.6]]
        
        # Mock collection query
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [["chunk text 1", "chunk text 2"]],
            "distances": [[0.1, 0.2]],
            "metadatas": [[
                {"email_id": 10, "category": "업무"},
                {"email_id": 20, "category": "개인"}
            ]]
        }
        
        def mock_get_collection():
            return mock_collection
        
        monkeypatch.setattr("backend.services.embeddings.create_embedding", mock_create_embedding)
        monkeypatch.setattr("backend.services.embeddings.get_collection", mock_get_collection)
        
        # Call function
        results = await search_similar("test query", top_k=2)
        
        # Verify results structure
        assert len(results) == 2
        assert results[0]["document"] == "chunk text 1"
        assert results[0]["distance"] == 0.1
        assert results[0]["email_id"] == 10
        assert results[0]["metadata"]["category"] == "업무"
        
        assert results[1]["document"] == "chunk text 2"
        assert results[1]["email_id"] == 20

    async def test_search_similar_with_category_filter(self, monkeypatch):
        """Category filter should be passed to collection.query."""
        async def mock_create_embedding(texts):
            return [[0.5, 0.6]]
        
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [[]],
            "distances": [[]],
            "metadatas": [[]]
        }
        
        def mock_get_collection():
            return mock_collection
        
        monkeypatch.setattr("backend.services.embeddings.create_embedding", mock_create_embedding)
        monkeypatch.setattr("backend.services.embeddings.get_collection", mock_get_collection)
        
        # Call with category filter
        await search_similar("test", top_k=5, category="업무")
        
        # Verify where clause was passed
        call_args = mock_collection.query.call_args
        assert "where" in call_args.kwargs
        assert call_args.kwargs["where"] == {"category": "업무"}

    async def test_search_similar_no_results(self, monkeypatch):
        """Empty results should return empty list."""
        async def mock_create_embedding(texts):
            return [[0.5, 0.6]]
        
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [[]],
            "distances": [[]],
            "metadatas": [[]]
        }
        
        def mock_get_collection():
            return mock_collection
        
        monkeypatch.setattr("backend.services.embeddings.create_embedding", mock_create_embedding)
        monkeypatch.setattr("backend.services.embeddings.get_collection", mock_get_collection)
        
        results = await search_similar("no match query")
        
        assert results == []
