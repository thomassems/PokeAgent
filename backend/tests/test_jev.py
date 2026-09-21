"""Jev routing adapter and benchmark tests with no live model calls."""

import json
from typing import Any

import pytest

from evals.loader import JevToolSelectionCase, jev_tool_selection_cases
from evals.run_jev_tool_selection import TOOL_CRITERIA, run_benchmark, save_report
from services import jev
from services.jev import JevDecision, JevError, JevUsage, classify_choice


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict[str, Any]:
        return self.payload


def test_classify_choice_sends_typed_criteria(monkeypatch) -> None:
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse(
            {
                "model": "typesafe/jev-1.13-20260917",
                "provider": "TypeSafe",
                "answers": {
                    "route": {
                        "type": "choice",
                        "choice": "get_pokemon",
                        "probabilities": {
                            "get_pokemon": 0.9,
                            "web_search": 0.1,
                        },
                        "confidence": 0.9,
                    }
                },
                "usage": {"input_tokens": 100, "output_tokens": 4, "cost": 0.001},
            }
        )

    monkeypatch.setenv("TYPESAFE_API_KEY", "secret-test-key")
    monkeypatch.setattr(jev.httpx2, "post", fake_post)
    decision = classify_choice(
        "What are Garchomp's stats?",
        "Choose a tool.",
        {"get_pokemon": "Pokemon data", "web_search": "Current information"},
    )

    assert decision.choice == "get_pokemon"
    assert decision.usage.input_tokens == 100
    assert captured["json"]["questions"]["route"]["type"] == "choice"
    assert captured["headers"]["Authorization"] == "Bearer secret-test-key"


def test_classify_choice_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    with pytest.raises(JevError, match="not configured"):
        classify_choice("prompt", "instructions", {"no_tool": "No tool"})


def test_classify_choice_rejects_unknown_choice(monkeypatch) -> None:
    monkeypatch.setenv("TYPESAFE_API_KEY", "secret-test-key")
    monkeypatch.setattr(
        jev.httpx2,
        "post",
        lambda *args, **kwargs: FakeResponse(
            {
                "answers": {
                    "route": {
                        "type": "choice",
                        "choice": "invented_tool",
                        "probabilities": {"invented_tool": 1.0},
                        "confidence": 1.0,
                    }
                }
            }
        ),
    )
    with pytest.raises(JevError, match="unknown choice"):
        classify_choice("prompt", "instructions", {"no_tool": "No tool"})


def test_every_fixture_has_a_valid_unique_expected_choice() -> None:
    cases = jev_tool_selection_cases()
    assert len({case.id for case in cases}) == len(cases)
    assert all(case.expected_choice in TOOL_CRITERIA for case in cases)


def test_benchmark_calculates_accuracy_latency_and_usage(monkeypatch) -> None:
    monkeypatch.setattr(
        "evals.run_jev_tool_selection._git_commit", lambda: "test-commit"
    )
    cases = [
        JevToolSelectionCase(
            id="stats",
            prompt="Garchomp stats?",
            expected_choice="get_pokemon",
            why="Exact data",
        )
    ]
    decisions = iter(
        [
            JevDecision(
                model="jev-test",
                choice="get_pokemon",
                probabilities={"get_pokemon": 0.8, "get_move": 0.2},
                confidence=0.8,
                latency_ms=100,
                usage=JevUsage(input_tokens=10, output_tokens=2, cost=0.01),
            ),
            JevDecision(
                model="jev-test",
                choice="get_move",
                probabilities={"get_move": 0.6, "get_pokemon": 0.4},
                confidence=0.6,
                latency_ms=200,
                usage=JevUsage(input_tokens=10, output_tokens=2, cost=0.01),
            ),
        ]
    )

    def fake_classifier(*args) -> JevDecision:
        return next(decisions)

    report = run_benchmark(cases, runs=2, classifier=fake_classifier)
    aggregate = report["aggregate"]
    assert aggregate["top_1_accuracy"] == 0.5
    assert aggregate["top_2_accuracy"] == 1.0
    assert aggregate["latency_ms"]["p50"] == 150
    assert aggregate["usage"]["input_tokens"] == 20
    assert aggregate["usage"]["cost"] == pytest.approx(0.02)
    assert report["git_commit"] == "test-commit"


def test_report_is_saved_as_readable_json(tmp_path) -> None:
    output = tmp_path / "result.json"
    report = {"schema_version": 1, "aggregate": {"top_1_accuracy": 0.75}}
    saved = save_report(report, output)
    assert saved == output
    assert json.loads(output.read_text()) == report
