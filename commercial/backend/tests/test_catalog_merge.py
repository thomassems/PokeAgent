"""Base catalog merge and the baked Lapras row."""

import json
from pathlib import Path

import pytest

from data.catalog_merge import merge_catalog
from scripts.refresh_base_catalog import _fetch

_BASE = Path(__file__).resolve().parents[1] / "data" / "go_base.json"


def test_lapras_dex_comes_from_the_merged_file() -> None:
    rows = json.loads(_BASE.read_text())["species"]
    lapras = next(row for row in rows if row["id"] == "lapras")
    assert lapras["dex"] == 131
    assert lapras["name"] == "Lapras"
    assert lapras["types"] == ["water", "ice"]
    assert lapras["shiny"] is False


def test_forms_group_under_the_base_species() -> None:
    merged = merge_catalog(
        [
            {
                "speciesId": "charizard",
                "speciesName": "Charizard",
                "dex": 6,
                "types": ["fire", "flying"],
                "released": True,
                "tags": ["starter"],
            },
            {
                "speciesId": "charizard_mega_x",
                "speciesName": "Charizard",
                "dex": 6,
                "types": ["fire", "dragon"],
                "released": True,
                "tags": [],
            },
            {
                "speciesId": "charizard_shadow",
                "speciesName": "Charizard",
                "dex": 6,
                "types": ["fire", "flying"],
                "released": True,
                "tags": ["shadow"],
            },
            {
                "speciesId": "unreleased_mon",
                "speciesName": "Nope",
                "dex": 0,
                "types": ["normal"],
                "released": False,
            },
        ],
        {"charizard": 6},
        {"charizard": {"name": "Charizard", "types": ["fire", "flying"]}},
    )
    assert len(merged) == 1
    row = merged[0]
    assert row["dex"] == 6
    assert row["forms"] == ["mega-x"]
    assert row["shadow"] is True
    assert row["shiny"] is False


def test_refresh_refuses_a_blocked_host() -> None:
    with pytest.raises(ValueError, match="Refusing"):
        _fetch("https://pokemongolive.com/post/example")
