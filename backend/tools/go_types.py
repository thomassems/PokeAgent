"""Mega catch-candy types versus raid-counter types.

The candy bonus follows a shared type. Super effective is a different
question. This does not compute damage. Pure: the chart is local data.
"""

from typing import Any

from data.dex import DEFENDING_CHARTS, LATEST_GENERATION


def go_type_roles(types: list[str]) -> dict[str, Any]:
    """Candy-bonus types, and the types that hit this typing super effectively."""
    if not isinstance(types, list):
        return {"error": "Pass one or two types."}

    chart = DEFENDING_CHARTS[LATEST_GENERATION]
    cleaned: list[str] = []
    for raw in types:
        if not isinstance(raw, str) or not raw.strip():
            return {"error": "Each type must be a type name."}
        name = raw.strip().lower()
        if name not in chart:
            return {"error": f"Unknown type '{raw}'."}
        if name not in cleaned:
            cleaned.append(name)
    if not cleaned or len(cleaned) > 2:
        return {"error": "Pass one or two types."}

    super_effective: list[dict[str, Any]] = []
    for attack in chart:
        multiplier = 1.0
        for own in cleaned:
            multiplier *= chart[own].get(attack, 1.0)
        if multiplier > 1:
            super_effective.append({"type": attack, "multiplier": multiplier})
    super_effective.sort(key=lambda item: (-item["multiplier"], item["type"]))
    return {
        "types": cleaned,
        "candy_bonus_types": list(cleaned),
        "super_effective": super_effective,
        "chart": "latest",
    }
