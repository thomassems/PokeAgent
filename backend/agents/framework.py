"""The same agent, built on LangChain instead of by hand.

`agents/custom.py` writes the loop out: call the model, branch on stop_reason,
dispatch the tool, append the result, go again. This module hands that loop to
`create_agent` and consumes the stream it produces. Same prompt, same tool
surface, same caps, same `TraceEvent` output, so the comparison between the two
measures architecture rather than incidental differences.

What the framework replaces is the loop and the tool dispatch, which is most of
the other module. What it does not replace:

- The tool schemas. `create_agent` wants its own tool objects, so the shared
  registry has to be adapted into them. See `_langchain_tools`.
- The hard caps. Two come from prebuilt middleware, one needs middleware written
  here, and the wall-clock bound stays a deadline check in the stream loop.

The caps and the error type are imported from `agents.custom` rather than
redeclared. CLAUDE.md requires both agents to run under identical settings, and
importing makes that true by construction instead of by vigilance. Those
constants really want to live in a module neither agent owns; moving them edits
`custom.py`, which is out of scope here.
"""

import time
from collections.abc import Iterator, Sequence
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import (
    AgentMiddleware,
    ModelCallLimitMiddleware,
    ModelRequest,
    ModelResponse,
    ToolCallLimitMiddleware,
)
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.graph.state import CompiledStateGraph

from agents.conversation import ConversationTurn
from agents.custom import (
    MAX_OUTPUT_TOKENS,
    MAX_RUN_SECONDS,
    MAX_TOOL_CALLS,
    NUM_ITERS,
    OutputLimitReached,
)
from agents.events import RunMetrics, TraceEvent
from agents.prompts import SYSTEM_PROMPT
from agents.protocol import Agent
from llm.tools.registry import TOOL_FUNCTIONS, TOOLS

# Duplicates the literal in custom.py:chat, because the model id is written
# inline there rather than being a named constant. Both agents must use the same
# model or the comparison is meaningless, so this is the one piece of parity
# nothing enforces.
MODEL = "deepseek-v4-flash"

# A backstop, deliberately loose. The real step bound is
# ModelCallLimitMiddleware below; this only catches a graph that loops without
# calling the model at all.
#
# LangGraph counts super-steps, and each loop iteration costs one model node,
# one tool node, and a node per installed middleware hook, measured at about
# five. Sizing this tightly would mean a GraphRecursionError ("the graph ran
# long") landing before ModelCallLimitExceededError ("the agent used its five
# steps"), which is the same failure reported in less useful words, and it would
# also mean that adding a middleware silently lowers the step cap.
RECURSION_LIMIT = 8 * NUM_ITERS


def _langchain_tools() -> list[StructuredTool]:
    """Adapt the shared registry into the tool objects `create_agent` wants.

    The registry holds Anthropic-shaped entries: a name, a description, and an
    `input_schema` of raw JSON Schema. `create_agent` does accept plain dicts in
    `tools=`, but that path is for provider-side tools the model runs itself, not
    for functions we execute, so each entry becomes a `StructuredTool`.

    Built from `TOOLS` and `TOOL_FUNCTIONS` rather than redeclared with `@tool`
    and Pydantic models. Redeclaring would hand the two agents two tool surfaces
    that drift independently, and the benchmark would then be measuring the
    drift. `infer_schema=False` keeps LangChain from deriving a second schema
    from the function signature and quietly preferring it.

    `custom.py` injects `max_results=5` into `web_search` input at dispatch time.
    There is no equivalent interception point here, and none is needed: the
    registry function already defaults to the same 5. The two would diverge only
    if `custom.MAX_RESULT` were changed without changing that default.
    """
    return [
        StructuredTool.from_function(
            func=TOOL_FUNCTIONS[schema["name"]],
            name=schema["name"],
            description=schema["description"],
            args_schema=schema["input_schema"],
            infer_schema=False,
        )
        for schema in TOOLS
    ]


