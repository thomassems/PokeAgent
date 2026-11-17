"""PvPoke species and ranking cache, without calling GitHub."""

import json

import pytest

from services.go_stats import (
    SLOW_TTL_SECONDS,
    SPECIES_URL,
    StatsCache,
    get_go_pokemon,
    get_pvp_rankings,
    rankings_url,
)

SPECIES = [
    {
        "speciesId": "medicham",
        "speciesName": "Medicham",
        "baseStats": {"atk": 121, "def": 152, "hp": 155},
        "types": ["fighting", "psychic"],
        "fastMoves": ["COUNTER", "PSYCHO_CUT"],
        "chargedMoves": ["DYNAMIC_PUNCH", "ICE_PUNCH"],
        "eliteMoves": None,
        "level25CP": None,
        "defaultIVs": {"cp1500": [49, 7, 15, 14]},
        "buddyDistance": 3,
    },
    {
        "speciesId": "garchomp",
        "speciesName": "Garchomp",
        "baseStats": {"atk": 261, "def": 193, "hp": 239},
        "types": ["dragon", "ground"],
        "fastMoves": ["DRAGON_TAIL", "MUD_SHOT"],
        "chargedMoves": ["EARTHQUAKE", "OUTRAGE"],
        "eliteMoves": ["EARTH_POWER"],
        "level25CP": 2500,
        "defaultIVs": {"cp2500": [23, 4, 15, 14]},
    },
    {
        "speciesId": "garchomp_shadow",
        "speciesName": "Garchomp (Shadow)",
        "baseStats": {"atk": 261, "def": 193, "hp": 239},
        "types": ["dragon", "ground"],
        "fastMoves": ["DRAGON_TAIL"],
        "chargedMoves": ["OUTRAGE"],
        "eliteMoves": ["EARTH_POWER"],
    },
    {
        "speciesId": "mewtwo",
        "speciesName": "Mewtwo",
        "baseStats": {"atk": 300, "def": 182, "hp": 214},
        "types": ["psychic", "none"],
        "fastMoves": ["PSYCHO_CUT"],
        "chargedMoves": ["PSYSTRIKE"],
    },
    {"speciesName": "Broken"},
]

RANKINGS = [
    {
        "speciesId": "medicham",
        "speciesName": "Medicham",
        "rating": 682,
        "moveset": ["PSYCHO_CUT", "ICE_PUNCH", "DYNAMIC_PUNCH"],
        "editorNotes": "A long note that the model does not need.",
        "matchups": [
            {"opponent": "sableye", "rating": 700},
            {"opponent": "lickitung", "rating": 650},
            {"opponent": "azu", "rating": 600},
            {"opponent": "extra", "rating": 500},
        ],
        "counters": [
            {"opponent": "trevenant", "rating": 200},
            {"opponent": "nidoqueen", "rating": 180},
            {"opponent": "scrafty", "rating": 150},
            {"opponent": "extra", "rating": 100},
        ],
    },
    {
        "speciesId": "garchomp",
        "speciesName": "Garchomp",
        "rating": 600,
        "moveset": ["MUD_SHOT", "EARTH_POWER", "OUTRAGE"],
        "matchups": [{"opponent": "dialga", "rating": 550}],
        "counters": [{"opponent": "togekiss", "rating": 100}],
    },
    {
        "speciesId": "melmetal",
        "speciesName": "Melmetal",
        "rating": 714,
        "moveset": ["THUNDER_SHOCK", "DOUBLE_IRON_BASH"],
        "matchups": [{"opponent": "mimikyu", "rating": 729}],
        "counters": [],
    },
]


def _install(
    monkeypatch: pytest.MonkeyPatch,
    payloads: dict[str, list],
    fail_after: int = 0,
) -> tuple[list[str], dict[str, float]]:
    calls: list[str] = []
    now = {"t": 0.0}

    def fetch(url: str) -> list:
        calls.append(url)
        if fail_after and len(calls) > fail_after:
            raise RuntimeError("upstream down")
        for key, rows in payloads.items():
            if url.endswith(key):
                return rows
        raise AssertionError(url)

    cache = StatsCache(fetcher=fetch, clock=lambda: now["t"])
    monkeypatch.setattr("services.go_stats.stats_cache", cache)
    return calls, now


