"""Request and response models for the API boundary.

Everything crossing into the backend is validated here rather than inside the
agent, so `agents/` can assume its input is already well formed and stays free
of HTTP concerns.
"""

from pydantic import BaseModel, Field

# Generous for a team-building question, which normally runs a few hundred
# characters, while still bounding what one request can cost. An unbounded
# prompt is a spend attack: the caller gets to choose how many tokens you pay
# for. Roughly four characters per token, so this caps input at ~500 tokens.
MAX_PROMPT_CHARS = 2000


class RunRequest(BaseModel):
    """A single agent run, requested by the browser."""

    prompt: str = Field(
        min_length=1,
        max_length=MAX_PROMPT_CHARS,
        description="The user's team-building question.",
    )
