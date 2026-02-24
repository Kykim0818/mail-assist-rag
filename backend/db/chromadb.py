"""ChromaDB persistent client — vector store for email embeddings."""

from __future__ import annotations

import chromadb

from backend.config import settings

_client: chromadb.ClientAPI | None = None
_collection = None


def get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
    return _client


def get_collection():
    global _collection
    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(
            name="emails",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection
