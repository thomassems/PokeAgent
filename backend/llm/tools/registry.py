# will store all 3 tools, for now will have 3 tools
import collections

from data.dex import MOVES, POKEMON, ATTACKING_CHART, DEFENDING_CHART

# data tool
# need to have normalization
def get_pokemon(pokemon):
    # any way that mal intent queries can be input here and run?????
    print('calling get pokemon')
    pokemonmap = {}
    for p in pokemon:
        # first normalize p
        p_norm = p.strip().lower().replace(" ", "-")
        if p_norm in POKEMON:
            pokemonmap[p] = POKEMON[p_norm]
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


def get_type_matchups(pokemon, direction):
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
                    typemap[p]= ["invalid direction provided"]
        else:
            typemap[p] = ["Couldn't find types for pokemon"]
    return typemap


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
            "Look up base stats, typing and moveset for one or more Pokemon by name. "
            "Pass every Pokemon you need in a single call rather than calling once "
            "per Pokemon."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pokemon": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Pokemon names, for example ['Garchomp', 'Rotom-Wash']",
                }
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
                    "description": "Move names, for example ['Earthquake', 'Stone Edge']",
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
                    "description": "Pokemon names, for example ['Garchomp', 'Ferrothorn']",
                },
                "direction": {
                    "type": "string",
                    "enum": ["attacking", "defending"],
                    "description": (
                        "'defending' reads the chart against these Pokemon, "
                        "'attacking' reads it in their favour."
                    ),
                },
            },
            "required": ["pokemon", "direction"],
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
}
