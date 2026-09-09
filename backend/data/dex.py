"""Loads the baked dex into module-level constants.

This is the only place in the backend that reads game data off disk. Python
executes a module once per process and caches it, so these three files are read
a single time no matter how many tool calls a run makes. Every layer above
imports an already-materialised dict and never touches the filesystem, which is
what keeps `tools/` pure and unit-testable without mocks.

A malformed or missing file raises here, at import, rather than midway through
an agent run. For baked data that is the better failure.
"""

import json
from pathlib import Path
from typing import Any

_DATA_DIR = Path(__file__).parent


def _load(filename: str, key: str) -> dict[str, Any]:
    """Read one JSON file and return the payload under `key`.

    Each file wraps its records alongside metadata such as `generation`, so the
    caller names the key it wants rather than getting the envelope.
    """
    payload = json.loads((_DATA_DIR / filename).read_text())
    return payload[key]


# Keyed by id: "garchomp", "rotom-wash". Values carry name, types, stats, moves.
POKEMON: dict[str, Any] = _load("pokemon.json", "pokemon")

# Keyed by id: "earthquake". Values carry name, type, category, power, accuracy, pp.
MOVES: dict[str, Any] = _load("moves.json", "moves")

# Keyed by id: "levitate". Values carry name and a one line effect. Abilities
# routinely override the type chart, so a matchup answer that ignores them is
# wrong for every Levitate, Flash Fire or Water Absorb holder in the dex.
ABILITIES: dict[str, Any] = _load("abilities.json", "abilities")

def _invert(chart: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    """Flip attacker->defender into defender->attacker.

    Answering "what is Steel weak to" against the attacking chart means scanning
    every row looking for a `steel` key. Inverting once here makes it a direct
    lookup, without storing the same matchups twice where the copies could drift.
    """
    inverted: dict[str, dict[str, float]] = {type_name: {} for type_name in chart}
    for attacker, row in chart.items():
        for defender, multiplier in row.items():
            inverted.setdefault(defender, {})[attacker] = multiplier
    return inverted


_CHART_FILE: dict[str, Any] = json.loads((_DATA_DIR / "type-chart.json").read_text())

# The chart is generation dependent, so both of these are keyed by generation as
# a string: "1" through "9". Steel resisted Ghost and Dark until Gen 6, Fairy did
# not exist before it, and Gen 1 had its own quirks. Reading the wrong generation
# gives confidently wrong matchups rather than an error.
ATTACKING_CHARTS: dict[str, dict[str, dict[str, float]]] = _CHART_FILE["charts"]
DEFENDING_CHARTS: dict[str, dict[str, dict[str, float]]] = {
    generation: _invert(chart) for generation, chart in ATTACKING_CHARTS.items()
}

LATEST_GENERATION: str = str(_CHART_FILE["latest_generation"])

# Convenience aliases for the current generation. Anything that cares which
# generation it is answering for should index the dicts above instead.
ATTACKING_CHART: dict[str, dict[str, float]] = ATTACKING_CHARTS[LATEST_GENERATION]
DEFENDING_CHART: dict[str, dict[str, float]] = DEFENDING_CHARTS[LATEST_GENERATION]
