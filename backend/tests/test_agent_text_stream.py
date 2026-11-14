"""Text chunks from a model step reach the client before the final message."""

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


def test_chat_uses_the_provider_stream() -> None:
    calls: list[dict[str, Any]] = []
    reply = object()

    class FakeMessages:
        def stream(self, **kwargs: Any) -> Any:
            calls.append(kwargs)
            return nullcontext(
                SimpleNamespace(
                    text_stream=iter(("Try ", "Jolteon.")),
                    get_final_message=lambda: reply,
                )
            )

    client = SimpleNamespace(messages=FakeMessages())
    with custom.chat(client, [{"role": "user", "content": "Hi"}], 100, 5.0) as stream:
        assert list(stream.text_stream) == ["Try ", "Jolteon."]
        assert stream.get_final_message() is reply

    assert calls[0]["max_tokens"] == 100
    assert calls[0]["timeout"] == 5.0


def test_custom_agent_yields_text_before_the_final_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        def close(self) -> None:
            pass

    monkeypatch.setattr(custom.anthropic, "Anthropic", FakeClient)
    reply = SimpleNamespace(
        stop_reason="end_turn",
        content=[SimpleNamespace(type="text", text="Try Jolteon.")],
        usage=SimpleNamespace(input_tokens=40, output_tokens=4),
    )
    monkeypatch.setattr(
        custom,
        "chat",
        lambda client, messages, max_tokens, timeout: nullcontext(
            SimpleNamespace(
                text_stream=iter(("Try ", "Jolteon.")),
                get_final_message=lambda: reply,
            )
        ),
    )

    events = list(custom.call_agent("Suggest a fast Electric type", generation=4))

    assert [(event.type, event.message) for event in events] == [
        ("status", f"Step 1 of {custom.NUM_ITERS}"),
        ("answer_delta", "Try "),
        ("answer_delta", "Jolteon."),
        ("answer", "Try Jolteon."),
        ("metrics", ""),
    ]


def test_output_limit_has_an_actionable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        def close(self) -> None:
            pass

    monkeypatch.setattr(custom.anthropic, "Anthropic", FakeClient)

    def limited_chat(
        client: object,
        messages: list[dict[str, Any]],
        max_tokens: int,
        timeout: float,
    ) -> Any:
        return nullcontext(
            SimpleNamespace(
                text_stream=iter(()),
                get_final_message=lambda: SimpleNamespace(
                    stop_reason="max_tokens",
                    content=[],
                    usage=SimpleNamespace(input_tokens=10, output_tokens=max_tokens),
                ),
            )
        )

    monkeypatch.setattr(custom, "chat", limited_chat)
    with pytest.raises(custom.OutputLimitReached):
        list(custom.call_agent("A long question", generation=4))

    def limited_agent(
        prompt: str, generation: int, history: list[ConversationTurn]
    ) -> Iterator[TraceEvent]:
        yield TraceEvent(type="status", message="Step 1 of 3")
        raise custom.OutputLimitReached()

    monkeypatch.setitem(main.AGENTS, "custom", limited_agent)
    response = TestClient(main.app).post(
        "/api/runs", json={"prompt": "A long question", "generation": 4}
    )
    assert "event: error" in response.text
    assert "output limit" in response.text
    assert "Check the server logs" not in response.text
