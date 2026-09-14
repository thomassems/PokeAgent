"""One-time fetch: build the baked dex from PokeAPI's CSV source data.

Never imported at runtime. Run by hand when the data needs refreshing:

    uv run python data/fetch_dex.py

Pulls CSVs from the PokeAPI repository rather than calling the API. The API
would be thousands of requests against a service whose fair use policy asks you
to cache, while the same data ships as CSV in the repo under BSD-3-Clause.

Emits the three files data/dex.py loads, in the schema it already expects.
"""

import csv
import json
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

RAW = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/"
HERE = Path(__file__).parent
CACHE = HERE / ".cache"

ENGLISH = "9"

# Only the six base stats. Ids 7 and 8 are accuracy and evasion, which are battle
# modifiers rather than anything a Pokemon has a base value for.
STAT_IDS = {
    "1": "hp",
    "2": "attack",
    "3": "defense",
    "4": "special_attack",
    "5": "special_defense",
    "6": "speed",
}

NEEDED = [
    "pokemon.csv",
    "pokemon_species.csv",
    "pokemon_species_names.csv",
    "pokemon_types.csv",
    "pokemon_stats.csv",
    "pokemon_moves.csv",
    "types.csv",
    "type_efficacy.csv",
    "type_efficacy_past.csv",
    "generations.csv",
    "moves.csv",
    "move_names.csv",
    "move_damage_classes.csv",
    "abilities.csv",
    "ability_names.csv",
    "ability_prose.csv",
    "pokemon_abilities.csv",
]


def fetch(name: str) -> Path:
    """Download one CSV unless it is already cached."""
    CACHE.mkdir(exist_ok=True)
    path = CACHE / name
    if not path.exists():
        print(f"  downloading {name}")
        urllib.request.urlretrieve(RAW + name, path)
    return path


