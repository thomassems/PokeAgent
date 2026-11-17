from copy import deepcopy
from typing import Any

from data.dex import DEFENDING_CHARTS, LATEST_GENERATION, MOVES, POKEMON
from data.go_guides import GO_GUIDE_TOPICS
from services.go_feed import (
    EGG_DISTANCES,
    EVENT_TYPES,
    RAID_TIERS,
    RESEARCH_TYPES,
    ROCKET_GROUPS,
    load_feed,
)
from services.go_guide_search import search_go_guides
from services.go_stats import (
    LEAGUES,
    RANKING_LIMIT_MAX,
    get_go_pokemon,
    get_pvp_rankings,
)
from services.search import web_search
from services.strategy_search import search_strategy
from tools.dex_query import find_pokemon
from tools.go_types import go_type_roles
from tools.matchups import type_effectiveness, type_matchups


# data tool
# need to have normalization
def get_pokemon(pokemon, include_moves=False):
    # any way that mal intent queries can be input here and run?????
    pokemonmap = {}
    for p in pokemon:
        # first normalize p
        p_norm = p.strip().lower().replace(" ", "-")
        if p_norm in POKEMON:
            record = POKEMON[p_norm]
            if include_moves:
                pokemonmap[p] = deepcopy(record)
            else:
                # Movepools are ~80% of a record and are usually unwanted, so
                # they are dropped by default and replaced with a count.
                #
                # Copy first. POKEMON is the process-wide dex loaded once at
                # import, so mutating this record would delete the movepool for
                # every later call in the same process, not just this one.
                trimmed = {k: deepcopy(v) for k, v in record.items() if k != "moves"}
                trimmed["move_count"] = len(record["moves"])
                pokemonmap[p] = trimmed
        else:
            pokemonmap[p] = f"Pokemon {p_norm} does not exist"
    return pokemonmap


def get_move(moves):
    movemap = {}
    for m in moves:
        # first normalize p
        m_norm = m.strip().lower().replace(" ", "-")
        if m_norm in MOVES:
            movemap[m] = deepcopy(MOVES[m_norm])
        else:
            movemap[m] = "Move does not exist"
    return movemap


# Thin wrapper: the arithmetic lives in tools/ where it is pure and tested.
get_type_matchups = type_matchups
get_type_effectiveness = type_effectiveness
get_go_type_roles = go_type_roles


def get_current_events(event_type: str | None = None) -> dict[str, Any]:
    """Current LeekDuck events. `event_type` filters the cached list."""
    if event_type is not None and event_type not in EVENT_TYPES:
        return {"error": f"Unknown event type '{event_type}'."}
    payload = load_feed("events")
    if "error" in payload:
        return payload
    events = payload["events"]
    if event_type is not None:
        events = [event for event in events if event.get("event_type") == event_type]
    return {**payload, "events": events}


def get_research_rewards(task_type: str | None = None) -> dict[str, Any]:
    """Field research tasks. Rows with no type appear only when unfiltered."""
    if task_type is not None and task_type not in RESEARCH_TYPES:
        return {"error": f"Unknown research type '{task_type}'."}
    payload = load_feed("research")
    if "error" in payload:
        return payload
    tasks = payload["research"]
    if task_type is not None:
        tasks = [task for task in tasks if task.get("task_type") == task_type]
    return {**payload, "research": tasks}


def get_egg_pool(distance: str | None = None) -> dict[str, Any]:
    """Pokemon currently hatching from eggs. `distance` is the egg label."""
    if distance is not None and distance not in EGG_DISTANCES:
        return {"error": f"Unknown egg distance '{distance}'."}
    payload = load_feed("eggs")
    if "error" in payload:
        return payload
    eggs = payload["eggs"]
    if distance is not None:
        eggs = [egg for egg in eggs if egg.get("distance") == distance]
    return {**payload, "eggs": eggs}


def get_rocket_lineups(group: str | None = None) -> dict[str, Any]:
    """Team Rocket lineups. Leaders are the four named bosses."""
    if group is not None and group not in ROCKET_GROUPS:
        return {"error": f"Unknown Rocket group '{group}'."}
    payload = load_feed("rockets")
    if "error" in payload:
        return payload
    lineups = payload["rockets"]
    if group is not None:
        lineups = [row for row in lineups if row.get("group") == group]
    return {**payload, "rockets": lineups}


def get_raid_bosses(tier: str | None = None) -> dict[str, Any]:
    """Current raid bosses. An omitted tier returns every row in the feed."""
    if tier is not None and tier not in RAID_TIERS:
        return {"error": f"Unknown raid tier '{tier}'."}
    payload = load_feed("raids")
    if "error" in payload:
        return payload
    raids = payload["raids"]
    if tier is not None:
        raids = [boss for boss in raids if boss.get("tier") == tier]
    return {**payload, "raids": raids}


# web search tool

# vector db tool


# Schemas the model sees. Both agents import this list and pass it straight to
# tools=, so neither can be handed a different tool surface than the other.
#
# Property names match the function parameter names on purpose, so a tool call's
# input dict can be splatted into the function without remapping.
TOOLS = [
    {
        "name": "get_pokemon",
        "description": (
            "Look up one or more Pokemon by name. Returns base stats including "
            "base stat total, typing, abilities, the generation the form debuted, "
            "whether it is legendary or mythical, and how many moves it can learn. "
            "Pass every Pokemon you need in a single call rather than calling once "
            "per Pokemon. Set include_moves if you need the move list itself."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pokemon": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Pokemon names, for example ['Garchomp', 'Rotom-Wash']"
                    ),
                },
                "include_moves": {
                    "type": "boolean",
                    "description": (
                        "Optional, defaults to false. When false you get move_count "
                        "instead of the move list, which is far smaller. Set it true "
                        "only when you need to know which specific moves a Pokemon "
                        "can learn, such as judging offensive coverage."
                    ),
                },
            },
            "required": ["pokemon"],
        },
    },
    {
        "name": "get_move",
        "description": (
            "Look up type, damage category, power, accuracy and PP for one or more "
            "moves by name. Use this whenever a move's properties matter, including "
            "when judging what a Pokemon can actually hit, since offensive coverage "
            "comes from moves rather than from a Pokemon's own typing. Pass every "
            "move you need in a single call."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "moves": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Move names, for example ['Earthquake', 'Stone Edge']"
                    ),
                }
            },
            "required": ["moves"],
        },
    },
    {
        "name": "get_type_matchups",
        "description": (
            "Type effectiveness for one or more Pokemon, with dual-type "
            "multiplication already applied and grouped by multiplier, so a 4x "
            "weakness appears as 4 and an immunity as 0. Neutral types are omitted. "
            "Use direction='defending' for what hits them hard and what they resist. "
            "Use direction='attacking' for what their own types are strong against, "
            "which is same-type attack coverage only and ignores the moves they "
            "actually carry. Pass the whole team in one call."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pokemon": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Pokemon names, for example ['Garchomp', 'Ferrothorn']"
                    ),
                },
                "direction": {
                    "type": "string",
                    "enum": ["attacking", "defending"],
                    "description": (
                        "'defending' reads the chart against these Pokemon, "
                        "'attacking' reads it in their favour."
                    ),
                },
                "ability": {
                    "type": "string",
                    "description": (
                        "Optional. An ability that changes the matchup, such as "
                        "Levitate or Flash Fire. Most Pokemon have two or three "
                        "possible abilities and which one an individual has is not "
                        "knowable from the species, so supply it only when the user "
                        "has said which. Returns the ability's effect for you to "
                        "apply; it is not applied to the numbers for you."
                    ),
                },
                "generation": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 9,
                    "description": (
                        "Optional. Which generation's type chart to use. When "
                        "omitted, this uses the generation selected for the "
                        "question, or the latest generation if none is selected."
                    ),
                },
            },
            "required": ["pokemon", "direction"],
        },
    },
    {
        "name": "get_type_effectiveness",
        "description": (
            "Look up one attacking type into one defending type in a specific "
            "generation. Use this for raw chart questions like 'Ghost into Steel "
            "in generation 4'. Neutral pairs return 1.0, immunities return 0."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "attacker": {
                    "type": "string",
                    "enum": [
                        "normal",
                        "fighting",
                        "flying",
                        "poison",
                        "ground",
                        "rock",
                        "bug",
                        "ghost",
                        "steel",
                        "fire",
                        "water",
                        "grass",
                        "electric",
                        "psychic",
                        "ice",
                        "dragon",
                        "dark",
                        "fairy",
                    ],
                    "description": "The attacking move type.",
                },
                "defender": {
                    "type": "string",
                    "enum": [
                        "normal",
                        "fighting",
                        "flying",
                        "poison",
                        "ground",
                        "rock",
                        "bug",
                        "ghost",
                        "steel",
                        "fire",
                        "water",
                        "grass",
                        "electric",
                        "psychic",
                        "ice",
                        "dragon",
                        "dark",
                        "fairy",
                    ],
                    "description": "The defending target type.",
                },
                "generation": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 9,
                    "description": (
                        "Optional. Which generation's type chart to use. When "
                        "omitted, this uses the generation selected for the "
                        "question, or the latest generation if none is selected."
                    ),
                },
            },
            "required": ["attacker", "defender"],
        },
    },
    {
        "name": "web_search",
        "description": (
            "Search the web for information the dex does not hold. Use this for "
            "tiers, competitive formats, what is currently popular, categories like "
            "legendary or mythical, characters such as gym leaders and champions, or "
            "any term you cannot resolve from the other tools. Do not use it for base "
            "stats, typings, move data or type matchups, which are exact facts and "
            "come from the dex tools."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "maxLength": 400,
                    "description": "What to search for, phrased as a search query.",
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "How many results to return. Defaults to 5.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_strategy",
        "description": (
            "Search a curated strategy corpus for generation- and format-specific "
            "battle advice. Results are semantically retrieved, reranked, and include "
            "source metadata. Use this for roles, movesets, teammates, counters, team "
            "archetypes, and game plans. Use dex tools instead for exact stats, move "
            "properties, typings, and type effectiveness."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "maxLength": 500,
                    "description": (
                        "A focused strategy question to retrieve evidence for."
                    ),
                },
                "generation": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 9,
                    "description": "The generation whose strategy should be searched.",
                },
                "format": {
                    "type": "string",
                    "maxLength": 50,
                    "description": "Optional format identifier, for example 'ou'.",
                },
                "pokemon": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 6,
                    "description": "Optional Pokemon names used to filter results.",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": (
                        "How many reranked passages to return. Defaults to 5."
                    ),
                },
            },
            "required": ["query", "generation"],
        },
    },
    {
        "name": "find_pokemon",
        "description": (
            "Find Pokemon matching filters, when you do not already know the names. "
            "Use this for questions about a category rather than a specific Pokemon: "
            "legendaries, mythicals, everything of a type, everything from one "
            "generation, or the fastest thing meeting those constraints. Filters "
            "combine with AND and any you omit does not constrain. Returns names and "
            "the sorted stat only, so follow up with get_pokemon for the ones worth a "
            "closer look."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "normal",
                            "fighting",
                            "flying",
                            "poison",
                            "ground",
                            "rock",
                            "bug",
                            "ghost",
                            "steel",
                            "fire",
                            "water",
                            "grass",
                            "electric",
                            "psychic",
                            "ice",
                            "dragon",
                            "dark",
                            "fairy",
                        ],
                    },
                    "description": (
                        "Matches Pokemon carrying all of these types. One type finds "
                        "every Pokemon with it, two finds only that exact dual typing."
                    ),
                },
                "generation": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 9,
                    "description": "The generation the form debuted in.",
                },
                "is_legendary": {"type": "boolean"},
                "is_mythical": {"type": "boolean"},
                "sort_by": {
                    "type": "string",
                    "enum": [
                        "hp",
                        "attack",
                        "defense",
                        "special_attack",
                        "special_defense",
                        "speed",
                        "total",
                    ],
                    "description": "Sorted descending. Defaults to total base stats.",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "description": "How many to return. Defaults to 20.",
                },
            },
            "required": [],
        },
    },
]


