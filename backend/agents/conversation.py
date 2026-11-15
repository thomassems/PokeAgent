"""Completed turns supplied with a follow-up question."""

from typing import Literal

from pydantic import BaseModel, Field

Game = Literal["main", "go"]


class ConversationTurn(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    answer: str = Field(min_length=1)
    # None when that turn was asked with generation left off.
    generation: int | None = Field(default=None, ge=1, le=9)
    # Main series when a client from before the game selector omits it.
    game: Game = "main"


def format_user_message(
    prompt: str, generation: int | None, game: Game = "main"
) -> str:
    """The user turn both agents send.

    The prefix lives in the user message, not the system prompt, so the two
    implementations ask the same question. A GO turn says which game it is
    and does not carry a generation, even if one is stored in the client.
    A main-series turn names a generation only when one was selected.
    """
    if game == "go":
        return f"Selected game: Pokemon GO\n\n{prompt}"
    if generation is None:
        return prompt
    return f"Selected generation: {generation}\n\n{prompt}"
