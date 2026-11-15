"""Generation is optional, and both agents word it the same way."""

from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from agents import custom, framework
from agents.conversation import ConversationTurn
from agents.events import TraceEvent
from api import main
from llm.tools.registry import apply_selected_generation
from tests.test_agent_stream import fake_stream
from tests.test_framework_agent import Step, script

HISTORY = [
    ConversationTurn(prompt="Earlier question", answer="An earlier answer."),
    ConversationTurn(
        prompt="And this one?",
        answer="Steel resisted Ghost.",
        generation=4,
    ),
]


def _user_texts(messages: list[dict[str, Any]]) -> list[str]:
    return [
        message["content"]
        for message in messages
        if message["role"] == "user" and isinstance(message["content"], str)
    ]


def _run_custom(
    monkeypatch: pytest.MonkeyPatch,
    prompt: str,
    generation: int | None,
    history: list[ConversationTurn] | None = None,
) -> list[str]:
    class FakeClient:
        def close(self) -> None:
            pass

    monkeypatch.setattr(custom.anthropic, "Anthropic", FakeClient)
    calls: list[list[dict[str, Any]]] = []

    def fake_chat(
        client: object,
        messages: list[dict[str, Any]],
        max_tokens: int,
        timeout: float,
    ) -> Any:
        calls.append(list(messages))
        return fake_stream(
            SimpleNamespace(
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text="Done.")],
                usage=SimpleNamespace(input_tokens=1, output_tokens=1),
            )
        )

    monkeypatch.setattr(custom, "chat", fake_chat)
    list(custom.call_agent(prompt, generation, history or []))
    return _user_texts(calls[0])


def _framework_user_texts(model: Any) -> list[str]:
    return [
        message.text for message in model.seen_messages[0] if message.type == "human"
    ]


def test_no_generation_means_no_prefix_in_either_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompt = "What makes a fast Electric type?"
    custom_turns = _run_custom(monkeypatch, prompt, None, HISTORY)
    model = script(monkeypatch, [Step("Done.", (), 1)])
    list(framework.call_agent(prompt, None, HISTORY))

    expected = [
        "Earlier question",
        "Selected generation: 4\n\nAnd this one?",
        prompt,
    ]
    assert custom_turns == expected
    assert _framework_user_texts(model) == expected


def test_a_selected_generation_uses_the_same_prefix_in_both_agents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompt = "Which one is fastest?"
    history = [
        ConversationTurn(
            prompt="What is Body Slam?", answer="A Normal move.", generation=3
        )
    ]
    custom_turns = _run_custom(monkeypatch, prompt, 4, history)
    model = script(monkeypatch, [Step("Jolteon.", (), 1)])
    list(framework.call_agent(prompt, 4, history))

    expected = [
        "Selected generation: 3\n\nWhat is Body Slam?",
        "Selected generation: 4\n\nWhich one is fastest?",
    ]
    assert custom_turns == expected
    assert _framework_user_texts(model) == expected


def test_selected_generation_fills_omitted_matchup_generation() -> None:
    arguments = {"pokemon": ["Garchomp"], "direction": "defending"}
    assert apply_selected_generation("get_type_matchups", arguments, 4) == {
        **arguments,
        "generation": 4,
    }
    assert apply_selected_generation("get_type_effectiveness", arguments, None) is (
        arguments
    )
    # A debut filter, not a chart. Filling it would drop every other generation.
    assert apply_selected_generation("find_pokemon", arguments, 4) is arguments
    explicit = {**arguments, "generation": 2}
    assert apply_selected_generation("get_type_matchups", explicit, 4) is explicit


def _record_matchup(seen: list[dict[str, Any]]) -> Any:
    def record(**kwargs: Any) -> dict[str, Any]:
        seen.append(kwargs)
        return {"generation": kwargs.get("generation"), "matchups": {}}

    return record