# Dispatch map: tool name to the function that runs it. Both agents look a tool
# up here rather than growing an if/elif chain, so adding a tool touches this
# file and nothing else.
#
# Schema property names match each function's parameter names, so a tool call's
# input dict splats straight in: TOOL_FUNCTIONS[block.name](**block.input)
TOOL_FUNCTIONS = {
    "get_pokemon": get_pokemon,
    "get_move": get_move,
    "get_type_matchups": get_type_matchups,
    "get_type_effectiveness": get_type_effectiveness,
    "web_search": web_search,
    "search_strategy": search_strategy,
    "find_pokemon": find_pokemon,
    "get_current_events": get_current_events,
    "get_raid_bosses": get_raid_bosses,
    "get_research_rewards": get_research_rewards,
    "get_egg_pool": get_egg_pool,
    "get_rocket_lineups": get_rocket_lineups,
    "get_go_pokemon": get_go_pokemon,
    "get_pvp_rankings": get_pvp_rankings,
    "search_go_guides": search_go_guides,
    "get_go_type_roles": get_go_type_roles,
}


def _tool(name: str) -> dict[str, Any]:
    for tool in TOOLS:
        if tool["name"] == name:
            return tool
    raise KeyError(name)


# Pokemon GO sees the live feeds and the modern type chart. The main-series
# dex and the strategy corpus stay off this list: their numbers and advice
# are the wrong answer for a GO question. Both agents take this list from
# tools_for, so they cannot be handed different GO tools.
GO_TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_current_events",
        "description": (
            "List current Pokemon GO events from LeekDuck via ScrapedDuck. "
            "Includes Community Day, Spotlight Hour, raid hours, seasons, and "
            "raid-battles events. Mega and Shadow raid bosses are often on "
            "raid-battles events rather than in get_raid_bosses. Each event "
            "has start, end, and timing: local means the player's local time, "
            "utc means one global instant. The result includes fetched_at and "
            "stale."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "enum": list(EVENT_TYPES),
                    "description": (
                        "Optional. Limit the list to one event type, such as "
                        "community-day, pokemon-spotlight-hour, or raid-battles."
                    ),
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_raid_bosses",
        "description": (
            "List current Pokemon GO raid bosses from LeekDuck via ScrapedDuck, "
            "with tier, types, catch CP, and weather boost. Omit tier to return "
            "every boss in the raids feed, including a tier this schema does not "
            "name. Mega and Shadow bosses may be absent here and present on "
            "get_current_events with event_type raid-battles. The result includes "
            "fetched_at and stale."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tier": {
                    "type": "string",
                    "enum": list(RAID_TIERS),
                    "description": "Optional. Limit the list to one raid tier.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_research_rewards",
        "description": (
            "List current Pokemon GO field research tasks from LeekDuck via "
            "ScrapedDuck, with reward names, catch CP, and whether the reward "
            "can be shiny. Omit task_type to include tasks that have no type. "
            "A filter drops those untyped tasks. The result includes fetched_at "
            "and stale."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task_type": {
                    "type": "string",
                    "enum": list(RESEARCH_TYPES),
                    "description": (
                        "Optional. Limit the list to one task type, such as "
                        "catch, throw, battle, or rocket."
                    ),
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_egg_pool",
        "description": (
            "List Pokemon currently hatching from Pokemon GO eggs, from "
            "LeekDuck via ScrapedDuck. Distances include 1 km, which the "
            "wiki omits, plus 2 km, 5 km, 7 km, 10 km, and 12 km. Omit "
            "distance to return every pool. The result includes fetched_at "
            "and stale."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "distance": {
                    "type": "string",
                    "enum": list(EGG_DISTANCES),
                    "description": "Optional. Limit the pool to one egg distance.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_rocket_lineups",
        "description": (
            "List current Team GO Rocket lineups from LeekDuck via ScrapedDuck. "
            "Leaders are Giovanni, Cliff, Arlo, and Sierra. Everyone else, "
            "including the decoy, is a grunt. Each slot is a list of possible "
            "Pokemon, and is_encounter marks the one the player can catch. "
            "The result includes fetched_at and stale."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "group": {
                    "type": "string",
                    "enum": list(ROCKET_GROUPS),
                    "description": "Optional. leader or grunt.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_go_pokemon",
        "description": (
            "Look up Pokemon GO base stats, types, fast moves, charged moves, "
            "elite moves, level-25 CP, and default IVs from the PvPoke "
            "gamemaster. These are GO stats, not main-series base stats. A "
            "name that is missing is reported as a miss. Pass every species "
            "in one call."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pokemon": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Pokemon names, for example ['Medicham', 'Garchomp']."
                    ),
                },
            },
            "required": ["pokemon"],
        },
    },
    {
        "name": "get_pvp_rankings",
        "description": (
            "PvPoke overall rankings for an open league: little, great, ultra, "
            "or master. The numbers are PvPoke simulations, not an official "
            "ladder. The result says so, and includes fetched_at and stale. "
            "Pass pokemon for one species (rating, moveset, and a few "
            "matchups). Omit pokemon and set limit for a top list. List rows "
            "omit matchups. Cups such as Remix are not here. Use web_search "
            "for a cup."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "league": {
                    "type": "string",
                    "enum": list(LEAGUES),
                    "description": "little, great, ultra, or master.",
                },
                "pokemon": {
                    "type": "string",
                    "description": (
                        "Optional. One species, such as Medicham or Garchomp. "
                        "Omit for a top list."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": RANKING_LIMIT_MAX,
                    "description": "Optional. Top-list length. Default 10, maximum 25.",
                },
            },
            "required": ["league"],
        },
    },
    _tool("get_type_matchups"),
    _tool("get_type_effectiveness"),
    _tool("web_search"),
    {
        "name": "search_go_guides",
        "description": (
            "Search evergreen Pokemon GO mechanics: catching technique, Candy, "
            "Candy XL, trading, and the Mega Evolution catch-candy bonus. "
            "Results are written summaries with source metadata. Use this for "
            "how something works. Use the live feeds for what is happening now: "
            "events, raids, research, eggs, and Rocket lineups. Do not use "
            "this for main-series battle advice."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "maxLength": 500,
                    "description": "The mechanic to look up, phrased as a question.",
                },
                "topic": {
                    "type": "string",
                    "enum": list(GO_GUIDE_TOPICS),
                    "description": (
                        "Optional. Limit the search to one topic, such as "
                        "catching, candy, trading, mega, or items."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "How many passages to return. Defaults to 5.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_go_type_roles",
        "description": (
            "Split a catch's types into the Mega candy bonus and the raid "
            "counters. candy_bonus_types are the types you pass in: a Mega "
            "that shares one of them earns extra catch candy. super_effective "
            "is which attacks hit that typing hardest on the latest chart. "
            "Those are not the same choice. Pass one or two type names."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": sorted(DEFENDING_CHARTS[LATEST_GENERATION]),
                    },
                    "minItems": 1,
                    "maxItems": 2,
                    "description": "The types of the Pokemon being caught.",
                },
            },
            "required": ["types"],
        },
    },
]


def tools_for(game: str) -> list[dict[str, Any]]:
    """The tool list for this game. Main series is `TOOLS` unchanged."""
    if game == "go":
        return GO_TOOLS
    if game == "main":
        return TOOLS
    raise ValueError(f"Unknown game: {game}")


# Matchup tools fall back to the latest chart when generation is omitted.
# Both agents fill in a selected generation before the call, so the chart
# matches the question. An explicit generation on the call is left alone:
# the user may have named a different one in the text. find_pokemon's
# generation is a debut filter, not a chart, so it is not in this set.
# Pokemon GO always uses the latest chart. A stored main-series generation
# must not bring an old Steel resistance into a GO answer, so an explicit
# generation on a GO call is replaced too.
SELECTED_GENERATION_TOOLS = frozenset({"get_type_matchups", "get_type_effectiveness"})


def apply_selected_generation(
    tool_name: str,
    arguments: dict[str, Any],
    generation: int | None,
    game: str = "main",
) -> dict[str, Any]:
    """Copy `arguments` with the chart generation filled in when needed."""
    if tool_name not in SELECTED_GENERATION_TOOLS:
        return arguments
    if game == "go":
        return {**arguments, "generation": int(LATEST_GENERATION)}
    if generation is None or arguments.get("generation") is not None:
        return arguments
    return {**arguments, "generation": generation}
