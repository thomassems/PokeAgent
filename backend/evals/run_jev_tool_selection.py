"""Run and save the local Jev tool-classification benchmark."""

import argparse
import json
import subprocess
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from statistics import fmean
from typing import Any

from evals.loader import JevToolSelectionCase, jev_tool_selection_cases
from llm.tools.registry import TOOLS
from services.jev import JevDecision, JevError, classify_choice

DEFAULT_MODEL = "jev-1.13.0"
DEFAULT_RUNS = 5
RESULTS_DIR = Path(__file__).parent / "results"
ROUTING_INSTRUCTIONS = (
    "Choose the single best next route for this Pokemon request. Select a tool "
    "only when it can be called first from the information given. Choose no_tool "
    "when no lookup is needed or clarification is required. Choose "
    "needs_agent_planning when the request requires multiple dependent tool calls."
)

TOOL_CRITERIA = {tool["name"]: tool["description"] for tool in TOOLS}
TOOL_CRITERIA.update(
    {
        "no_tool": (
            "No lookup is needed, or the agent must ask a clarifying question "
            "before any tool can be selected."
        ),
        "needs_agent_planning": (
            "The request requires multiple dependent lookups and cannot be routed "
            "correctly as one immediate tool call."
        ),
    }
)

Classifier = Callable[[str, str, dict[str, str], str], JevDecision]


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _top_choices(probabilities: dict[str, float], count: int = 2) -> list[str]:
    ranked = sorted(probabilities, key=probabilities.get, reverse=True)
    return ranked[:count]


def run_benchmark(
    cases: list[JevToolSelectionCase],
    runs: int = DEFAULT_RUNS,
    model: str = DEFAULT_MODEL,
    classifier: Classifier = classify_choice,
) -> dict[str, Any]:
    """Classify every fixture repeatedly and calculate aggregate metrics."""
    case_results = []
    all_successes = []
    failure_count = 0

    for case in cases:
        attempts = []
        for _ in range(runs):
            try:
                decision = classifier(
                    case.prompt,
                    ROUTING_INSTRUCTIONS,
                    TOOL_CRITERIA,
                    model,
                )
            except JevError as exc:
                failure_count += 1
                attempts.append({"error": str(exc)})
                continue

            top_two = _top_choices(decision.probabilities)
            attempt = {
                **decision.model_dump(mode="json"),
                "correct": decision.choice == case.expected_choice,
                "top_2_correct": case.expected_choice in top_two,
            }
            attempts.append(attempt)
            all_successes.append(attempt)

        successful_attempts = [
            attempt for attempt in attempts if "error" not in attempt
        ]
        choice_counts = Counter(attempt["choice"] for attempt in successful_attempts)
        case_results.append(
            {
                "id": case.id,
                "prompt": case.prompt,
                "expected_choice": case.expected_choice,
                "why": case.why,
                "choice_counts": dict(choice_counts),
                "top_1_accuracy": (
                    fmean(attempt["correct"] for attempt in successful_attempts)
                    if successful_attempts
                    else 0.0
                ),
                "attempts": attempts,
            }
        )

    latencies = [attempt["latency_ms"] for attempt in all_successes]
    confidences = [attempt["confidence"] for attempt in all_successes]
    return {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "git_commit": _git_commit(),
        "requested_model": model,
        "runs_per_case": runs,
        "criteria": TOOL_CRITERIA,
        "aggregate": {
            "case_count": len(cases),
            "attempt_count": len(cases) * runs,
            "successful_attempts": len(all_successes),
            "failed_attempts": failure_count,
            "top_1_accuracy": (
                fmean(attempt["correct"] for attempt in all_successes)
                if all_successes
                else 0.0
            ),
            "top_2_accuracy": (
                fmean(attempt["top_2_correct"] for attempt in all_successes)
                if all_successes
                else 0.0
            ),
            "mean_confidence": fmean(confidences) if confidences else 0.0,
            "latency_ms": {
                "mean": fmean(latencies) if latencies else 0.0,
                "p50": _percentile(latencies, 0.50),
                "p95": _percentile(latencies, 0.95),
            },
            "usage": {
                "input_tokens": sum(
                    attempt["usage"]["input_tokens"] for attempt in all_successes
                ),
                "output_tokens": sum(
                    attempt["usage"]["output_tokens"] for attempt in all_successes
                ),
                "cost": sum(attempt["usage"]["cost"] for attempt in all_successes),
            },
        },
        "cases": case_results,
    }


def save_report(report: dict[str, Any], output: Path | None = None) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    if output is None:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        output = RESULTS_DIR / f"jev-tool-selection-{timestamp}.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.runs < 1:
        raise SystemExit("--runs must be at least 1.")

    report = run_benchmark(
        jev_tool_selection_cases(),
        runs=args.runs,
        model=args.model,
    )
    output = save_report(report, args.output)
    print(json.dumps(report["aggregate"], indent=2))
    print(f"Saved report to {output}.")


if __name__ == "__main__":
    main()
