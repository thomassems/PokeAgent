"""Completed turns supplied with a follow-up question."""

from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    answer: str = Field(min_length=1)
    generation: int = Field(ge=1, le=9)
