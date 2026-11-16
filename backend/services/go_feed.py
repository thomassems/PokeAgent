"""Current Pokemon GO feeds from the ScrapedDuck mirror of LeekDuck.

The "endpoints" are JSON files on the `data` branch. This module caches
them in process memory. `tools/` does not import it: the fetch is why
`services/` exists.
"""

import html
import logging
import re
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx2

logger = logging.getLogger(__name__)

# Events and raids move during the day. Research, eggs, and Rocket lineups
# change more slowly, so they keep a payload for a day.
LIVE_TTL_SECONDS = 3 * 60 * 60
SLOW_TTL_SECONDS = 24 * 60 * 60

_DATA_BRANCH = "https://raw.githubusercontent.com/bigfoott/ScrapedDuck/data"
FEEDS: dict[str, tuple[str, int]] = {
    "events": (f"{_DATA_BRANCH}/events.min.json", LIVE_TTL_SECONDS),
    "raids": (f"{_DATA_BRANCH}/raids.min.json", LIVE_TTL_SECONDS),
    "research": (f"{_DATA_BRANCH}/research.min.json", SLOW_TTL_SECONDS),
    "eggs": (f"{_DATA_BRANCH}/eggs.min.json", SLOW_TTL_SECONDS),
    # The wiki's Endpoints page does not list this file. It is on the data
    # branch anyway, and the filename is not "rockets".
    "rockets": (f"{_DATA_BRANCH}/rocketLineups.min.json", SLOW_TTL_SECONDS),
}

# The wiki's eventType table. A value outside this list is rejected before
# any filtering, so the model cannot turn a free string into a request.
EVENT_TYPES = (
    "community-day",
    "event",
    "live-event",
    "pokemon-go-fest",
    "global-challenge",
    "safari-zone",
    "ticketed-event",
    "location-specific",
    "bonus-hour",
    "pokemon-spotlight-hour",
    "potential-ultra-unlock",
    "update",
    "season",
    "pokemon-go-tour",
    "go-pass",
    "ticketed",
    "pokestop-showcase",
    "wild-area",
    "city-safari",
    "research",
    "timed-research",
    "limited-research",
    "research-breakthrough",
    "special-research",
    "research-day",
    "raid-day",
    "raid-battles",
    "raid-hour",
    "raid-weekend",
    "go-battle-league",
    "elite-raids",
    "max-battles",
    "max-mondays",
    "go-rocket-takeover",
    "team-go-rocket",
    "giovanni-special-research",
)

# Live raids.json uses the star labels. Mega is on the wiki. Shadow and Mega
# bosses often arrive as raid-battles events instead of rows in this file.
RAID_TIERS = ("1-Star Raids", "3-Star Raids", "5-Star Raids", "Mega")

# Wiki task types. The live file omits `type` on some rows, and a snapshot
# may not use every value. Rows with no type stay in the unfiltered list.
RESEARCH_TYPES = (
    "catch",
    "throw",
    "battle",
    "explore",
    "training",
    "rocket",
    "buddy",
    "ar",
    "sponsored",
    "event",
)

# `1 km` is in the live eggs file and missing from the wiki's allowed list.
EGG_DISTANCES = ("1 km", "2 km", "5 km", "7 km", "10 km", "12 km")

# Leaders are these four names. An empty `type` is not enough: untyped
# grunts and the decoy also have `type: ""`.
ROCKET_LEADERS = frozenset({"Giovanni", "Cliff", "Arlo", "Sierra"})
ROCKET_GROUPS = ("leader", "grunt")

_TIMEOUT_SECONDS = 10.0
_HTML_TAGS = re.compile(r"<[^>]+>")
_UNAVAILABLE = "Pokemon GO event feed is unavailable."

Fetcher = Callable[[str], Any]


def clean_text(value: str) -> str:
    """Drop HTML tags the LeekDuck feed leaves in titles and task text."""
    return html.unescape(_HTML_TAGS.sub("", value)).strip()


def _http_fetch(url: str) -> Any:
    response = httpx2.get(url, timeout=httpx2.Timeout(_TIMEOUT_SECONDS))
    response.raise_for_status()
    return response.json()


