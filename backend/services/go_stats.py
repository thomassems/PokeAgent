"""Pokemon GO species stats and league rankings from PvPoke.

PvPoke is MIT-licensed. The numbers are still the game's data, republished
and, for rankings, simulated. This module caches the gamemaster and the
open overall ranking files. A league name is an allowlist key. It is never
copied into a URL path. `tools/` does not import this module.
"""

import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx2

from services.go_feed import SLOW_TTL_SECONDS

logger = logging.getLogger(__name__)

# Rankings and the gamemaster move on the maintainer's schedule, not during
# a raid hour, so they use the same day-long cache as research and eggs.
_TTL_SECONDS = SLOW_TTL_SECONDS
_TIMEOUT_SECONDS = 10.0
_UNAVAILABLE = "PvPoke data is unavailable."
_SIMULATIONS = "PvPoke simulations, not an official ladder."

_PVPOKE = "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data"
SPECIES_URL = f"{_PVPOKE}/gamemaster/pokemon.json"

# The cup directories rotate. Only these four open leagues are fetched, and
# the CP cap is the value we put in the path. A model string never is.
LEAGUES = ("little", "great", "ultra", "master")
LEAGUE_CP = {"little": 500, "great": 1500, "ultra": 2500, "master": 10000}
RANKING_LIMIT_DEFAULT = 10
RANKING_LIMIT_MAX = 25
_MATCHUP_LIMIT = 3

Fetcher = Callable[[str], Any]


def rankings_url(league: str) -> str:
    """URL for one allowlisted league. Caller has already checked `league`."""
    cp = LEAGUE_CP[league]
    return f"{_PVPOKE}/rankings/all/overall/rankings-{cp}.json"


def _http_fetch(url: str) -> Any:
    response = httpx2.get(url, timeout=httpx2.Timeout(_TIMEOUT_SECONDS))
    response.raise_for_status()
    return response.json()


def _name_key(value: str) -> str:
    """Fold a display name or species id onto PvPoke's speciesId shape."""
    text = value.strip().lower().replace("(", " ").replace(")", " ")
    text = text.replace("-", " ").replace("_", " ")
    return "_".join(part for part in text.split() if part)


def trim_species(row: dict[str, Any]) -> dict[str, Any]:
    types = row.get("types")
    stats = row.get("baseStats")
    trimmed: dict[str, Any] = {
        "species_id": row.get("speciesId"),
        "name": row.get("speciesName"),
        "base_stats": stats if isinstance(stats, dict) else {},
        "types": [item for item in types if isinstance(item, str) and item != "none"]
        if isinstance(types, list)
        else [],
        "fast_moves": _strings(row.get("fastMoves")),
        "charged_moves": _strings(row.get("chargedMoves")),
    }
    elite = row.get("eliteMoves")
    if isinstance(elite, list) and any(isinstance(item, str) for item in elite):
        trimmed["elite_moves"] = _strings(elite)
    if isinstance(row.get("level25CP"), int):
        trimmed["level_25_cp"] = row["level25CP"]
    ivs = row.get("defaultIVs")
    if isinstance(ivs, dict):
        trimmed["default_ivs"] = ivs
    return trimmed


def trim_ranking(row: dict[str, Any], rank: int, *, detailed: bool) -> dict[str, Any]:
    trimmed: dict[str, Any] = {
        "rank": rank,
        "species_id": row.get("speciesId"),
        "name": row.get("speciesName"),
        "rating": row.get("rating"),
        "moveset": _strings(row.get("moveset")),
    }
    if detailed:
        trimmed["matchups"] = _opponents(row.get("matchups"))
        trimmed["counters"] = _opponents(row.get("counters"))
    return trimmed


def _strings(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, str)]


def _opponents(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    kept: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("opponent"), str):
            continue
        kept.append({"opponent": item["opponent"], "rating": item.get("rating")})
        if len(kept) == _MATCHUP_LIMIT:
            break
    return kept


