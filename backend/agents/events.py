"""Progress emitted by an agent run, independent of HTTP and SSE."""

from typing import Literal

from pydantic import BaseModel


class TraceEvent(BaseModel):
    type: Literal["status", "tool", "answer_delta", "answer", "error", "done"]
    message: str