def _output_tokens_spent(messages: Sequence[BaseMessage]) -> int:
    """Output tokens this run has already used.

    Read off the message history rather than counted in an instance attribute,
    so it stays correct no matter how many runs share a middleware object. Turns
    replayed from `history` carry no usage metadata and contribute nothing,
    which is right: they were paid for by an earlier run.
    """
    return sum(
        message.usage_metadata["output_tokens"]
        for message in messages
        if isinstance(message, AIMessage) and message.usage_metadata
    )


class OutputTokenBudget(AgentMiddleware[Any, Any]):
    """Bound the whole run's output tokens, not each individual call's.

    There is prebuilt middleware for model-call and tool-call limits, but none
    for a run-wide token budget. `max_tokens` on the model is per call, so
    without this a five-step run could spend five times what `custom.py` allows
    and the benchmark's cost column would mean nothing.

    `custom.py` keeps a remaining-token counter and passes it as the next call's
    `max_tokens`, which hard-bounds the run total. This rewrites `max_tokens` on
    each outgoing request the same way, so the bound is identical rather than
    merely similar, and raises on the same two conditions: budget exhausted
    before a call, and a call that stopped because it hit the ceiling.
    """

    def wrap_model_call(
        self,
        request: ModelRequest[Any],
        handler: Any,
    ) -> ModelResponse[Any]:
        remaining = MAX_OUTPUT_TOKENS - _output_tokens_spent(request.state["messages"])
        if remaining <= 0:
            raise OutputLimitReached
        response: ModelResponse[Any] = handler(
            request.override(
                model_settings={**request.model_settings, "max_tokens": remaining}
            )
        )
        last = response.result[-1] if response.result else None
        if (
            isinstance(last, AIMessage)
            and last.response_metadata.get("stop_reason") == "max_tokens"
        ):
            raise OutputLimitReached
        return response


def _check_deadline(deadline: float) -> None:
    """Raise once this run has outlived its wall-clock budget."""
    if time.monotonic() >= deadline:
        raise TimeoutError("Agent run exceeded its time limit")


def _model() -> BaseChatModel:
    """The provider client, with the settings `custom.py:chat` uses.

    `ChatAnthropic` falls back to `ANTHROPIC_BASE_URL` when `ANTHROPIC_API_URL`
    is unset, so this reaches the same endpoint as the custom agent's client
    without the base URL being named here. Neither agent sets `temperature`, and
    both default to two retries.

    `max_tokens` is the ceiling for a single call; `OutputTokenBudget` lowers it
    per call to whatever the run has left.

    Separate from `build_agent` so a test can replace the model without
    restating the middleware stack, which would then stop following changes to
    it.
    """
    return ChatAnthropic(
        model=MODEL,
        max_tokens=MAX_OUTPUT_TOKENS,
        timeout=MAX_RUN_SECONDS,
    )


def build_agent() -> CompiledStateGraph[Any, Any, Any, Any]:
    """Compile the graph for one run.

    Built per run rather than once at import, matching `custom.py` constructing
    its client per run. A module-level agent would hold a model client open for
    the process lifetime and share middleware state across concurrent requests.
    """
    return create_agent(
        model=_model(),
        tools=_langchain_tools(),
        system_prompt=SYSTEM_PROMPT,
        middleware=[
            # Steps. A step is one model call, so this counts the same thing
            # NUM_ITERS bounds in the hand-written loop.
            ModelCallLimitMiddleware(run_limit=NUM_ITERS, exit_behavior="error"),
            # Tool calls. exit_behavior="error" rather than the default
            # "continue", which would feed the model an error message and let
            # the run carry on past its cap.
            ToolCallLimitMiddleware(run_limit=MAX_TOOL_CALLS, exit_behavior="error"),
            OutputTokenBudget(),
        ],
    )


