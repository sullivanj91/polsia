from datetime import datetime

from pydantic import BaseModel


class MemoryEntryOut(BaseModel):
    id: int
    category: str
    title: str
    content: str
    source: str | None
    tags: list[str] | None
    chroma_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MemoryEntryCreate(BaseModel):
    category: str
    title: str
    content: str
    source: str | None = None
    tags: list[str] | None = None
