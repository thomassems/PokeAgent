import logging
import os
from collections.abc import Iterator
from typing import Literal

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, Field
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from agents import custom, framework
from agents.conversation import ConversationTurn, Game
from agents.custom import OutputLimitReached
from agents.events import TraceEvent
from agents.protocol import Agent
from api.community import router as community_router


def _is_event_stream(headers: list[tuple[bytes, bytes]]) -> bool:
    return any(
        name.lower() == b"content-type" and b"text/event-stream" in value
        for name, value in headers
    )


def _with_no_transform(
    headers: list[tuple[bytes, bytes]],
) -> list[tuple[bytes, bytes]]:
    """Add `no-transform` to Cache-Control and keep a single header.

    Next's dev server gzips a proxied response when the browser sends
    Accept-Encoding. The rewrite proxy never flushes that zlib stream, so
    every server-sent event arrives together when the run ends. Compression
    is skipped only when Cache-Control contains `no-transform`. FastAPI sets
    `no-cache` on its own, and that value does not match.
    """
    directives: list[bytes] = []
    for name, value in headers:
        if name.lower() != b"cache-control":
            continue
        for part in value.split(b","):
            item = part.strip()
            if item and item not in directives:
                directives.append(item)
    if b"no-cache" not in directives:
        directives.insert(0, b"no-cache")
    if b"no-transform" not in directives:
        directives.append(b"no-transform")
    kept = [
        (name, value) for name, value in headers if name.lower() != b"cache-control"
    ]
    kept.append((b"cache-control", b", ".join(directives)))
    return kept


class LeaveEventStreamUntransformed:
    """Mark the agent event stream so a proxy will not compress it."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_event_stream(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                if _is_event_stream(headers):
                    message = {**message, "headers": _with_no_transform(headers)}
            await send(message)

        await self.app(scope, receive, send_event_stream)


def _app_name() -> str:
    configured = os.environ.get("APP_NAME", "").strip()
    return configured or "Trainermon"


app = FastAPI(title=f"{_app_name()} API")
app.include_router(community_router)
app.add_middleware(LeaveEventStreamUntransformed)
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
    generation: int | None = Field(default=None, ge=1, le=9)
    history: list[ConversationTurn] = Field(default_factory=list)
    # Which implementation to run. Defaults to the hand-written one, so a client
    # that predates the second agent keeps the behaviour it had.
    agent: Literal["custom", "langchain"] = "custom"
    # Main series when a client from before the game selector omits it.
    game: Game = "main"


def _frame(event: TraceEvent) -> ServerSentEvent:
    """One trace event as an SSE frame.

    Serialised here rather than handed to `data=` so that `exclude_none` applies:
    only a metrics event carries a `metrics` object, and every other event keeps
    the two-field shape the frontend parser already reads.
    """
    return ServerSentEvent(
        raw_data=event.model_dump_json(exclude_none=True), event=event.type
    )


# Routes carry the /api prefix in the path itself rather than relying on a mount
# point. The same URL then resolves through the Next.js dev proxy and through the
# Vercel rewrite, whose post-rewrite path handling is not yet confirmed.
@app.get("/api/health")
def health() -> Health:
    return Health(status="ok", service=_app_name())


@app.post("/api/runs", response_class=EventSourceResponse)
def run_agent(request: RunRequest) -> Iterator[ServerSentEvent]:
    """Send progress from one agent run over a single HTTP response."""
    agent = AGENTS[request.agent]
    try:
        for event in agent(
            request.prompt, request.generation, request.history, game=request.game
        ):
            yield _frame(event)
    except OutputLimitReached:
        logger.info("Agent run reached its output-token limit")
        error = TraceEvent(
            type="error",
            message=(
                "The model reached this run's output limit. "
                "Try a shorter question or ask for a shorter answer."
            ),
        )
        yield _frame(error)
        return
    except Exception:
        logger.exception("Agent run failed")
        error = TraceEvent(
            type="error", message="The run failed. Check the server logs."
        )
        yield _frame(error)
        return

    done = TraceEvent(type="done", message="")
    yield _frame(done)
