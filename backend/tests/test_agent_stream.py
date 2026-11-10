"""The run boundary and event stream without a paid model call."""

import json
from collections.abc import Iterator
from contextlib import nullcontext
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from agents import custom
from agents.conversation import ConversationTurn
from agents.events import TraceEvent
from api import main


def fake_stream(reply: Any, chunks: tuple[str, ...] = ()) -> Any:
    return nullcontext(
        SimpleNamespace(text_stream=iter(chunks), get_final_message=lambda: reply)
    )


def test_custom_agent_streams_a_tool_step_and_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        closed = False

        def close(self) -> None:
            self.closed = True

    fake_client = FakeClient()

    def fake_client_factory() -> FakeClient:
        return fake_client

    monkeypatch.setattr(custom.anthropic, "Anthropic", fake_client_factory)

    def fake_get_move(moves: list[str]) -> dict[str, dict[str, int]]:
        return {moves[0]: {"power": 85}}

    monkeypatch.setitem(
        custom.TOOL_FUNCTIONS,
        "get_move",
        fake_get_move,
    )
    tool_use = SimpleNamespace(
        type="tool_use", id="call-1", name="get_move", input={"moves": ["Body Slam"]}
    )
    replies = iter(
        [
            SimpleNamespace(
                stop_reason="tool_use",
                content=[tool_use],
                usage=SimpleNamespace(input_tokens=200, output_tokens=20),
            ),
            SimpleNamespace(
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text="Body Slam has 85 power.")],
                usage=SimpleNamespace(input_tokens=300, output_tokens=15),
            ),
        ]
    )
    calls: list[tuple[object, list[dict[str, Any]], int, float]] = []

    def fake_chat(
        client: object,
        messages: list[dict[str, Any]],
        max_tokens: int,
        timeout: float,
    ) -> Any:
        calls.append((client, list(messages), max_tokens, timeout))
        reply = next(replies)
        chunks = (
            ("Checking the move...",)
            if reply.stop_reason == "tool_use"
            else ("Body Slam has 85 power.",)
        )
        return fake_stream(reply, chunks)

    monkeypatch.setattr(custom, "chat", fake_chat)
    events = list(custom.call_agent("Tell me about Body Slam", generation=4))

    assert [event.type for event in events] == [
        "status",
        "answer_delta",
        "tool",
        "tool",
        "status",
        "answer_delta",
        "answer",
        "metrics",
    ]
    assert events[1].message == "Checking the move..."
    assert events[-2].message == "Body Slam has 85 power."
    assert calls[0][1][0]["content"] == (
        "Selected generation: 4\n\nTell me about Body Slam"
    )
    assert json.loads(calls[1][1][-1]["content"][0]["content"]) == {
        "Body Slam": {"power": 85}
    }
    assert fake_client.closed


def test_custom_agent_can_answer_on_fifth_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        def close(self) -> None:
            pass

    monkeypatch.setattr(custom.anthropic, "Anthropic", FakeClient)
    monkeypatch.setitem(custom.TOOL_FUNCTIONS, "get_move", lambda moves: {})
    replies = iter(
        [
            SimpleNamespace(
                stop_reason="tool_use",
                content=[
                    SimpleNamespace(
                        type="tool_use",
                        id=f"call-{step}",
                        name="get_move",
                        input={"moves": ["Thunderbolt"]},
                    )
                ],
                usage=SimpleNamespace(input_tokens=100, output_tokens=100),
            )
            for step in range(1, 5)
        ]
        + [
            SimpleNamespace(
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text="Try Jolteon.")],
                usage=SimpleNamespace(input_tokens=100, output_tokens=100),
            )
        ]
    )

    def fake_chat(
        client: object,
        messages: list[dict[str, Any]],
        max_tokens: int,
        timeout: float,
    ) -> Any:
        return fake_stream(next(replies))

    monkeypatch.setattr(custom, "chat", fake_chat)
    events = list(custom.call_agent("What makes a fast Electric type?", generation=4))

    assert [event.message for event in events if event.type == "status"] == [
        f"Step {step} of 5" for step in range(1, 6)
    ]
    assert events[-2] == TraceEvent(type="answer", message="Try Jolteon.")


def test_custom_agent_receives_prior_turns_and_ten_thousand_token_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        def close(self) -> None:
            pass

    monkeypatch.setattr(custom.anthropic, "Anthropic", FakeClient)
    calls: list[tuple[list[dict[str, Any]], int]] = []

    def fake_chat(
        client: object,
        messages: list[dict[str, Any]],
        max_tokens: int,
        timeout: float,
    ) -> Any:
        calls.append((list(messages), max_tokens))
        return fake_stream(
            SimpleNamespace(
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text="Jolteon is fast.")],
                usage=SimpleNamespace(input_tokens=50, output_tokens=25),
            )
        )

    monkeypatch.setattr(custom, "chat", fake_chat)
    history = [
        ConversationTurn(
            prompt="What is Body Slam?", answer="A Normal move.", generation=3
        ),
        ConversationTurn(
            prompt="What about Electric types?", answer="Consider speed.", generation=4
        ),
    ]

    events = list(
        custom.call_agent("Which one is fastest?", generation=4, history=history)
    )

    assert calls == [
        (
            [
                {
                    "role": "user",
                    "content": "Selected generation: 3\n\nWhat is Body Slam?",
                },
                {"role": "assistant", "content": "A Normal move."},
                {
                    "role": "user",
                    "content": "Selected generation: 4\n\nWhat about Electric types?",
                },
                {"role": "assistant", "content": "Consider speed."},
                {
                    "role": "user",
                    "content": "Selected generation: 4\n\nWhich one is fastest?",
                },
            ],
            10_000,
        )
    ]
    assert events[-2] == TraceEvent(type="answer", message="Jolteon is fast.")


def test_run_endpoint_sends_sse_and_sanitizes_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_agent(
        prompt: str, generation: int, history: list[ConversationTurn]
    ) -> Iterator[TraceEvent]:
        assert (prompt, generation) == ("Help with Garchomp", 4)
        assert history == [
            ConversationTurn(prompt="Suggest a type", answer="Try Steel.", generation=4)
        ]
        yield TraceEvent(type="status", message="Step 1 of 3")
        yield TraceEvent(type="answer_delta", message="Try a ")
        yield TraceEvent(type="answer", message="Try a Steel type.")

    monkeypatch.setitem(main.AGENTS, "custom", fake_agent)
    response = TestClient(main.app).post(
        "/api/runs",
        json={
            "prompt": "Help with Garchomp",
            "generation": 4,
            "history": [
                {"prompt": "Suggest a type", "answer": "Try Steel.", "generation": 4}
            ],
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: status" in response.text
    assert 'data: {"type":"answer_delta","message":"Try a "}' in response.text
    assert 'data: {"type":"answer","message":"Try a Steel type."}' in response.text
    assert "event: done" in response.text

    def failing_agent(
        prompt: str, generation: int, history: list[ConversationTurn]
    ) -> Iterator[TraceEvent]:
        yield TraceEvent(type="status", message="Step 1 of 3")
        raise RuntimeError("provider secret and internal path")

    monkeypatch.setitem(main.AGENTS, "custom", failing_agent)
    failed = TestClient(main.app).post(
        "/api/runs", json={"prompt": "Help with Garchomp", "generation": 4}
    )
    assert "event: error" in failed.text
    assert "provider secret and internal path" not in failed.text
