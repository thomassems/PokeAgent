"""Type effectiveness, with the dual-type arithmetic already done.

Returning raw chart rows and leaving the model to multiply them is where this
goes wrong. Ferrothorn is Grass/Steel, so Fire is 2x twice over for a 4x
weakness, and chains involving a 0 are worse still: one immunity beats any
number of weaknesses, and a model that multiplies 2 x 0 and reports "weak" is
confidently wrong with no way to notice.

Pure functions over data/. No network, no I/O, deterministic.
"""

from typing import Any

from data.dex import (
    ABILITIES,
    ATTACKING_CHARTS,
    DEFENDING_CHARTS,
    LATEST_GENERATION,
    POKEMON,
)


def _normalise(name: str) -> str:
    return name.strip().lower().replace(" ", "-")


def _bucket(profile: dict[str, float]) -> dict[str, list[str]]:
    """Group types by multiplier, dropping neutral.

    Neutral is the majority and carries no information, so omitting it cuts the
    payload by more than half and leaves only what a decision turns on.
    """
    buckets: dict[str, list[str]] = {}
    for type_name, multiplier in sorted(profile.items()):
        if multiplier == 1.0:
            continue
        # 4.0 not 4, 0.25 not 0.250: keys are read by a model, so keep them tidy.
        key = f"{multiplier:g}"
        buckets.setdefault(key, []).append(type_name)
    return dict(sorted(buckets.items(), key=lambda item: float(item[0]), reverse=True))


def _defending_profile(types: list[str], generation: str) -> dict[str, float]:
    """Multiply incoming damage across every type this Pokemon has."""
    chart = DEFENDING_CHARTS
    all_types = list(ATTACKING_CHARTS[generation])
    profile: dict[str, float] = {}
    for other in all_types:
        multiplier = 1.0
        for own in types:
            multiplier *= chart[generation][own].get(other, 1.0)
        profile[other] = multiplier
    return profile


def _attacking_profile(types: list[str], generation: str) -> dict[str, float]:
    """Use the best same-type attack multiplier against each defending type."""
    chart = ATTACKING_CHARTS
    all_types = list(chart[generation])
    profile: dict[str, float] = {}
    for defender in all_types:
        profile[defender] = max(
            chart[generation][attack_type].get(defender, 1.0)
            for attack_type in types
        )
    return profile


def _profile(types: list[str], direction: str, generation: str) -> dict[str, float]:
    if direction == "defending":
        return _defending_profile(types, generation)
    return _attacking_profile(types, generation)


def type_matchups(
    pokemon: list[str],
    direction: str,
    ability: str | None = None,
    generation: int | None = None,
) -> dict[str, Any]:
    """Type effectiveness for one or more Pokemon, bucketed by multiplier."""
    if direction not in ("attacking", "defending"):
        return {"error": "direction must be 'attacking' or 'defending'."}

    chart_key = str(generation) if generation is not None else LATEST_GENERATION
    if chart_key not in ATTACKING_CHARTS:
        return {"error": f"No type chart for generation {generation}."}

    ability_record = None
    if ability is not None:
        ability_id = _normalise(ability)
        if ability_id not in ABILITIES:
            return {"error": f"Unknown ability '{ability}'."}
        ability_record = {"id": ability_id, **ABILITIES[ability_id]}

    results: dict[str, Any] = {}
    for name in pokemon:
        identifier = _normalise(name)
        record = POKEMON.get(identifier)
        if record is None:
            results[name] = {"error": f"No Pokemon called '{name}' in the dex."}
            continue

        entry: dict[str, Any] = {
            "id": identifier,
            "types": record["types"],
            direction: _bucket(_profile(record["types"], direction, chart_key)),
        }
        if ability_record is not None:
            possible = {a["name"] for a in record["abilities"]}
            entry["ability"] = ability_record
            if ability_record["id"] not in possible:
                entry["ability_warning"] = (
                    f"{record['name']} cannot have {ability_record['name']}. "
                    "The multipliers above ignore it."
                )
        results[name] = entry

    return {"generation": int(chart_key), "matchups": results}


def type_effectiveness(
    attacker: str,
    defender: str,
    generation: int | None = None,
) -> dict[str, Any]:
    """One attacking type into one defending type."""
    chart_key = str(generation) if generation is not None else LATEST_GENERATION
    if chart_key not in ATTACKING_CHARTS:
        return {"error": f"No type chart for generation {generation}."}

    attacking_type = _normalise(attacker)
    defending_type = _normalise(defender)
    chart = ATTACKING_CHARTS[chart_key]
    if attacking_type not in chart:
        return {"error": f"Unknown attacking type '{attacker}'."}
    if defending_type not in chart:
        return {"error": f"Unknown defending type '{defender}'."}

    return {
        "generation": int(chart_key),
        "attacker": attacking_type,
        "defender": defending_type,
        "multiplier": chart[attacking_type].get(defending_type, 1.0),
    }
