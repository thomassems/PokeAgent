"""The hand-written agent loop used by the single-agent UI."""

import json
import time
from collections.abc import Iterator, Sequence
from typing import Any

import anthropic
from anthropic.lib.streaming import MessageStreamManager
from anthropic.types import Message

from agents.conversation import ConversationTurn
from agents.events import RunMetrics, TraceEvent
from agents.prompts import SYSTEM_PROMPT
from llm.tools.registry import TOOL_FUNCTIONS, TOOLS

NUM_ITERS = 5
MAX_RESULT = 5
MAX_TOOL_CALLS = 12
MAX_OUTPUT_TOKENS = 10_000
MAX_RUN_SECONDS = 60


class OutputLimitReached(RuntimeError):
    """The model used this run's allowed output tokens before finishing."""


def add_user_message(messages: list[dict[str, Any]], content: Any) -> None:
    messages.append({"role": "user", "content": content})


def add_assistant_message(messages: list[dict[str, Any]], content: Any) -> None:
    messages.append({"role": "assistant", "content": content})


def chat(
    client: anthropic.Anthropic,
    messages: list[dict[str, Any]],
    max_tokens: int,
    timeout: float,
) -> MessageStreamManager:
    return client.messages.stream(
        model="deepseek-v4-flash",
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=messages,
        tools=TOOLS,
        timeout=timeout,
    )


def _remaining_time(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Agent run exceeded its time limit")
    return remaining


def call_agent(
    user_message: str,
    generation: int,
    history: Sequence[ConversationTurn] = (),
) -> Iterator[TraceEvent]:
    """Continue a conversation and yield progress and answer text as it arrives."""
    messages: list[dict[str, Any]] = []
    for turn in history:
        add_user_message(
            messages, f"Selected generation: {turn.generation}\n\n{turn.prompt}"
        )
        add_assistant_message(messages, turn.answer)
    add_user_message(messages, f"Selected generation: {generation}\n\n{user_message}")
    deadline = time.monotonic() + MAX_RUN_SECONDS
    remaining_tokens = MAX_OUTPUT_TOKENS
    tool_calls = 0
    # Totals for the run, reported once at the end. Separate from
    # remaining_tokens, which is a budget being spent down rather than a count.
    input_tokens = 0
    output_tokens = 0
    client = anthropic.Anthropic()

    try:
        for iteration in range(1, NUM_ITERS + 1):
            yield TraceEvent(type="status", message=f"Step {iteration} of {NUM_ITERS}")
            if remaining_tokens <= 0:
                raise OutputLimitReached
            with chat(
                client, messages, remaining_tokens, _remaining_time(deadline)
            ) as stream:
                for chunk in stream.text_stream:
                    _remaining_time(deadline)
                    if chunk:
                        yield TraceEvent(type="answer_delta", message=chunk)
                answer: Message = stream.get_final_message()
            _remaining_time(deadline)
            remaining_tokens -= answer.usage.output_tokens
            input_tokens += answer.usage.input_tokens
            output_tokens += answer.usage.output_tokens
            add_assistant_message(messages, answer.content)

            if answer.stop_reason == "max_tokens":
                raise OutputLimitReached

            if answer.stop_reason == "tool_use":
                tool_results: list[dict[str, str]] = []
                for block in answer.content:
                    if block.type != "tool_use":
                        continue
                    tool_calls += 1
                    if tool_calls > MAX_TOOL_CALLS:
                        raise RuntimeError("Agent run exceeded its tool-call limit")
                    _remaining_time(deadline)
                    if block.name not in TOOL_FUNCTIONS:
                        raise ValueError(f"Unknown tool: {block.name}")
                    yield TraceEvent(type="tool", message=f"Using {block.name}")
                    tool_input = dict(block.input)
                    if block.name == "web_search":
                        tool_input.setdefault("max_results", MAX_RESULT)
                    result = TOOL_FUNCTIONS[block.name](**tool_input)
                    _remaining_time(deadline)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        }
                    )
                    yield TraceEvent(type="tool", message=f"{block.name} returned")
                if not tool_results:
                    raise RuntimeError("Model requested tools without a tool call")
                add_user_message(messages, tool_results)
                continue

            if answer.stop_reason == "end_turn":
                final_text = "".join(
                    block.text for block in answer.content if block.type == "text"
                )
                if not final_text:
                    raise RuntimeError("Model ended without an answer")
                yield TraceEvent(type="answer", message=final_text)
                yield TraceEvent(
                    type="metrics",
                    message="",
                    metrics=RunMetrics(
                        steps=iteration,
                        tool_calls=tool_calls,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    ),
                )
                return

            raise RuntimeError(f"Model stopped unexpectedly: {answer.stop_reason}")

        raise RuntimeError("Agent run reached its step limit without an answer")
    finally:
        client.close()
