"""Friendship notes for a list row. Pure: no database and no network.

In-person special trades need Good Friends. Remote trades need Forever
Friends. Shadow Pokémon cannot be traded remotely. Mythicals that cannot
be traded are rejected before this runs.
"""

from typing import Any


def trade_notes(species: Any, shiny: bool, shadow: bool) -> list[str]:
    notes: list[str] = []
    if shiny or species.legendary:
        notes.append(
            "An in-person trade of a shiny or Legendary is a Special Trade "
            "and needs Good Friends."
        )
    notes.append("A remote trade needs Forever Friends.")
    if shadow:
        notes.append("Shadow Pokémon cannot be traded remotely.")
    return notes
