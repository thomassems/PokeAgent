"""Load and validate the repository-owned strategy corpus."""

import json
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StrategyTopic = Literal[
    "archetype",
    "counter",
    "gameplan",
    "matchup",
    "moveset",
    "role",
    "teammate",
]
BattleStyle = Literal["singles", "doubles"]
SourceKind = Literal[
    "licensed-guide",
    "official",
    "pokeagent-authored",
    "usage-data",
]


class StrategyRecord(BaseModel):
    """One independently retrievable passage plus its filtering metadata."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]+$")
    chunk_text: str = Field(min_length=80, max_length=1500)
    title: str = Field(min_length=5, max_length=120)
    pokemon: list[str] = Field(default_factory=list)
    generation: int = Field(ge=1, le=9)
    format: str = Field(pattern=r"^[a-z0-9][a-z0-9-]+$")
    battle_style: BattleStyle
    topic: StrategyTopic
    game: str = Field(pattern=r"^[a-z0-9][a-z0-9-]+$")
    source_kind: SourceKind = "pokeagent-authored"
    source_name: str = Field(min_length=3, max_length=120)
    source_url: str | None = None
    source_updated_at: date
    license: str | None = None
    dataset_version: str = Field(pattern=r"^strategy-v[1-9][0-9]*$")


_CORPUS_PATH = Path(__file__).parent / "strategy" / "seed.jsonl"


def _load_strategy_records(path: Path = _CORPUS_PATH) -> tuple[StrategyRecord, ...]:
    records = tuple(
        StrategyRecord.model_validate(json.loads(line))
        for line in path.read_text().splitlines()
        if line.strip()
    )
    ids = [record.id for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Strategy record IDs must be unique.")
    return records


STRATEGY_RECORDS = _load_strategy_records()
