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


def _keeps(
    row: dict[str, Any],
    species_id: str,
    form: str,
    flags: dict[str, bool],
    background: str = "",
) -> bool:
    if species_id and row["species_id"] != species_id:
        return False
    if form and row["form"] != form:
        return False
    if background and row.get("background") != background:
        return False
    for name, selected in flags.items():
        if selected and not row.get(name):
            return False
    return True


def search_trades(
    user_id: int,
    city: str,
    species_id: str = "",
    form: str = "",
    flags: dict[str, bool] | None = None,
    background: str = "",
) -> list[dict[str, Any]]:
    init_lists()
    needle = city.strip().lower()
    everyone = needle in {"", "all"}
    selected = flags or {}
    wanted_form = form.strip().lower()
    wanted_background = background.strip().lower()
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
        they_have = [
            row
            for row in overlap["they_have"]
            if _keeps(row, species_id, wanted_form, selected, wanted_background)
        ]
        i_have = [
            row
            for row in overlap["i_have"]
            if _keeps(row, species_id, wanted_form, selected, wanted_background)
        ]
        if not they_have and not i_have:
            continue
        matches.append(
            {
                "trainer_name": user["trainer_name"],
                "city": user["city"],
                "they_have": they_have,
                "i_have": i_have,
            }
        )
    matches.sort(key=lambda row: (row["city"], row["trainer_name"]))
    return matches
