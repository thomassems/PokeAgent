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

def _invert(chart: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    """Flip attacker->defender into defender->attacker.

    Answering "what is Steel weak to" against the attacking chart means scanning
    all eighteen rows looking for a `steel` key. Inverting once here makes it a
    direct lookup, without storing the same matchups in a second file where the
    two copies could drift apart.
    """
    inverted: dict[str, dict[str, float]] = {type_name: {} for type_name in chart}
    for attacker, row in chart.items():
        for defender, multiplier in row.items():
            inverted.setdefault(defender, {})[attacker] = multiplier
    return inverted


# Attacker keyed to defender: ATTACKING_CHART["fire"]["steel"] is 2.
# Absent pairs are neutral, so lookups default to 1.0 rather than assume the key
# exists. Note 0 is a real value (immunity), so it is not safe to treat as falsy.
ATTACKING_CHART: dict[str, dict[str, float]] = _load("type-chart.json", "chart")

# The same matchups read the other way: DEFENDING_CHART["steel"]["fire"] is 2.
# Derived, never edited. type-chart.json stays the single source of truth.
DEFENDING_CHART: dict[str, dict[str, float]] = _invert(ATTACKING_CHART)

# Which generation's rules these files encode. Type charts and typings both
# differ by generation, so anything deriving from them should say which it used.
GENERATION: str = json.loads((_DATA_DIR / "type-chart.json").read_text())["generation"]
