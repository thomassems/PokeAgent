"""The LangChain agent's event stream and caps, without a paid model call.

The custom agent is testable by monkeypatching its `chat` function, because it
owns the loop that calls it. There is no equivalent seam here: `create_agent`
builds the graph and the call site is inside it. So the double goes in one level
lower, as a chat model, and the test drives the real graph.

That is the trade the framework makes. The loop is not ours to stub, so the
tests exercise more real machinery than the custom agent's tests do, and they
depend on how `create_agent` streams rather than only on our own code.
"""

import json
from collections.abc import Iterator, Sequence
from contextlib import nullcontext
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from langchain.agents.middleware.model_call_limit import ModelCallLimitExceededError
from langchain.agents.middleware.tool_call_limit import ToolCallLimitExceededError
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessageChunk
from langchain_core.outputs import ChatGenerationChunk

from agents import custom, framework
from agents.conversation import ConversationTurn
from agents.events import RunMetrics, TraceEvent
from agents.protocol import Agent
from api import main

# Both implementations satisfy the shared protocol. It is structural, so
# conformance is checked by assignment rather than by inheritance, and a drift
# in either signature stops this module type checking.
_custom_conforms: Agent = custom.call_agent
_framework_conforms: Agent = framework.call_agent

GET_MOVE_CALL = {"name": "get_move", "args": {"moves": ["Body Slam"]}, "id": "c1"}


class Step:
    """One scripted model turn: what it says, what it calls, what it spends."""

    def __init__(
        self,
        text: str,
        tool_calls: Sequence[dict[str, Any]] = (),
        output_tokens: int = 10,
        stop_reason: str = "end_turn",
        input_tokens: int = 1,
    ) -> None:
        self.text = text
        self.tool_calls = tool_calls
        self.output_tokens = output_tokens
        self.stop_reason = stop_reason
        self.input_tokens = input_tokens


