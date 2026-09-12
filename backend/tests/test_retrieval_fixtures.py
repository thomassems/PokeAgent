"""Asserts the dex holds what the eval fixtures claim.

This is the free half of layer 1. The same cases are replayed against a live
agent in evals/, and splitting them this way makes failures diagnosable: if this
file fails the data is wrong, and if only the eval fails the model hallucinated.
"""

from typing import Any

import pytest

from data.dex import ATTACKING_CHARTS, MOVES, POKEMON
from evals.loader import RetrievalCase, retrieval_cases

CASES = retrieval_cases()


def resolve(case: RetrievalCase) -> Any:
    """Compute the case's expected value straight from the dex."""
    check = case.check
    if check.kind == "stat":
        return POKEMON[check.pokemon]["stats"][check.stat]
    if check.kind == "typing":
        return POKEMON[check.pokemon]["types"]
    if check.kind == "move":
        return MOVES[check.move][check.field]
    # Absent pairs are neutral, so the default is 1.0 rather than a KeyError.
    row = ATTACKING_CHARTS[str(check.generation)][check.attacker]
    return row.get(check.defender, 1.0)


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_dex_matches_fixture(case: RetrievalCase) -> None:
    assert resolve(case) == case.expect


def test_every_case_has_a_unique_id() -> None:
    ids = [case.id for case in CASES]
    assert len(ids) == len(set(ids))
