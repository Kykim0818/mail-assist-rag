"""Embedding storage and similarity search over email chunks."""

from __future__ import annotations

from backend.db.chromadb import get_collection
from backend.services.llm import create_embedding

# ── Chunking parameters ─────────────────────────────────────────────

_CHUNK_SIZE = 1000
_CHUNK_OVERLAP = 200


def _chunk_text(text: str) -> list[str]:
    """Split *text* into overlapping chunks."""
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + _CHUNK_SIZE
        chunks.append(text[start:end])
        start += _CHUNK_SIZE - _CHUNK_OVERLAP
    return chunks


# ── Public API ───────────────────────────────────────────────────────


async def store_email_embedding(
    email_id: int,
    body: str,
    metadata: dict,
) -> None:
    """Chunk *body*, embed each chunk, and upsert into ChromaDB."""
    chunks = _chunk_text(body)
    if not chunks:
        return

    vectors = await create_embedding(chunks)
    collection = get_collection()

    ids = [f"email_{email_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {**metadata, "email_id": email_id, "chunk_index": i}
        for i in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        embeddings=vectors,
        documents=chunks,
        metadatas=metadatas,
    )


async def search_similar(
    query: str,
    top_k: int = 5,
    category: str | None = None,
) -> list[dict]:
    """Return the *top_k* most similar chunks for *query*."""
    query_vector = await create_embedding([query])
    collection = get_collection()

    kwargs: dict = {
        "query_embeddings": query_vector,
        "n_results": top_k,
        "include": ["documents", "distances", "metadatas"],
    }
    if category is not None:
        kwargs["where"] = {"category": category}

    results = collection.query(**kwargs)

    items: list[dict] = []
    for doc, dist, meta in zip(
        results["documents"][0],
        results["distances"][0],
        results["metadatas"][0],
    ):
        items.append({
            "document": doc,
            "distance": dist,
            "metadata": meta,
            "email_id": meta.get("email_id"),
        })
    return items


async def delete_email_embedding(email_id: int) -> None:
    """Delete all chunks belonging to *email_id*."""
    collection = get_collection()
    collection.delete(where={"email_id": email_id})
