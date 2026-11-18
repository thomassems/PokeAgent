"""Typed Jev classification calls for local routing experiments."""

import os
from time import perf_counter

import httpx2
from pydantic import BaseModel, Field

_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
_TIMEOUT_SECONDS = 15.0


class JevUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0


class JevChoiceAnswer(BaseModel):
    type: str
    choice: str
    probabilities: dict[str, float]
    confidence: float = Field(ge=0, le=1)


class JevDecision(BaseModel):
    model: str
    provider: str | None = None
    choice: str
    probabilities: dict[str, float]
    confidence: float
    latency_ms: float
    usage: JevUsage


class JevError(RuntimeError):
    """A sanitized failure safe to report from the local eval runner."""


def classify_choice(
    state: str,
    instructions: str,
    criteria: dict[str, str],
    model: str = "jev-1.13.0",
) -> JevDecision:
    """Ask Jev to select one named option from caller-provided criteria."""
    api_key = os.environ.get("TYPESAFE_API_KEY")
    if not api_key:
        raise JevError("TYPESAFE_API_KEY is not configured.")

    payload = {
        "model": model,
        "state": state,
        "questions": {
            "route": {
                "type": "choice",
                "instructions": instructions,
                "criteria": criteria,
            }
        },
    }

    started = perf_counter()
    try:
        response = httpx2.post(
            _ENDPOINT,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=httpx2.Timeout(_TIMEOUT_SECONDS),
        )
        response.raise_for_status()
        body = response.json()
        answer = JevChoiceAnswer.model_validate(body["answers"]["route"])
        usage = JevUsage.model_validate(body.get("usage", {}))
    except (httpx2.HTTPError, KeyError, TypeError, ValueError) as exc:
        print(f"[services.jev] request failed: {type(exc).__name__}: {exc}")
        raise JevError("Jev classification failed.") from exc
    latency_ms = (perf_counter() - started) * 1000

    if answer.choice not in criteria:
        raise JevError(f"Jev returned unknown choice '{answer.choice}'.")

    return JevDecision(
        model=body.get("model", model),
        provider=body.get("provider"),
        choice=answer.choice,
        probabilities=answer.probabilities,
        confidence=answer.confidence,
        latency_ms=latency_ms,
        usage=usage,
    )
