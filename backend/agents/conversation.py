"""Completed turns supplied with a follow-up question."""

from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    answer: str = Field(min_length=1)
    # None when that turn was asked with generation left off.
    generation: int | None = Field(default=None, ge=1, le=9)


def format_user_message(prompt: str, generation: int | None) -> str:
    """The user turn both agents send.

    The generation prefix lives in the user message, not the system prompt, so
    the two implementations ask the same question. It is omitted when no
    generation was selected for that turn.
    """
    if generation is None:
        return prompt
    return f"Selected generation: {generation}\n\n{prompt}"