class StatsCache:
    """Process-local cache. Same stale rule as the LeekDuck feed cache."""

    def __init__(
        self,
        fetcher: Fetcher = _http_fetch,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._fetcher = fetcher
        self._clock = clock
        self._entries: dict[str, tuple[float, str, list[Any]]] = {}

    def load(self, key: str, url: str) -> dict[str, Any]:
        now = self._clock()
        cached = self._entries.get(key)
        if cached is not None and now - cached[0] < _TTL_SECONDS:
            return self._envelope(url, cached[1], cached[2], stale=False)
        try:
            payload = self._fetcher(url)
        except Exception as exc:
            logger.warning("PvPoke %s failed: %s: %s", key, type(exc).__name__, exc)
            if cached is None:
                return {"error": _UNAVAILABLE}
            return self._envelope(url, cached[1], cached[2], stale=True)
        if not isinstance(payload, list):
            logger.warning("PvPoke %s was not a list", key)
            if cached is None:
                return {"error": _UNAVAILABLE}
            return self._envelope(url, cached[1], cached[2], stale=True)
        fetched_at = datetime.now(UTC).isoformat()
        self._entries[key] = (now, fetched_at, payload)
        return self._envelope(url, fetched_at, payload, stale=False)

    def _envelope(
        self,
        url: str,
        fetched_at: str,
        payload: list[Any],
        stale: bool,
    ) -> dict[str, Any]:
        return {
            "source": "PvPoke",
            "source_url": url,
            "fetched_at": fetched_at,
            "stale": stale,
            "rows": payload,
        }


stats_cache = StatsCache()


def _species_index(rows: list[Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("speciesId"), str):
            logger.warning("Skipping a PvPoke species row that has no speciesId")
            continue
        index.setdefault(row["speciesId"], row)
        name = row.get("speciesName")
        if isinstance(name, str):
            index.setdefault(_name_key(name), row)
    return index


def _find_row(rows: list[Any], name: str) -> dict[str, Any] | None:
    key = _name_key(name)
    for row in rows:
        if not isinstance(row, dict):
            continue
        species_id = row.get("speciesId")
        species_name = row.get("speciesName")
        name_matches = isinstance(species_name, str) and _name_key(species_name) == key
        if species_id == key or name_matches:
            return row
    return None


def load_species() -> dict[str, Any]:
    loaded = stats_cache.load("species", SPECIES_URL)
    if "error" in loaded:
        return loaded
    return {key: value for key, value in loaded.items() if key != "rows"} | {
        "species": [
            trim_species(row)
            for row in loaded["rows"]
            if isinstance(row, dict) and isinstance(row.get("speciesId"), str)
        ]
    }


def get_go_pokemon(pokemon: list[str]) -> dict[str, Any]:
    """GO stats for the named species. A name that misses is reported as a miss."""
    if not isinstance(pokemon, list) or not pokemon:
        return {"error": "Pass at least one Pokemon name."}
    loaded = stats_cache.load("species", SPECIES_URL)
    if "error" in loaded:
        return loaded
    index = _species_index(loaded["rows"])
    found: dict[str, Any] = {}
    for name in pokemon:
        if not isinstance(name, str) or not name.strip():
            found[str(name)] = "Pokemon name is missing."
            continue
        row = index.get(_name_key(name))
        if row is None:
            found[name] = f"Pokemon '{name}' is not in the PvPoke gamemaster."
        else:
            found[name] = trim_species(row)
    result = {key: value for key, value in loaded.items() if key != "rows"}
    result["label"] = "PvPoke gamemaster"
    result["pokemon"] = found
    return result


def get_pvp_rankings(
    league: str,
    pokemon: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Overall PvPoke rankings for one open league. Cups are not a league."""
    if league not in LEAGUE_CP:
        return {"error": f"Unknown league '{league}'."}
    if limit is None:
        limit = RANKING_LIMIT_DEFAULT
    elif isinstance(limit, bool) or not isinstance(limit, int):
        return {"error": "Ranking limit must be an integer from 1 to 25."}
    elif not 1 <= limit <= RANKING_LIMIT_MAX:
        return {"error": "Ranking limit must be an integer from 1 to 25."}
    url = rankings_url(league)
    loaded = stats_cache.load(f"rankings-{league}", url)
    if "error" in loaded:
        return loaded
    rows = [row for row in loaded["rows"] if isinstance(row, dict)]
    result = {key: value for key, value in loaded.items() if key != "rows"}
    result["label"] = _SIMULATIONS
    result["league"] = league
    result["cp_cap"] = LEAGUE_CP[league]
    if pokemon is None:
        result["rankings"] = [
            trim_ranking(row, index + 1, detailed=False)
            for index, row in enumerate(rows[:limit])
            if isinstance(row.get("speciesId"), str)
        ]
        return result
    if not isinstance(pokemon, str) or not pokemon.strip():
        return {"error": "Pass a Pokemon name, or omit it for a top list."}
    match = _find_row(rows, pokemon)
    if match is None:
        result["pokemon"] = (
            f"'{pokemon}' is not in the PvPoke {league} League overall rankings."
        )
        return result
    rank = next(index + 1 for index, row in enumerate(rows) if row is match)
    result["pokemon"] = trim_ranking(match, rank, detailed=True)
    return result
