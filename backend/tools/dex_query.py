"""Filtering over the baked dex.

Pure functions over `data/`, no network and no I/O of its own: the dex is
already materialised by the time this imports it. Deterministic and testable
without mocks, which is the rule this directory exists to keep.
"""

from typing import Any

from data.dex import POKEMON

# What a caller may sort by. Constrained deliberately: CLAUDE.md rules out
# free-form strings that become lookups, and an enum also stops the model
# inventing a stat name and getting an empty result it cannot explain.
SORTABLE = (
    "hp",
    "attack",
    "defense",
    "special_attack",
    "special_defense",
    "speed",
    "total",
)

MAX_LIMIT = 50


def _stat(record: dict[str, Any], key: str) -> int:
    stats = record["stats"]
    return sum(stats.values()) if key == "total" else stats[key]


def find_pokemon(
    types: list[str] | None = None,
    generation: int | None = None,
    is_legendary: bool | None = None,
    is_mythical: bool | None = None,
    sort_by: str = "total",
    limit: int = 20,
) -> dict[str, Any]:
    """Find Pokemon matching every filter given, sorted by a stat, descending.

    Filters combine with AND, and omitting one means it does not constrain.
    `types` matches a Pokemon carrying all the types listed, so ["dragon"]
    finds every Dragon and ["dragon", "ground"] finds only the duals.

    Returns names plus the sorted value, not whole records. The caller decides
    which ones are worth a full get_pokemon, rather than paying for fifty.
    """
    if sort_by not in SORTABLE:
        return {"error": f"sort_by must be one of: {', '.join(SORTABLE)}"}

    wanted = {t.strip().lower() for t in types} if types else set()
    limit = max(1, min(limit, MAX_LIMIT))

    # Aliases mean one Pokemon can appear under several ids, so dedupe by name.
    seen: set[str] = set()
    matches: list[dict[str, Any]] = []
    for record in POKEMON.values():
        if wanted and not wanted <= set(record["types"]):
            continue
        if generation is not None and record.get("generation") != generation:
            continue
        if is_legendary is not None and record.get("is_legendary") is not is_legendary:
            continue
        if is_mythical is not None and record.get("is_mythical") is not is_mythical:
            continue
        if record["name"] in seen:
            continue
        seen.add(record["name"])
        matches.append(
            {
                "name": record["name"],
                "types": record["types"],
                sort_by: _stat(record, sort_by),
            }
        )

    matches.sort(key=lambda m: m[sort_by], reverse=True)
    return {
        "count": len(matches),
        "returned": min(len(matches), limit),
        "pokemon": matches[:limit],
    }
