"""Reads eval fixtures off disk into validated case objects.

Fixtures are shared: tests/ uses the `check` block to verify the dex holds the
expected value, for free, while evals/ uses `question` or `prompt` to verify the
agent reports it, which costs a model call. Writing a case once and checking it
both ways is the point of keeping them in one file.

Validated with Pydantic so a mistyped key fails here, naming the file and the
field, rather than surfacing later as a confusing assertion error.
"""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

FIXTURES = Path(__file__).parent / "fixtures"


class StatCheck(BaseModel):
    kind: Literal["stat"]
    pokemon: str
    stat: str


class TypingCheck(BaseModel):
    kind: Literal["typing"]
    pokemon: str


class MoveCheck(BaseModel):
    kind: Literal["move"]
    move: str
    field: str


class ProfileCheck(BaseModel):
    """A multiplier against a whole Pokemon, after dual-type multiplication.

    MatchupCheck reads one cell of the chart. This reads the product across both
    of a Pokemon's types, which is the arithmetic the tool does on the model's
    behalf and the place it used to go wrong.
    """

    kind: Literal["profile"]
    pokemon: str
    direction: Literal["attacking", "defending"]
    against: str


class MatchupCheck(BaseModel):
    kind: Literal["matchup"]
    attacker: str
    defender: str
    generation: int


Check = StatCheck | TypingCheck | MoveCheck | MatchupCheck | ProfileCheck


class RetrievalCase(BaseModel):
    id: str
    question: str
    expect: Any
    # Discriminated on `kind`, so Pydantic picks the right variant and reports
    # against that one rather than complaining about all four.
    check: Check = Field(discriminator="kind")


class ToolSelectionCase(BaseModel):
    id: str
    prompt: str
    expect_tool: str
    forbid_tools: list[str] = []
    why: str


class JevToolSelectionCase(BaseModel):
    id: str
    prompt: str
    expected_choice: str
    why: str


class TeamQualityCase(BaseModel):
    id: str
    prompt: str
    generation: int | None = None
    constraints: list[str]
    rubric: list[str]


def _load(filename: str) -> list[dict[str, Any]]:
    return yaml.safe_load((FIXTURES / filename).read_text())


def retrieval_cases() -> list[RetrievalCase]:
    return [RetrievalCase(**case) for case in _load("retrieval.yaml")]


def tool_selection_cases() -> list[ToolSelectionCase]:
    return [ToolSelectionCase(**case) for case in _load("tool_selection.yaml")]


def jev_tool_selection_cases() -> list[JevToolSelectionCase]:
    return [JevToolSelectionCase(**case) for case in _load("jev_tool_selection.yaml")]


def team_quality_cases() -> list[TeamQualityCase]:
    return [TeamQualityCase(**case) for case in _load("team_quality.yaml")]
