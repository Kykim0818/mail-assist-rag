from pydantic import BaseModel


class EmailInput(BaseModel):
    body: str
    sender: str | None = None
    subject: str | None = None


class EmailResponse(BaseModel):
    id: int
    body: str
    sender: str | None
    subject: str | None
    category: str
    summary: str
    created_at: str


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None


class ChatInput(BaseModel):
    question: str
    chat_history: list[dict] = []


class ChatResponse(BaseModel):
    answer: str
    source_ids: list[int] = []
    sources: list[dict] = []
