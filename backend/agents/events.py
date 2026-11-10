"""Progress emitted by an agent run, independent of HTTP and SSE."""

from typing import Literal

from pydantic import BaseModel


class RunMetrics(BaseModel):
    """What one run cost, for comparing the two implementations.

    Tokens rather than dollars. The counts come from the provider and stay true
    whatever the price list says, while a rate baked in here would go stale
    silently. The frontend converts to money at the point of display.

    `input_tokens` is the sum over every model call in the run, not the size of
    the final message list. Each step resends the whole conversation plus all
    seven tool schemas, and the provider charges for each resend, so the sum is
    what the run actually cost.
    """

    steps: int
    tool_calls: int
    input_tokens: int
    output_tokens: int


class TraceEvent(BaseModel):
    type: Literal[
        "status", "tool", "answer_delta", "answer", "error", "done", "metrics"
    ]
    message: str
    # Set only on a "metrics" event, which both agents emit once, immediately
    # after the answer. Optional rather than a separate event class: one extra
    # shape does not earn a discriminated union yet.
    metrics: RunMetrics | None = None