def test_species_trim_drops_sentinel_types_and_absent_elite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install(monkeypatch, {"pokemon.json": SPECIES})
    result = get_go_pokemon(["Medicham", "Mewtwo", "Nope"])
    medicham = result["pokemon"]["Medicham"]
    mewtwo = result["pokemon"]["Mewtwo"]

    assert result["label"] == "PvPoke gamemaster"
    assert result["stale"] is False
    assert medicham["types"] == ["fighting", "psychic"]
    assert "elite_moves" not in medicham
    assert "level_25_cp" not in medicham
    assert medicham["default_ivs"]["cp1500"] == [49, 7, 15, 14]
    assert mewtwo["types"] == ["psychic"]
    assert result["pokemon"]["Nope"].startswith("Pokemon 'Nope'")
    assert "buddyDistance" not in json.dumps(result)


def test_shadow_name_and_elite_moves_round_trip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install(monkeypatch, {"pokemon.json": SPECIES})
    found = get_go_pokemon(["Garchomp", "Garchomp (Shadow)"])["pokemon"]

    assert found["Garchomp"]["species_id"] == "garchomp"
    assert found["Garchomp"]["elite_moves"] == ["EARTH_POWER"]
    assert found["Garchomp"]["level_25_cp"] == 2500
    assert found["Garchomp (Shadow)"]["species_id"] == "garchomp_shadow"


def test_rankings_label_simulations_and_cap_matchups(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls, _ = _install(monkeypatch, {"rankings-1500.json": RANKINGS})
    one = get_pvp_rankings("great", pokemon="Medicham")
    listed = get_pvp_rankings("great", limit=2)

    assert one["label"] == "PvPoke simulations, not an official ladder."
    assert one["league"] == "great"
    assert one["cp_cap"] == 1500
    assert one["pokemon"]["moveset"][0] == "PSYCHO_CUT"
    assert len(one["pokemon"]["matchups"]) == 3
    assert len(one["pokemon"]["counters"]) == 3
    assert "editorNotes" not in json.dumps(one)
    assert [row["name"] for row in listed["rankings"]] == ["Medicham", "Garchomp"]
    assert "matchups" not in listed["rankings"][0]
    assert calls == [rankings_url("great")]
    assert "1500" in calls[0]
    assert "../" not in calls[0]


def test_a_league_outside_the_allowlist_does_not_fetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls, _ = _install(monkeypatch, {})
    assert "error" in get_pvp_rankings("../cups")
    assert "error" in get_pvp_rankings("remix")
    assert calls == []


def test_slow_cache_keeps_rankings_for_a_day(monkeypatch: pytest.MonkeyPatch) -> None:
    calls, now = _install(monkeypatch, {"rankings-2500.json": RANKINGS})
    first = get_pvp_rankings("ultra", limit=1)
    now["t"] = SLOW_TTL_SECONDS - 1
    get_pvp_rankings("ultra", limit=1)
    assert len(calls) == 1

    now["t"] = SLOW_TTL_SECONDS
    second = get_pvp_rankings("ultra", limit=1)
    assert len(calls) == 2
    assert first["stale"] is False
    assert second["stale"] is False
    assert rankings_url("ultra").endswith("rankings-2500.json")


def test_failed_refresh_serves_the_previous_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls, now = _install(monkeypatch, {"rankings-10000.json": RANKINGS}, fail_after=1)
    first = get_pvp_rankings("master", pokemon="Garchomp")
    now["t"] = SLOW_TTL_SECONDS
    stale = get_pvp_rankings("master", pokemon="Garchomp")

    assert first["stale"] is False
    assert stale["stale"] is True
    assert stale["fetched_at"] == first["fetched_at"]
    assert stale["pokemon"]["species_id"] == "garchomp"
    assert len(calls) == 2


def test_failed_refresh_with_nothing_cached_returns_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fetch(url: str) -> list:
        raise RuntimeError(url)

    cache = StatsCache(fetcher=fetch, clock=lambda: 0.0)
    monkeypatch.setattr("services.go_stats.stats_cache", cache)
    assert get_go_pokemon(["Medicham"]) == {"error": "PvPoke data is unavailable."}


def test_species_url_is_constant() -> None:
    assert SPECIES_URL.endswith("/gamemaster/pokemon.json")
    assert rankings_url("little").endswith("rankings-500.json")
    assert rankings_url("master").endswith("rankings-10000.json")
