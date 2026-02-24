import logging
from fastapi import APIRouter

from backend.db.sqlite import get_email_by_id
from backend.models import ChatInput, ChatResponse
from backend.services.rag import answer_question

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(data: ChatInput):
    """Answer a question using RAG over stored emails."""
    result = await answer_question(
        question=data.question,
        chat_history=data.chat_history,
    )

    # Enrich sources with email details from SQLite
    enriched_sources = []
    seen_ids = set()
    for source_id in result.get("source_ids", []):
        if source_id in seen_ids:
            continue
        seen_ids.add(source_id)
        email = await get_email_by_id(source_id)
        if email:
            enriched_sources.append({
                "email_id": email["id"],
                "sender": email.get("sender"),
                "subject": email.get("subject"),
                "summary": email.get("summary", "")[:200],
            })

    return ChatResponse(
        answer=result["answer"],
        source_ids=result.get("source_ids", []),
        sources=enriched_sources,
    )
