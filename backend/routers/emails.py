import logging
from fastapi import APIRouter, HTTPException, Query

from backend.db.sqlite import (
    insert_email, get_emails, get_email_by_id, update_email_category, get_categories
)
from backend.services.classifier import classify_and_summarize
from backend.services.embeddings import store_email_embedding, delete_email_embedding
from backend.models import EmailInput, EmailResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["emails"])


@router.post("/emails", response_model=EmailResponse, status_code=201)
async def create_email(data: EmailInput):
    """Receive email text, classify, summarize, store in SQLite + ChromaDB."""
    if not data.body or not data.body.strip():
        raise HTTPException(status_code=400, detail="메일 본문은 비어있을 수 없습니다.")

    # Get available category names
    categories_rows = await get_categories()
    category_names = [c["name"] for c in categories_rows]

    # Classify and summarize via LLM
    result = await classify_and_summarize(
        body=data.body,
        sender=data.sender,
        categories=category_names,
    )

    # Build email record
    email_data = {
        "sender": data.sender,
        "subject": result.get("subject") or data.subject,
        "body": data.body,
        "summary": result.get("summary", ""),
        "category": result.get("category", "미분류"),
        "date_extracted": result.get("date_extracted"),
        "status": result.get("status", "completed"),
    }

    # Insert into SQLite
    email_id = await insert_email(email_data)

    # Store embeddings in ChromaDB (non-blocking failure)
    try:
        await store_email_embedding(
            email_id=email_id,
            body=data.body,
            metadata={
                "category": email_data["category"],
                "sender": data.sender or "",
                "subject": email_data["subject"] or "",
            },
        )
    except Exception as e:
        logger.error("Failed to store embedding for email %d: %s", email_id, e)

    # Return the saved email
    saved = await get_email_by_id(email_id)
    return saved


@router.get("/emails", response_model=list[EmailResponse])
async def list_emails(
    category: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Get emails with optional category filter."""
    emails = await get_emails(category=category, limit=limit, offset=offset)
    return emails


@router.get("/emails/{email_id}", response_model=EmailResponse)
async def get_email(email_id: int):
    """Get a single email by ID."""
    email = await get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다.")
    return email


@router.put("/emails/{email_id}/category")
async def change_email_category(email_id: int, category: str = Query(...)):
    """Manually change email category."""
    email = await get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다.")
    await update_email_category(email_id, category)
    return {"id": email_id, "category": category}


@router.delete("/emails/{email_id}", status_code=204)
async def remove_email(email_id: int):
    """Delete email from SQLite and ChromaDB."""
    email = await get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="메일을 찾을 수 없습니다.")
    
    # Delete from ChromaDB first (non-critical)
    try:
        await delete_email_embedding(email_id)
    except Exception as e:
        logger.error("Failed to delete embedding for email %d: %s", email_id, e)
    
    # Delete from SQLite
    from backend.db.sqlite import get_db_path
    import aiosqlite
    db_path = await get_db_path()
    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute("DELETE FROM emails WHERE id = ?", (email_id,))
        await db.commit()
