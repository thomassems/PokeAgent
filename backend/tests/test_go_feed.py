"""The Pokemon GO feed cache, without calling GitHub."""

import json
from typing import Any

import httpx2

from services.go_feed import LIVE_TTL_SECONDS, SLOW_TTL_SECONDS, FeedCache, clean_text

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


RESEARCH = [
    {
        "text": "<span>Catch 8 Pokémon</span>",
        "rewards": [
            {
                "name": "Pidgey",
                "image": "pidgey",
                "canBeShiny": False,
                "combatPower": {"min": 10, "max": 10},
            }
        ],
    },
    {
        "text": "Make 3 Great Throws",
        "type": "throw",
        "rewards": [{"name": "Stardust", "image": "dust"}],
    },
]

EGGS = [
    {
        "name": "Bulbasaur",
        "eggType": "1 km",
        "isAdventureSync": False,
        "image": "bulb",
        "canBeShiny": True,
        "combatPower": {"min": 637, "max": 637},
        "isRegional": False,
        "isGiftExchange": False,
        "rarity": 4,
    },
    {
        "name": "Alolan Meowth",
        "eggType": "7 km",
        "image": "meowth",
        "canBeShiny": False,
        "combatPower": {"min": 1, "max": 2},
        "isAdventureSync": False,
        "isRegional": False,
        "isGiftExchange": True,
        "rarity": 2,
    },
]

ROCKETS = [
    {
        "name": "Giovanni",
        "title": "Team GO Rocket Boss",
        "type": "",
        "firstPokemon": [
            {
                "name": "Persian",
                "image": "persian",
                "types": ["normal"],
                "isEncounter": False,
                "canBeShiny": False,
            }
        ],
        "secondPokemon": [],
        "thirdPokemon": [
            {
                "name": "Shadow Kyogre",
                "image": "kyogre",
                "types": ["water"],
                "isEncounter": True,
                "canBeShiny": False,
            }
        ],
    },
    {
        "name": "Decoy Female Grunt",
        "title": "Team GO Rocket Grunt",
        "type": "",
        "firstPokemon": [{"name": "Snorlax", "types": ["normal"], "image": "snorlax"}],
        "secondPokemon": [],
        "thirdPokemon": [],
    },
]


def test_slow_feeds_keep_a_payload_for_a_day() -> None:
    cache, calls, now = _cache(
        {"research": RESEARCH, "eggs": EGGS, "rocketLineups": ROCKETS}
    )
    first = cache.load("research")
    now["t"] = LIVE_TTL_SECONDS
    cache.load("research")
    assert len(calls) == 1

    now["t"] = SLOW_TTL_SECONDS
    cache.load("research")
    assert len(calls) == 2
    assert first["stale"] is False
    assert "research.min.json" in first["source_url"]


def test_research_keeps_untyped_rows_and_strips_html() -> None:
    cache, _, _ = _cache({"research": RESEARCH})
    result = cache.load("research")
    untyped, typed = result["research"]

    assert untyped["text"] == "Catch 8 Pokémon"
    assert "task_type" not in untyped
    assert untyped["rewards"][0]["name"] == "Pidgey"
    assert typed["task_type"] == "throw"
    assert "image" not in json.dumps(result)


def test_egg_pool_keeps_the_one_kilometre_distance() -> None:
    cache, _, _ = _cache({"eggs": EGGS})
    eggs = cache.load("eggs")["eggs"]

    assert [egg["distance"] for egg in eggs] == ["1 km", "7 km"]
    assert eggs[1]["is_gift_exchange"] is True
    assert "image" not in json.dumps(eggs)


def test_rocket_leaders_are_the_four_names_not_an_empty_type() -> None:
    cache, _, _ = _cache({"rocketLineups": ROCKETS})
    lineups = cache.load("rockets")["rockets"]

    assert lineups[0]["group"] == "leader"
    assert lineups[0]["third"][0]["is_encounter"] is True
    assert lineups[0]["third"][0]["types"] == ["water"]
    assert lineups[1]["group"] == "grunt"
    assert lineups[1]["name"] == "Decoy Female Grunt"
    assert "rocketLineups.min.json" in cache.load("rockets")["source_url"]
    assert "image" not in json.dumps(lineups)


def test_failed_refresh_with_nothing_cached_returns_an_error() -> None:
    def explode(url: str) -> Any:
        raise httpx2.HTTPError("down")

    result = FeedCache(explode, lambda: 0.0).load("events")
    assert result == {"error": "Pokemon GO event feed is unavailable."}
