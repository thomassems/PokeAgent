"""Load and validate the repository-owned Pokemon GO guides corpus."""

import json
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

GO_GUIDE_TOPICS = ("catching", "candy", "trading", "mega", "items")
GoGuideTopic = Literal["catching", "candy", "trading", "mega", "items"]
GoGuideSourceKind = Literal["official", "pokeagent-authored"]


class GoGuideRecord(BaseModel):
    """One evergreen mechanic, written for retrieval. Not a live event."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]+$")
    chunk_text: str = Field(min_length=80, max_length=1500)
    title: str = Field(min_length=5, max_length=120)
    topic: GoGuideTopic
    pokemon: list[str] = Field(default_factory=list)
    source_kind: GoGuideSourceKind = "pokeagent-authored"
    source_name: str = Field(min_length=3, max_length=120)
    source_url: str | None = None
    discovery_urls: list[str] = Field(default_factory=list)
    source_updated_at: date
    license: str | None = None
    dataset_version: str = Field(pattern=r"^go-guides-v[1-9][0-9]*$")


_CORPUS_PATH = Path(__file__).parent / "go_guides" / "guides.jsonl"


def _load_go_guides(path: Path = _CORPUS_PATH) -> tuple[GoGuideRecord, ...]:
    records = tuple(
        GoGuideRecord.model_validate(json.loads(line))
        for line in path.read_text().splitlines()
        if line.strip()
    )
    ids = [record.id for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("GO guide IDs must be unique.")
    return records


GO_GUIDE_RECORDS = _load_go_guides()