def test_both_agents_pass_a_selected_generation_into_matchup_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool_input = {"pokemon": ["Garchomp"], "direction": "defending"}

    class FakeClient:
        def close(self) -> None:
            pass

    monkeypatch.setattr(custom.anthropic, "Anthropic", FakeClient)
    custom_seen: list[dict[str, Any]] = []
    monkeypatch.setitem(
        custom.TOOL_FUNCTIONS,
        "get_type_matchups",
        _record_matchup(custom_seen),
    )
    replies = iter(
        [
            SimpleNamespace(
                stop_reason="tool_use",
                content=[
                    SimpleNamespace(
                        type="tool_use",
                        id="c1",
                        name="get_type_matchups",
                        input=tool_input,
                    )
                ],
                usage=SimpleNamespace(input_tokens=1, output_tokens=1),
            ),
            SimpleNamespace(
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text="Weak to Ice.")],
                usage=SimpleNamespace(input_tokens=1, output_tokens=1),
            ),
        ]
    )
    monkeypatch.setattr(
        custom,
        "chat",
        lambda client, messages, max_tokens, timeout: fake_stream(next(replies)),
    )
    list(custom.call_agent("How does Garchomp fare?", 4))

    framework_seen: list[dict[str, Any]] = []
    script(
        monkeypatch,
        [
            Step(
                "Checking.",
                [
                    {
                        "name": "get_type_matchups",
                        "args": tool_input,
                        "id": "c1",
                    }
                ],
                1,
                "tool_use",
            ),
            Step("Weak to Ice.", (), 1),
        ],
        {"get_type_matchups": _record_matchup(framework_seen)},
    )
    list(framework.call_agent("How does Garchomp fare?", 4))

    assert custom_seen == [
        {"pokemon": ["Garchomp"], "direction": "defending", "generation": 4}
    ]
    assert framework_seen == custom_seen


def test_neither_agent_invents_a_generation_when_none_is_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tool_input = {"pokemon": ["Garchomp"], "direction": "defending"}

    class FakeClient:
        def close(self) -> None:
            pass

    monkeypatch.setattr(custom.anthropic, "Anthropic", FakeClient)
    custom_seen: list[dict[str, Any]] = []
    monkeypatch.setitem(
        custom.TOOL_FUNCTIONS, "get_type_matchups", _record_matchup(custom_seen)
    )
    replies = iter(
        [
            SimpleNamespace(
                stop_reason="tool_use",
                content=[
                    SimpleNamespace(
                        type="tool_use",
                        id="c1",
                        name="get_type_matchups",
                        input=dict(tool_input),
                    )
                ],
                usage=SimpleNamespace(input_tokens=1, output_tokens=1),
            ),
            SimpleNamespace(
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text="Weak to Ice.")],
                usage=SimpleNamespace(input_tokens=1, output_tokens=1),
            ),
        ]
    )
    monkeypatch.setattr(
        custom,
        "chat",
        lambda client, messages, max_tokens, timeout: fake_stream(next(replies)),
    )
    list(custom.call_agent("How does Garchomp fare?", None))

    framework_seen: list[dict[str, Any]] = []
    script(
        monkeypatch,
        [
            Step(
                "Checking.",
                [{"name": "get_type_matchups", "args": tool_input, "id": "c1"}],
                1,
                "tool_use",
            ),
            Step("Weak to Ice.", (), 1),
        ],
        {"get_type_matchups": _record_matchup(framework_seen)},
    )
    list(framework.call_agent("How does Garchomp fare?", None))

    assert custom_seen == [tool_input]
    assert framework_seen == [tool_input]


def test_run_accepts_a_missing_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def fake_agent(
        prompt: str, generation: int | None, history: list[ConversationTurn]
    ) -> Iterator[TraceEvent]:
        seen["generation"] = generation
        seen["history_generation"] = history[0].generation
        yield TraceEvent(type="answer", message="Jolteon is fast.")

    monkeypatch.setitem(main.AGENTS, "custom", fake_agent)
    response = TestClient(main.app).post(
        "/api/runs",
        json={
            "prompt": "What makes a fast Electric type?",
            "history": [{"prompt": "Hi", "answer": "Hello"}],
        },
    )

    assert response.status_code == 200
    assert seen == {"generation": None, "history_generation": None}
    assert "Jolteon is fast." in response.text


def test_run_rejects_a_generation_outside_1_to_9() -> None:
    response = TestClient(main.app).post(
        "/api/runs", json={"prompt": "Hello", "generation": 0}
    )
    assert response.status_code == 422
