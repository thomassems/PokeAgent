# will store all 3 tools, for now will have 3 tools
import collections

from data.dex import ABILITIES, ATTACKING_CHART, DEFENDING_CHART, MOVES, POKEMON
from services.search import web_search
from tools.dex_query import find_pokemon


# data tool
# need to have normalization
def get_pokemon(pokemon, include_moves=False):
    # any way that mal intent queries can be input here and run?????
    print('calling get pokemon')
    pokemonmap = {}
    for p in pokemon:
        # first normalize p
        p_norm = p.strip().lower().replace(" ", "-")
        if p_norm in POKEMON:
            record = POKEMON[p_norm]
            if include_moves:
                pokemonmap[p] = record
            else:
                # Movepools are ~80% of a record and are usually unwanted, so
                # they are dropped by default and replaced with a count.
                #
                # Copy first. POKEMON is the process-wide dex loaded once at
                # import, so mutating this record would delete the movepool for
                # every later call in the same process, not just this one.
                trimmed = {k: v for k, v in record.items() if k != "moves"}
                trimmed["move_count"] = len(record["moves"])
                pokemonmap[p] = trimmed
        else:
            pokemonmap[p] = f"Pokemon {p_norm} does not exist" # OR don't have any info on this pokemon
    return pokemonmap

def get_move(moves):
    movemap = {}
    for m in moves:
        # first normalize p
        m_norm = m.strip().lower().replace(" ", "-")
        if m_norm in MOVES:
            movemap[m] = MOVES[m_norm]
        else:
            movemap[m] = "Move does not exist" # OR no info on this
    return movemap


def get_type_matchups(pokemon, direction, ability=None):
    # for defenders will be whatever is in type chart or 1.0
    # since matchups only store values when the pair is not 1.0
    typemap = collections.defaultdict(list)
    for p in pokemon:
        # first normalize p
        p_norm = p.strip().lower().replace(" ", "-")
        if p_norm in POKEMON:
            types = POKEMON[p_norm]["types"]
            for t in types:
                if direction == "attacking":
                    typemap[p].append(ATTACKING_CHART[t])
                elif direction == "defending":
                    typemap[p].append(DEFENDING_CHART[t])
                else:
                    typemap[p] = ["invalid direction provided"]
        else:
            typemap[p] = ["Couldn't find types for pokemon"]

    if ability is None:
        return typemap

    # An ability can override the chart entirely: Levitate ignores Ground,
    # Flash Fire ignores Fire. Which one an individual has is not a property of
    # the species, so it has to be supplied rather than inferred. The effect is
    # returned as text rather than applied, because the data stores prose and
    # not a structured "immune to ground" flag.
    ability_id = ability.strip().lower().replace(" ", "-")
    if ability_id not in ABILITIES:
        return {"error": f"Unknown ability '{ability}'.", "matchups": typemap}

    result = {"matchups": typemap, "ability": ABILITIES[ability_id]}
    unavailable = [
        p
        for p in pokemon
        if (norm := p.strip().lower().replace(" ", "-")) in POKEMON
        and ability_id not in {a["name"] for a in POKEMON[norm]["abilities"]}
    ]
    if unavailable:
        result["warning"] = (
            f"{', '.join(unavailable)} cannot have {ABILITIES[ability_id]['name']}. "
            "The matchups above ignore it."
        )
    return result


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
            "Look up one or more Pokemon by name. Returns base stats, typing, "
            "abilities, the generation the form debuted, whether it is legendary or "
            "mythical, and how many moves it can learn. Pass every Pokemon you need "
            "in a single call rather than calling once per Pokemon. Set include_moves "
            "if you need the move list itself."
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
            "Look up type effectiveness for one or more Pokemon, based on their own "
            "typing. Use direction='defending' for what hits them hard and what they "
            "resist. Use direction='attacking' for what their own types are strong "
            "against, which is same-type attack coverage only and does not account "
            "for the moves they actually carry. Pass the whole team in one call."
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
            },
            "required": ["pokemon", "direction"],
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
                            "normal", "fighting", "flying", "poison", "ground", "rock",
                            "bug", "ghost", "steel", "fire", "water", "grass",
                            "electric", "psychic", "ice", "dragon", "dark", "fairy",
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
                        "hp", "attack", "defense", "special_attack",
                        "special_defense", "speed", "total",
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
    "web_search": web_search,
    "find_pokemon": find_pokemon,
}