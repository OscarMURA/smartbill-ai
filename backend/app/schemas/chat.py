from uuid import UUID
from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    invoice_id: UUID
    question: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    answer: str
    mode: Literal["digitalocean", "demo"]
    evidence: list[str] = Field(default_factory=list)