class FakeChatModel(BaseChatModel):
    """A chat model that replays scripted steps and records what it was sent."""

    steps: Any
    seen_messages: Any = None
    seen_max_tokens: Any = None

    @property
    def _llm_type(self) -> str:
        return "fake"

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> Any:
        # create_agent passes model_settings into bind_tools, and binding
        # forwards them to _stream as kwargs. Returning self would silently
        # discard the per-call max_tokens the budget middleware sets, which is
        # the thing some of these tests are checking.
        return self.bind(**kwargs)

    def _stream(
        self,
        messages: list[Any],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        step = next(self.steps)
        self.seen_messages.append(list(messages))
        self.seen_max_tokens.append(kwargs.get("max_tokens"))

        for word in step.text.split(" "):
            if word:
                yield ChatGenerationChunk(message=AIMessageChunk(content=word + " "))
        # The real provider's last chunk carries the tool-call fragments and the
        # usage totals rather than text, so the fake does the same.
        yield ChatGenerationChunk(
            message=AIMessageChunk(
                content="",
                tool_call_chunks=[
                    {
                        "name": call["name"],
                        "args": json.dumps(call["args"]),
                        "id": call["id"],
                        "index": index,
                        "type": "tool_call_chunk",
                    }
                    for index, call in enumerate(step.tool_calls)
                ],
                usage_metadata={
                    "input_tokens": step.input_tokens,
                    "output_tokens": step.output_tokens,
                    "total_tokens": step.input_tokens + step.output_tokens,
                },
                response_metadata={"stop_reason": step.stop_reason},
            )
        )

    def _generate(
        self,
        messages: list[Any],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> Any:
        raise NotImplementedError("The agent streams; it never calls _generate.")


def script(
    monkeypatch: pytest.MonkeyPatch,
    steps: Sequence[Step],
    tool_functions: dict[str, Any] | None = None,
) -> FakeChatModel:
    """Point build_agent at a scripted model, keeping the real middleware."""
    for name, function in (tool_functions or {}).items():
        monkeypatch.setitem(framework.TOOL_FUNCTIONS, name, function)

    model = FakeChatModel(steps=iter(steps), seen_messages=[], seen_max_tokens=[])
    # Only the model is replaced, so every run below goes through the real
    # middleware stack, the real tool adapter and the real graph.
    monkeypatch.setattr(framework, "_model", lambda: model)
    return model


def test_framework_agent_streams_a_tool_step_and_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = script(
        monkeypatch,
        [
            Step("Checking the move...", [GET_MOVE_CALL], 20, "tool_use"),
            Step("Body Slam has 85 power.", (), 15),
        ],
        {"get_move": lambda moves: {moves[0]: {"power": 85}}},
    )

    events = list(framework.call_agent("Tell me about Body Slam", generation=4))

    # The same event types, in the same order, as the custom agent produces for
    # this shape of run. See test_agent_stream.py for the other side.
    assert [event.type for event in events] == [
        "status",
        "answer_delta",
        "answer_delta",
        "answer_delta",
        "tool",
        "tool",
        "status",
        "answer_delta",
        "answer_delta",
        "answer_delta",
        "answer_delta",
        "answer_delta",
        "answer",
        "metrics",
    ]
    tool_events = [event.message for event in events if event.type == "tool"]
    assert tool_events == ["Using get_move", "get_move returned"]
    assert [event.message for event in events if event.type == "status"] == [
        f"Step 1 of {framework.NUM_ITERS}",
        f"Step 2 of {framework.NUM_ITERS}",
    ]
    assert events[-2].message.strip() == "Body Slam has 85 power."

    # The tool ran for real and its output went back as the tool message.
    tool_message = model.seen_messages[1][-1]
    assert json.loads(tool_message.content) == {"Body Slam": {"power": 85}}


def test_framework_agent_can_answer_on_the_last_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The step cap allows an answer on the last step, as the custom agent does."""
    script(
        monkeypatch,
        [
            Step("x", [GET_MOVE_CALL], 100, "tool_use")
            for _ in range(framework.NUM_ITERS - 1)
        ]
        + [Step("Try Jolteon.", (), 100)],
        {"get_move": lambda moves: {}},
    )

    events = list(
        framework.call_agent("What makes a fast Electric type?", generation=4)
    )

    assert [event.message for event in events if event.type == "status"] == [
        f"Step {step} of {framework.NUM_ITERS}"
        for step in range(1, framework.NUM_ITERS + 1)
    ]
    assert events[-2] == TraceEvent(type="answer", message="Try Jolteon. ")


def test_framework_agent_receives_prior_turns_and_the_generation_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = script(monkeypatch, [Step("Jolteon is fast.", (), 25)])
    history = [
        ConversationTurn(
            prompt="What is Body Slam?", answer="A Normal move.", generation=3
        ),
        ConversationTurn(
            prompt="What about Electric types?", answer="Consider speed.", generation=4
        ),
    ]

    events = list(
        framework.call_agent("Which one is fastest?", generation=4, history=history)
    )

    # The system prompt arrives as a message here rather than as a separate
    # parameter, so it is dropped before comparing with the custom agent's shape.
    sent = [
        (message.type, message.text)
        for message in model.seen_messages[0]
        if message.type != "system"
    ]
    assert sent == [
        ("human", "Selected generation: 3\n\nWhat is Body Slam?"),
        ("ai", "A Normal move."),
        ("human", "Selected generation: 4\n\nWhat about Electric types?"),
        ("ai", "Consider speed."),
        ("human", "Selected generation: 4\n\nWhich one is fastest?"),
    ]
    assert model.seen_messages[0][0].type == "system"
    assert events[-2].type == "answer"


def test_step_cap_raises_rather_than_running_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script(
        monkeypatch,
        [
            Step("x", [GET_MOVE_CALL], 10, "tool_use")
            for _ in range(framework.NUM_ITERS + 1)
        ],
        {"get_move": lambda moves: {}},
    )

    with pytest.raises(ModelCallLimitExceededError):
        list(framework.call_agent("Keep going forever", generation=4))


def test_tool_call_cap_raises_rather_than_feeding_the_model_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Thirteen tool calls inside the step budget still has to stop at twelve."""
    many_calls = [
        {"name": "get_move", "args": {"moves": ["Tackle"]}, "id": f"c{index}"}
        for index in range(7)
    ]
    script(
        monkeypatch,
        [Step("x", many_calls, 10, "tool_use") for _ in range(3)],
        {"get_move": lambda moves: {}},
    )

    with pytest.raises(ToolCallLimitExceededError):
        list(framework.call_agent("Call everything", generation=4))


def test_output_budget_shrinks_each_call_and_then_stops_the_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The token cap is per run, not per call, as it is in the custom agent."""
    spend = framework.MAX_OUTPUT_TOKENS // 2
    model = script(
        monkeypatch,
        [
            Step("x", [GET_MOVE_CALL], spend, "tool_use"),
            Step("x", [GET_MOVE_CALL], spend, "tool_use"),
            Step("never reached", (), 10),
        ],
        {"get_move": lambda moves: {}},
    )

    with pytest.raises(framework.OutputLimitReached):
        list(framework.call_agent("Spend the whole budget", generation=4))

    # Each call is capped at what the run has left, so the total can never
    # exceed MAX_OUTPUT_TOKENS however many steps it takes.
    assert model.seen_max_tokens == [
        framework.MAX_OUTPUT_TOKENS,
        framework.MAX_OUTPUT_TOKENS - spend,
    ]


def test_a_call_that_hits_the_ceiling_raises_the_same_error_as_the_custom_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script(monkeypatch, [Step("truncated", (), 10, "max_tokens")])

    with pytest.raises(framework.OutputLimitReached):
        list(framework.call_agent("A long question", generation=4))


def test_wall_clock_cap_stops_a_run_that_outlives_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script(
        monkeypatch,
        [Step("x", [GET_MOVE_CALL], 10, "tool_use") for _ in range(3)],
        {"get_move": lambda moves: {}},
    )
    monkeypatch.setattr(framework, "MAX_RUN_SECONDS", 0)

    with pytest.raises(TimeoutError):
        list(framework.call_agent("Take too long", generation=4))


def test_recursion_limit_leaves_room_for_the_step_cap_to_win() -> None:
    """The backstop must not fire before the cap that reports a useful reason.

    Each iteration costs about five super-steps, so a tightly sized limit would
    turn "the agent used its five steps" into "the graph ran long", and adding a
    middleware would silently lower the step cap. Measured at 26; the assertion
    leaves headroom above that.
    """
    assert framework.RECURSION_LIMIT >= 6 * framework.NUM_ITERS


def test_the_route_runs_the_agent_the_request_asks_for(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The run endpoint reaches the LangChain agent, and still defaults away."""
    script(
        monkeypatch,
        [
            Step("Checking...", [GET_MOVE_CALL], 20, "tool_use"),
            Step("Body Slam has 85 power.", (), 15),
        ],
        {"get_move": lambda moves: {moves[0]: {"power": 85}}},
    )
    client = TestClient(main.app)
    body = {"prompt": "Tell me about Body Slam", "generation": 4}

    chosen = client.post("/api/runs", json={**body, "agent": "langchain"})

    assert chosen.status_code == 200
    assert chosen.headers["content-type"].startswith("text/event-stream")
    assert "event: tool" in chosen.text
    assert "Using get_move" in chosen.text
    assert "Body Slam has 85 power." in chosen.text
    assert "event: done" in chosen.text

    # Omitting the field keeps the behaviour clients had before there were two
    # agents: the scripted model above is exhausted, so reaching it would raise.
    def stub(prompt: str, generation: int, history: Any) -> Iterator[TraceEvent]:
        yield TraceEvent(type="answer", message="from the custom agent")

    monkeypatch.setitem(main.AGENTS, "custom", stub)
    defaulted = client.post("/api/runs", json=body)

    assert "from the custom agent" in defaulted.text


def test_an_unknown_agent_is_rejected_before_a_run_starts() -> None:
    response = TestClient(main.app).post(
        "/api/runs",
        json={"prompt": "Tell me about Body Slam", "generation": 4, "agent": "nope"},
    )

    assert response.status_code == 422


def test_both_agents_report_the_same_metrics_for_the_same_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The one assertion the whole comparison rests on.

    Two implementations counting differently would show up as a difference in
    architecture rather than as the measurement bug it is. Both are given the
    same scripted run: one tool step spending 100 in and 20 out, then an answer
    spending 200 in and 15 out.
    """
    script(
        monkeypatch,
        [
            Step("Checking.", [GET_MOVE_CALL], 20, "tool_use", 100),
            Step("Body Slam has 85 power.", (), 15, "end_turn", 200),
        ],
        {"get_move": lambda moves: {moves[0]: {"power": 85}}},
    )
    framework_events = list(framework.call_agent("Tell me about Body Slam", 4))

    class FakeClient:
        def close(self) -> None:
            pass

    monkeypatch.setattr(custom.anthropic, "Anthropic", FakeClient)
    monkeypatch.setitem(
        custom.TOOL_FUNCTIONS, "get_move", lambda moves: {moves[0]: {"power": 85}}
    )
    replies = iter(
        [
            SimpleNamespace(
                stop_reason="tool_use",
                content=[
                    SimpleNamespace(
                        type="tool_use",
                        id="c1",
                        name="get_move",
                        input={"moves": ["Body Slam"]},
                    )
                ],
                usage=SimpleNamespace(input_tokens=100, output_tokens=20),
            ),
            SimpleNamespace(
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text="Body Slam has 85 power.")],
                usage=SimpleNamespace(input_tokens=200, output_tokens=15),
            ),
        ]
    )
    monkeypatch.setattr(
        custom,
        "chat",
        lambda client, messages, max_tokens, timeout: nullcontext(
            SimpleNamespace(
                text_stream=iter(()), get_final_message=lambda: next(replies)
            )
        ),
    )
    custom_events = list(custom.call_agent("Tell me about Body Slam", 4))

    expected = RunMetrics(steps=2, tool_calls=1, input_tokens=300, output_tokens=35)
    assert custom_events[-1] == TraceEvent(type="metrics", message="", metrics=expected)
    assert framework_events[-1] == custom_events[-1]