def rows(name: str) -> list[dict[str, str]]:
    with fetch(name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


# "unknown" and "shadow" are placeholders with no battle meaning. "stellar" is
# the Gen 9 Terastal type: it has no type_efficacy rows at all, so including it
# yields an empty chart row and breaks the eighteen type invariant everything
# else assumes.
_NOT_BATTLE_TYPES = {"unknown", "shadow", "stellar"}


def build_types() -> dict[str, str]:
    """Type id to identifier, dropping types that never appear in the chart."""
    return {
        r["id"]: r["identifier"]
        for r in rows("types.csv")
        if r["identifier"] not in _NOT_BATTLE_TYPES
    }


def build_charts(types: dict[str, str]) -> dict[str, dict[str, dict[str, float]]]:
    """One chart per generation, attacker to defender, non-neutral pairs only.

    The chart is not stable across generations. Steel resisted Ghost and Dark
    until Gen 6, and Gen 1 had Poison and Bug super effective against each other
    with Ghost doing nothing to Psychic. type_efficacy_past.csv records what a
    pair used to be, keyed by the last generation that value applied to.

    Types are also filtered by generation: Steel and Dark arrive in Gen 2, Fairy
    in Gen 6, so an early generation chart is genuinely smaller.
    """
    type_gen = {r["id"]: int(r["generation_id"]) for r in rows("types.csv")}
    latest = max(int(r["id"]) for r in rows("generations.csv"))

    # Work on a full matrix so an override back to 1.0 removes the pair rather
    # than being invisible, then sparsify at the end.
    full = {a: dict.fromkeys(types.values(), 1.0) for a in types.values()}
    for r in rows("type_efficacy.csv"):
        if r["damage_type_id"] in types and r["target_type_id"] in types:
            attacker, defender = types[r["damage_type_id"]], types[r["target_type_id"]]
            full[attacker][defender] = int(r["damage_factor"]) / 100

    past = [
        (
            int(r["generation_id"]),
            types[r["damage_type_id"]],
            types[r["target_type_id"]],
            int(r["damage_factor"]) / 100,
        )
        for r in rows("type_efficacy_past.csv")
        if r["damage_type_id"] in types and r["target_type_id"] in types
    ]

    charts: dict[str, dict[str, dict[str, float]]] = {}
    for generation in range(1, latest + 1):
        existing = {name for tid, name in types.items() if type_gen[tid] <= generation}
        matrix = {a: dict(row) for a, row in full.items() if a in existing}
        for applies_until, attacker, defender, factor in past:
            reachable = attacker in matrix and defender in existing
            if generation <= applies_until and reachable:
                matrix[attacker][defender] = factor
        charts[str(generation)] = {
            a: {d: f for d, f in row.items() if d in existing and f != 1.0}
            for a, row in matrix.items()
        }
    return charts


def build_moves(types: dict[str, str]) -> dict[str, dict[str, Any]]:
    names = {
        r["move_id"]: r["name"]
        for r in rows("move_names.csv")
        if r["local_language_id"] == ENGLISH
    }
    categories = {r["id"]: r["identifier"] for r in rows("move_damage_classes.csv")}

    moves: dict[str, dict[str, Any]] = {}
    for r in rows("moves.csv"):
        if r["type_id"] not in types:
            continue
        moves[r["identifier"]] = {
            "name": names.get(r["id"], r["identifier"]),
            "type": types[r["type_id"]],
            "category": categories.get(r["damage_class_id"], "status"),
            # Blank in the CSV means the field does not apply: status moves have
            # no power, and moves that never miss have no accuracy check.
            "power": int(r["power"]) if r["power"] else None,
            "accuracy": int(r["accuracy"]) if r["accuracy"] else None,
            "pp": int(r["pp"]) if r["pp"] else None,
        }
    return moves


def build_abilities() -> dict[str, dict[str, Any]]:
    """Ability id to name and a one line effect.

    The effect text is the point. "Levitate" tells a model nothing; "Evades
    Ground moves" tells it that the type chart is about to be wrong. Uses
    short_effect rather than the full prose, which runs to paragraphs.
    """
    names = {
        r["ability_id"]: r["name"]
        for r in rows("ability_names.csv")
        if r["local_language_id"] == ENGLISH
    }
    effects = {
        r["ability_id"]: r["short_effect"]
        for r in rows("ability_prose.csv")
        if r["local_language_id"] == ENGLISH
    }
    return {
        r["identifier"]: {
            "name": names.get(r["id"], r["identifier"]),
            "effect": effects.get(r["id"], ""),
        }
        for r in rows("abilities.csv")
        if r["is_main_series"] == "1"
    }


def build_pokemon(
    types: dict[str, str], move_ids: set[str]
) -> dict[str, dict[str, Any]]:
    species = {r["id"]: r for r in rows("pokemon_species.csv")}
    species_gen = {sid: int(r["generation_id"]) for sid, r in species.items()}
    species_name = {
        r["pokemon_species_id"]: r["name"]
        for r in rows("pokemon_species_names.csv")
        if r["local_language_id"] == ENGLISH
    }

    slots: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for r in rows("pokemon_types.csv"):
        if r["type_id"] in types:
            slots[r["pokemon_id"]].append((int(r["slot"]), types[r["type_id"]]))

    stats: dict[str, dict[str, int]] = defaultdict(dict)
    for r in rows("pokemon_stats.csv"):
        if r["stat_id"] in STAT_IDS:
            stats[r["pokemon_id"]][STAT_IDS[r["stat_id"]]] = int(r["base_stat"])
    for pokemon_stats in stats.values():
        pokemon_stats["total"] = sum(pokemon_stats[stat] for stat in STAT_IDS.values())

    # One flat set of distinct moves per Pokemon. The CSV carries a row per
    # version group, learn method and level; none of that is in the schema the
    # tools read, so it collapses here rather than shipping unused detail.
    ability_identifier = {r["id"]: r["identifier"] for r in rows("abilities.csv")}
    abilities: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in sorted(rows("pokemon_abilities.csv"), key=lambda r: int(r["slot"])):
        identifier = ability_identifier.get(r["ability_id"])
        if identifier:
            abilities[r["pokemon_id"]].append(
                {"name": identifier, "hidden": r["is_hidden"] == "1"}
            )

    identifier_by_move_id = {r["id"]: r["identifier"] for r in rows("moves.csv")}
    learnsets: dict[str, set[str]] = defaultdict(set)
    for r in rows("pokemon_moves.csv"):
        identifier = identifier_by_move_id.get(r["move_id"])
        if identifier in move_ids:
            learnsets[r["pokemon_id"]].add(identifier)

    dex: dict[str, dict[str, Any]] = {}
    default_of_species: dict[str, str] = {}
    species_of_identifier: dict[str, str] = {}
    for r in rows("pokemon.csv"):
        pid, species_id = r["id"], r["species_id"]
        if pid not in slots or pid not in stats:
            continue
        dex[r["identifier"]] = {
            "name": species_name.get(species_id, r["identifier"]),
            "types": [t for _, t in sorted(slots[pid])],
            "stats": stats[pid],
            "generation": species_gen.get(species_id),
            "is_legendary": species[species_id]["is_legendary"] == "1",
            "is_mythical": species[species_id]["is_mythical"] == "1",
            "abilities": abilities.get(pid, []),
            "moves": sorted(learnsets.get(pid, ())),
        }
        species_of_identifier[r["identifier"]] = species_id
        if r["is_default"] == "1":
            default_of_species[species_id] = r["identifier"]

    # Newly added forms sometimes have no move rows upstream yet: both of the
    # Legends Z-A Megas land here with an empty learnset. A Mega shares its base
    # form's movepool, and an empty list reads to a model as "learns nothing"
    # rather than "not recorded", so fall back to the default form.
    for identifier, record in dex.items():
        if not record["moves"]:
            base = default_of_species.get(species_of_identifier.get(identifier, ""))
            if base and base != identifier and dex.get(base, {}).get("moves"):
                record["moves"] = dex[base]["moves"]
                record["moves_inherited_from"] = base

    # Thirty-odd species are stored only under a form identifier: there is no
    # "mimikyu", only "mimikyu-disguised". A caller asking for the plain name is
    # asking for the default form, so alias it rather than reporting that a
    # perfectly real Pokemon does not exist.
    for r in rows("pokemon_species.csv"):
        name, default = r["identifier"], default_of_species.get(r["id"])
        if name not in dex and default in dex:
            dex[name] = dex[default]
    return dex


def write(filename: str, payload: dict[str, Any]) -> None:
    path = HERE / filename
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"  wrote {filename:20} {path.stat().st_size / 1_048_576:6.2f} MB")


def main() -> None:
    print("fetching PokeAPI CSVs")
    types = build_types()

    charts = build_charts(types)
    moves = build_moves(types)
    abilities = build_abilities()
    pokemon = build_pokemon(types, set(moves))

    note = (
        "Generated by data/fetch_dex.py from PokeAPI CSV source data "
        "(BSD-3-Clause). Do not edit by hand."
    )
    print("\nwriting")
    write(
        "type-chart.json",
        {
            "note": note
            + " One chart per generation, attacker keyed to defender. Any pair"
            " not listed is 1.0 (neutral). Early generations have fewer types.",
            "multipliers": {
                "super_effective": 2,
                "neutral": 1,
                "not_very_effective": 0.5,
                "no_effect": 0,
            },
            "latest_generation": max(int(g) for g in charts),
            "charts": charts,
        },
    )
    write("moves.json", {"note": note, "moves": moves})
    write("abilities.json", {"note": note, "abilities": abilities})
    write("pokemon.json", {"note": note, "pokemon": pokemon})

    print(f"\n  {len(pokemon)} pokemon, {len(moves)} moves, "
          f"{len(abilities)} abilities, {len(charts)} generation charts")


if __name__ == "__main__":
    main()
