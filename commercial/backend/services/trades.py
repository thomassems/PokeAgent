"""Find trainers whose lists overlap. No model call, no friend codes."""

from typing import Any

from services.accounts import connect
from services.lists import _public, init_lists
from tools.trade_match import pair_matches


def _rows(user_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM list_entries WHERE user_id = ? ORDER BY id",
            (user_id,),
        ).fetchall()
    return [_public(row) for row in rows]


def search_trades(user_id: int, city: str) -> list[dict[str, Any]]:
    init_lists()
    needle = city.strip().lower()
    everyone = needle in {"", "all"}
    mine = _rows(user_id)
    with connect() as conn:
        users = conn.execute(
            "SELECT id, trainer_name, city FROM users WHERE id != ?",
            (user_id,),
        ).fetchall()
    matches: list[dict[str, Any]] = []
    for user in users:
        if not everyone and user["city"].strip().lower() != needle:
            continue
        overlap = pair_matches(mine, _rows(user["id"]))
        if not overlap["they_have"] and not overlap["i_have"]:
            continue
        matches.append(
            {
                "trainer_name": user["trainer_name"],
                "city": user["city"],
                "they_have": overlap["they_have"],
                "i_have": overlap["i_have"],
            }
        )
    matches.sort(key=lambda row: (row["city"], row["trainer_name"]))
    return matches
