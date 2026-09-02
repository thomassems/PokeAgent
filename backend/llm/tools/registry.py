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

def __init__():
    if __name__=='__main__':
        print(get_pokemon("garchomp"))