def _starting_messages(
    user_message: str,
    generation: int,
    history: Sequence[ConversationTurn],
) -> list[dict[str, str]]:
    """Replay the conversation in the shape `custom.py` sends it.

    The generation prefix is part of the user turn in both agents. If it moved
    into the system prompt here the two would be answering differently worded
    questions.
    """
    messages: list[dict[str, str]] = []
    for turn in history:
        prompt = f"Selected generation: {turn.generation}\n\n{turn.prompt}"
        messages.append({"role": "user", "content": prompt})
        messages.append({"role": "assistant", "content": turn.answer})
    current = f"Selected generation: {generation}\n\n{user_message}"
    messages.append({"role": "user", "content": current})
    return messages


def call_agent(
    user_message: str,
    generation: int,
    history: Sequence[ConversationTurn] = (),
) -> Iterator[TraceEvent]:
    """Continue a conversation and yield progress and answer text as it arrives.

    Two stream modes, because neither alone carries everything the trace needs:
    `messages` gives token deltas, `updates` gives completed tool calls and tool
    results. `version="v2"` gives every chunk the same type/data shape.

    The step counter is reconstructed from the stream rather than owned, which is
    the one visible difference from `custom.py`: that module yields "Step N"
    before making the call, since it is the thing making the call, while a stream
    consumer cannot know a step began until the step's first output arrives.
    Same events in the same order, announced a beat later.
    """
    deadline = time.monotonic() + MAX_RUN_SECONDS
    step = 0
    announced = False
    # Counted off the stream for the same reason the step number is: the graph
    # owns the loop, so these are observed rather than kept.
    tool_calls = 0
    input_tokens = 0
    output_tokens = 0

    def begin_step() -> Iterator[TraceEvent]:
        nonlocal step, announced
        if not announced:
            step += 1
            announced = True
            yield TraceEvent(type="status", message=f"Step {step} of {NUM_ITERS}")

    for chunk in build_agent().stream(
        {"messages": _starting_messages(user_message, generation, history)},
        stream_mode=["messages", "updates"],
        version="v2",
        config={"recursion_limit": RECURSION_LIMIT},
    ):
        _check_deadline(deadline)

        if chunk["type"] == "messages":
            token, _ = chunk["data"]
            # The messages stream carries tool output as well as model output,
            # and the model's own stream ends with empty chunks that only carry
            # tool-call fragments and usage. Neither is answer text.
            if isinstance(token, AIMessageChunk) and token.text:
                yield from begin_step()
                yield TraceEvent(type="answer_delta", message=token.text)
            continue

        if chunk["type"] != "updates":
            continue

        for source, update in chunk["data"].items():
            messages = update.get("messages", ()) if isinstance(update, dict) else ()

            if source == "tools":
                for message in messages:
                    if isinstance(message, ToolMessage):
                        yield TraceEvent(
                            type="tool", message=f"{message.name} returned"
                        )
                continue

            if source != "model":
                continue

            for message in messages:
                if not isinstance(message, AIMessage):
                    continue
                # A step that went straight to a tool call without a word of
                # preamble has streamed no text, so this is where it gets
                # announced. Resetting after it arms the next step.
                yield from begin_step()
                announced = False

                # One usage record per model response. Replayed history turns
                # carry none, so they add nothing, which is right: an earlier
                # run paid for those.
                if message.usage_metadata:
                    input_tokens += message.usage_metadata["input_tokens"]
                    output_tokens += message.usage_metadata["output_tokens"]

                if message.tool_calls:
                    # Counts what the model asked for, which is what
                    # custom.py counts and what ToolCallLimitMiddleware bounds.
                    tool_calls += len(message.tool_calls)
                    for call in message.tool_calls:
                        yield TraceEvent(type="tool", message=f"Using {call['name']}")
                    continue
                if not message.text:
                    raise RuntimeError("Model ended without an answer")
                yield TraceEvent(type="answer", message=message.text)
                yield TraceEvent(
                    type="metrics",
                    message="",
                    metrics=RunMetrics(
                        steps=step,
                        tool_calls=tool_calls,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    ),
                )
                return

    raise RuntimeError("Agent run ended without an answer")


# Structural check, not a cast: if this signature drifts from the protocol the
# benchmark stops comparing like with like, and this line stops type checking.
_conforms: Agent = call_agent
