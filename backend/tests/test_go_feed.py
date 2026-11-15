"""The Pokemon GO feed cache, without calling GitHub."""

import json
from typing import Any

import httpx2

from services.go_feed import LIVE_TTL_SECONDS, FeedCache, clean_text

EVENTS = [
    {
        "eventID": "cd",
        "name": "Pawniard <span>Community Day</span>",
        "eventType": "community-day",
        "heading": "Community Day",
        "link": "https://www.leekduck.com/events/cd/",
        "image": "https://example.test/cd.jpg",
        "start": "2026-11-15T14:00:00.000",
        "end": "2026-11-15T17:00:00.000",
        "extraData": {
            "generic": {"hasSpawns": True, "hasFieldResearchTasks": False},
            "communityday": {
                "spawns": [{"name": "Pawniard", "image": "spawn"}],
                "bonuses": [{"text": "1/4 Egg Hatch Distance", "image": "bonus"}],
                "bonusDisclaimers": ["* Disclaimer"],
                "shinies": [{"name": "Pawniard", "image": "shiny"}],
                "specialresearch": [
                    {
                        "name": "Field Notes",
                        "step": 1,
                        "tasks": [{"text": "Catch 3 <span>Pawniard</span>"}],
                    }
                ],
            },
            "unknown-branch": {"image": "nope"},
        },
    },
    {
        "eventID": "spot",
        "name": "Noibat Spotlight Hour",
        "eventType": "pokemon-spotlight-hour",
        "heading": "Spotlight Hour",
        "link": "https://www.leekduck.com/events/spot/",
        "image": "https://example.test/spot.jpg",
        "start": "2026-11-17T18:00:00.000Z",
        "end": "2026-11-17T19:00:00.000Z",
        "extraData": {
            "spotlight": {
                "name": "Noibat",
                "bonus": "2x Catch Candy",
                "image": "icon",
                "list": [{"name": "Noibat", "image": "icon"}],
            }
        },
    },
    {"eventID": "broken"},
]

RAIDS = [
    {
        "name": "Cresselia",
        "tier": "5-Star Raids",
        "canBeShiny": True,
        "types": [{"name": "psychic", "image": "type"}],
        "combatPower": {
            "normal": {"min": 1, "max": 2},
            "boosted": {"min": 3, "max": 4},
        },
        "boostedWeather": [{"name": "windy", "image": "weather"}],
        "image": "boss",
    },
    {"tier": "Mega"},
]


def _cache(
    payloads: dict[str, Any], fail_after: int = 0
) -> tuple[FeedCache, list[str], dict[str, float]]:
    calls: list[str] = []
    now = {"t": 0.0}

    def fetch(url: str) -> Any:
        calls.append(url)
        if fail_after and len(calls) > fail_after:
            raise httpx2.HTTPError("down")
        for name, payload in payloads.items():
            if url.endswith(f"/{name}.min.json"):
                return payload
        raise AssertionError(url)

    return FeedCache(fetch, lambda: now["t"]), calls, now


def test_clean_text_strips_html() -> None:
    assert clean_text("Catch 5 <span>Pokemon</span>") == "Catch 5 Pokemon"


def test_fresh_events_are_trimmed_and_cached() -> None:
    cache, calls, now = _cache({"events": EVENTS, "raids": RAIDS})
    first = cache.load("events")
    second = cache.load("events")

    assert first["stale"] is False
    assert first["source"] == "LeekDuck via ScrapedDuck"
    assert "events.min.json" in first["source_url"]
    assert len(calls) == 1
    assert second["fetched_at"] == first["fetched_at"]
    assert len(calls) == 1

    community = first["events"][0]
    assert community["name"] == "Pawniard Community Day"
    assert community["timing"] == "local"
    assert community["extra"]["community_day"]["spawns"] == ["Pawniard"]
    assert community["extra"]["community_day"]["special_research"][0]["tasks"] == [
        "Catch 3 Pawniard"
    ]
    assert "unknown-branch" not in community["extra"]
    assert "image" not in json.dumps(first)

    spotlight = first["events"][1]
    assert spotlight["timing"] == "utc"
    assert spotlight["extra"]["spotlight"]["bonus"] == "2x Catch Candy"
    assert len(first["events"]) == 2

    now["t"] = LIVE_TTL_SECONDS
    cache.load("events")
    assert len(calls) == 2


def test_failed_refresh_serves_the_previous_payload() -> None:
    cache, calls, now = _cache({"raids": RAIDS}, fail_after=1)
    fresh = cache.load("raids")
    now["t"] = LIVE_TTL_SECONDS
    stale = cache.load("raids")

    assert fresh["stale"] is False
    assert stale["stale"] is True
    assert stale["fetched_at"] == fresh["fetched_at"]
    assert stale["raids"][0]["types"] == ["psychic"]
    assert stale["raids"][0]["boosted_weather"] == ["windy"]
    assert len(stale["raids"]) == 1
    assert len(calls) == 2


def test_failed_refresh_with_nothing_cached_returns_an_error() -> None:
    def explode(url: str) -> Any:
        raise httpx2.HTTPError("down")

    result = FeedCache(explode, lambda: 0.0).load("events")
    assert result == {"error": "Pokemon GO event feed is unavailable."}
