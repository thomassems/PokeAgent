import logging
from collections.abc import Iterator
from typing import Literal

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, Field

from agents import custom, framework
from agents.conversation import ConversationTurn
from agents.custom import OutputLimitReached
from agents.events import TraceEvent
from agents.protocol import Agent

app = FastAPI(title="PokeAgent API")
logger = logging.getLogger(__name__)

# The two implementations the benchmark compares. Typed as the shared protocol
# so a signature drift between them fails here rather than at request time.
AGENTS: dict[str, Agent] = {
    "custom": custom.call_agent,
    "langchain": framework.call_agent,
}


class Health(BaseModel):
    status: str
    service: str


class RunRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    generation: int = Field(ge=1, le=9)
    history: list[ConversationTurn] = Field(default_factory=list)
    # Which implementation to run. Defaults to the hand-written one, so a client
    # that predates the second agent keeps the behaviour it had.
    agent: Literal["custom", "langchain"] = "custom"


# Routes carry the /api prefix in the path itself rather than relying on a mount
# point. The same URL then resolves through the Next.js dev proxy and through the
# Vercel rewrite, whose post-rewrite path handling is not yet confirmed.
@app.get("/api/health")
def health() -> Health:
    return Health(status="ok", service="pokeagent-backend")


@app.post("/api/runs", response_class=EventSourceResponse)
def run_agent(request: RunRequest) -> Iterator[ServerSentEvent]:
    """Send progress from one agent run over a single HTTP response."""
    agent = AGENTS[request.agent]
    try:
        for event in agent(request.prompt, request.generation, request.history):
            yield ServerSentEvent(data=event, event=event.type)
    except OutputLimitReached:
        logger.info("Agent run reached its output-token limit")
        error = TraceEvent(
            type="error",
            message=(
                "The model reached this run's output limit. "
                "Try a shorter question or ask for a shorter answer."
            ),
        )
        yield ServerSentEvent(data=error, event=error.type)
        return
    except Exception:
        logger.exception("Agent run failed")
        error = TraceEvent(
            type="error", message="The run failed. Check the server logs."
        )
        yield ServerSentEvent(data=error, event=error.type)
        return

    done = TraceEvent(type="done", message="")
    yield ServerSentEvent(data=done, event=done.type)
