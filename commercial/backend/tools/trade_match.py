"""Plain list matching. A true flag on a want is required on the have.

A false flag means the want does not care. Form must match, and a blank form
is the base form. This module does not call a model.
"""

from collections.abc import Mapping
from typing import Any

_FLAGS = (
    "shiny",
    "dynamax",
    "gigantamax",
    "shadow",
    "purified",
    "lucky",
    "costume",
)


def satisfies(want: Mapping[str, Any], have: Mapping[str, Any]) -> bool:
    if want["species_id"] != have["species_id"]:
        return False
    if (want.get("form") or "") != (have.get("form") or ""):
        return False
    return all(not want.get(flag) or have.get(flag) for flag in _FLAGS)


def pair_matches(
    mine: list[Mapping[str, Any]], theirs: list[Mapping[str, Any]]
) -> dict[str, list[Mapping[str, Any]]]:
    my_wants = [row for row in mine if row["kind"] == "want"]
    my_haves = [row for row in mine if row["kind"] == "have"]
    their_wants = [row for row in theirs if row["kind"] == "want"]
    their_haves = [row for row in theirs if row["kind"] == "have"]
    they_have = [
        row for row in their_haves if any(satisfies(want, row) for want in my_wants)
    ]
    i_have = [
        row for row in my_haves if any(satisfies(want, row) for want in their_wants)
    ]
    return {"they_have": they_have, "i_have": i_have}