def _names(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    names: list[str] = []
    for item in items:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            names.append(clean_text(item["name"]))
    return names


def _texts(items: Any, key: str = "text") -> list[str]:
    if not isinstance(items, list):
        return []
    texts: list[str] = []
    for item in items:
        if isinstance(item, str):
            texts.append(clean_text(item))
        elif isinstance(item, dict) and isinstance(item.get(key), str):
            texts.append(clean_text(item[key]))
    return texts


def _timing(start: Any, end: Any) -> str | None:
    """Local clock unless the feed marks the instant as UTC with a trailing Z."""
    for value in (start, end):
        if isinstance(value, str) and value:
            return "utc" if value.endswith("Z") else "local"
    return None


def _extra(raw: Any) -> dict[str, Any]:
    """Keep the fields a question needs and drop images and unknown branches."""
    if not isinstance(raw, dict):
        return {}
    kept: dict[str, Any] = {}
    generic = raw.get("generic")
    if isinstance(generic, dict):
        kept["generic"] = {
            "has_spawns": bool(generic.get("hasSpawns")),
            "has_field_research": bool(generic.get("hasFieldResearchTasks")),
        }
    spotlight = raw.get("spotlight")
    if isinstance(spotlight, dict):
        name = spotlight.get("name")
        bonus = spotlight.get("bonus")
        kept["spotlight"] = {
            "name": clean_text(name) if isinstance(name, str) else None,
            "bonus": clean_text(bonus) if isinstance(bonus, str) else None,
            "pokemon": _names(spotlight.get("list")),
        }
    community = raw.get("communityday")
    if isinstance(community, dict):
        research: list[dict[str, Any]] = []
        steps = community.get("specialresearch")
        if isinstance(steps, list):
            for step in steps:
                if not isinstance(step, dict):
                    continue
                name = step.get("name")
                research.append(
                    {
                        "name": clean_text(name) if isinstance(name, str) else None,
                        "step": step.get("step"),
                        "tasks": _texts(step.get("tasks")),
                    }
                )
        kept["community_day"] = {
            "spawns": _names(community.get("spawns")),
            "bonuses": _texts(community.get("bonuses")),
            "bonus_disclaimers": _texts(community.get("bonusDisclaimers")),
            "shinies": _names(community.get("shinies")),
            "special_research": research,
        }
    raids = raw.get("raidbattles")
    if isinstance(raids, dict):
        bosses: list[dict[str, Any]] = []
        for boss in raids.get("bosses") or []:
            if isinstance(boss, dict) and isinstance(boss.get("name"), str):
                bosses.append(
                    {
                        "name": clean_text(boss["name"]),
                        "can_be_shiny": boss.get("canBeShiny"),
                    }
                )
        kept["raid_bosses"] = {
            "bosses": bosses,
            "shinies": _names(raids.get("shinies")),
        }
    return kept


def trim_event(row: dict[str, Any]) -> dict[str, Any]:
    name = row.get("name")
    heading = row.get("heading")
    return {
        "event_id": row.get("eventID"),
        "name": clean_text(name) if isinstance(name, str) else None,
        "event_type": row.get("eventType"),
        "heading": clean_text(heading) if isinstance(heading, str) else None,
        "link": row.get("link"),
        "start": row.get("start"),
        "end": row.get("end"),
        "timing": _timing(row.get("start"), row.get("end")),
        "extra": _extra(row.get("extraData")),
    }


def trim_research(row: dict[str, Any]) -> dict[str, Any]:
    text = row.get("text")
    rewards: list[dict[str, Any]] = []
    for reward in row.get("rewards") or []:
        if not isinstance(reward, dict):
            continue
        name = reward.get("name")
        rewards.append(
            {
                "name": clean_text(name) if isinstance(name, str) else None,
                "can_be_shiny": reward.get("canBeShiny"),
                "combat_power": reward.get("combatPower"),
            }
        )
    trimmed: dict[str, Any] = {
        "text": clean_text(text) if isinstance(text, str) else None,
        "rewards": rewards,
    }
    # Absent on purpose. A missing type must not look like a real category.
    if isinstance(row.get("type"), str):
        trimmed["task_type"] = row["type"]
    return trimmed


def trim_egg(row: dict[str, Any]) -> dict[str, Any]:
    name = row.get("name")
    return {
        "name": clean_text(name) if isinstance(name, str) else None,
        "distance": row.get("eggType"),
        "can_be_shiny": row.get("canBeShiny"),
        "combat_power": row.get("combatPower"),
        "is_adventure_sync": row.get("isAdventureSync"),
        "is_regional": row.get("isRegional"),
        "is_gift_exchange": row.get("isGiftExchange"),
        "rarity": row.get("rarity"),
    }


def _rocket_slot(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    slot: list[dict[str, Any]] = []
    for mon in items:
        if not isinstance(mon, dict) or not isinstance(mon.get("name"), str):
            continue
        types = mon.get("types")
        slot.append(
            {
                "name": clean_text(mon["name"]),
                "types": [item for item in types if isinstance(item, str)]
                if isinstance(types, list)
                else [],
                "is_encounter": mon.get("isEncounter"),
                "can_be_shiny": mon.get("canBeShiny"),
            }
        )
    return slot


def trim_rocket(row: dict[str, Any]) -> dict[str, Any]:
    name = clean_text(row["name"]) if isinstance(row.get("name"), str) else None
    title = row.get("title")
    rocket_type = row.get("type")
    return {
        "name": name,
        "title": clean_text(title) if isinstance(title, str) else None,
        "type": rocket_type if isinstance(rocket_type, str) else "",
        "group": "leader" if name in ROCKET_LEADERS else "grunt",
        "first": _rocket_slot(row.get("firstPokemon")),
        "second": _rocket_slot(row.get("secondPokemon")),
        "third": _rocket_slot(row.get("thirdPokemon")),
    }


def trim_raid(row: dict[str, Any]) -> dict[str, Any]:
    types = row.get("types")
    weather = row.get("boostedWeather")
    return {
        "name": clean_text(row["name"]) if isinstance(row.get("name"), str) else None,
        "tier": row.get("tier"),
        "can_be_shiny": row.get("canBeShiny"),
        "types": _names(types) if isinstance(types, list) else [],
        "combat_power": row.get("combatPower"),
        "boosted_weather": _names(weather) if isinstance(weather, list) else [],
    }


def _trim(name: str, payload: list[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in payload:
        if not isinstance(row, dict):
            logger.warning("Skipping a %s row that is not an object", name)
            continue
        if name == "research":
            if not isinstance(row.get("text"), str):
                logger.warning("Skipping a research row that has no text")
                continue
            rows.append(trim_research(row))
            continue
        if not isinstance(row.get("name"), str):
            logger.warning("Skipping a %s row that has no name", name)
            continue
        if name == "events":
            rows.append(trim_event(row))
        elif name == "eggs":
            rows.append(trim_egg(row))
        elif name == "rockets":
            rows.append(trim_rocket(row))
        else:
            rows.append(trim_raid(row))
    return rows


class FeedCache:
    """One process-local cache. Tests build their own instead of sharing this."""

    def __init__(
        self,
        fetcher: Fetcher = _http_fetch,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._fetcher = fetcher
        self._clock = clock
        # monotonic fetch time, wall-clock stamp, raw JSON list
        self._entries: dict[str, tuple[float, str, list[Any]]] = {}

    def load(self, name: str) -> dict[str, Any]:
        if name not in FEEDS:
            return {"error": f"Unknown Pokemon GO feed '{name}'."}
        url, ttl = FEEDS[name]
        now = self._clock()
        cached = self._entries.get(name)
        if cached is not None and now - cached[0] < ttl:
            return self._envelope(name, url, cached[1], cached[2], stale=False)
        try:
            payload = self._fetcher(url)
        except Exception as exc:
            logger.warning(
                "Pokemon GO feed %s failed: %s: %s", name, type(exc).__name__, exc
            )
            if cached is None:
                return {"error": _UNAVAILABLE}
            return self._envelope(name, url, cached[1], cached[2], stale=True)
        if not isinstance(payload, list):
            logger.warning("Pokemon GO feed %s was not a list", name)
            if cached is None:
                return {"error": _UNAVAILABLE}
            return self._envelope(name, url, cached[1], cached[2], stale=True)
        fetched_at = datetime.now(UTC).isoformat()
        self._entries[name] = (now, fetched_at, payload)
        return self._envelope(name, url, fetched_at, payload, stale=False)

    def _envelope(
        self,
        name: str,
        url: str,
        fetched_at: str,
        payload: list[Any],
        stale: bool,
    ) -> dict[str, Any]:
        return {
            "source": "LeekDuck via ScrapedDuck",
            "source_url": url,
            "fetched_at": fetched_at,
            "stale": stale,
            name: _trim(name, payload),
        }


feed_cache = FeedCache()


def load_feed(name: str) -> dict[str, Any]:
    return feed_cache.load(name)
