"""Want and have lists. Rows are what the trainer typed. No game account."""

import sqlite3
from typing import Any

from data.go_catalog import EntryFlags, check_entry
from services.accounts import connect, init_db
from services.catalog import species_by_id
from tools.trade_rules import trade_notes


def init_lists() -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS list_entries (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                kind TEXT NOT NULL CHECK (kind IN ('want', 'have')),
                species_id TEXT NOT NULL,
                form TEXT NOT NULL DEFAULT '',
                shiny INTEGER NOT NULL,
                dynamax INTEGER NOT NULL,
                gigantamax INTEGER NOT NULL,
                shadow INTEGER NOT NULL,
                purified INTEGER NOT NULL,
                lucky INTEGER NOT NULL,
                costume INTEGER NOT NULL,
                notes TEXT NOT NULL DEFAULT ''
            )
            """
        )


def _flags(row: sqlite3.Row | dict[str, Any]) -> EntryFlags:
    return EntryFlags(
        form=row["form"],
        shiny=bool(row["shiny"]),
        dynamax=bool(row["dynamax"]),
        gigantamax=bool(row["gigantamax"]),
        shadow=bool(row["shadow"]),
        purified=bool(row["purified"]),
        lucky=bool(row["lucky"]),
        costume=bool(row["costume"]),
        notes=row["notes"],
    )


def _public(row: sqlite3.Row) -> dict[str, Any]:
    species = species_by_id(row["species_id"])
    if species is None:
        raise ValueError(f"Unknown species '{row['species_id']}'.")
    flags = _flags(row)
    return {
        "id": row["id"],
        "kind": row["kind"],
        "species_id": species.id,
        "dex": species.dex,
        "name": species.name,
        "types": species.types,
        "form": flags.form,
        "shiny": flags.shiny,
        "dynamax": flags.dynamax,
        "gigantamax": flags.gigantamax,
        "shadow": flags.shadow,
        "purified": flags.purified,
        "lucky": flags.lucky,
        "costume": flags.costume,
        "notes": flags.notes,
        "trade_notes": trade_notes(species, flags.shiny, flags.shadow),
    }


def list_entries(user_id: int) -> list[dict[str, Any]]:
    init_lists()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM list_entries WHERE user_id = ? ORDER BY id",
            (user_id,),
        ).fetchall()
    return [_public(row) for row in rows]


def add_entry(
    user_id: int, kind: str, flags: EntryFlags, species_id: str
) -> dict[str, Any]:
    if kind not in {"want", "have"}:
        raise ValueError("A list is either want or have.")
    species = species_by_id(species_id)
    if species is None:
        raise ValueError(f"Unknown species '{species_id}'.")
    check_entry(species, flags)
    init_lists()
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO list_entries (
                user_id, kind, species_id, form, shiny, dynamax, gigantamax,
                shadow, purified, lucky, costume, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                kind,
                species.id,
                flags.form.strip().lower(),
                int(flags.shiny),
                int(flags.dynamax),
                int(flags.gigantamax),
                int(flags.shadow),
                int(flags.purified),
                int(flags.lucky),
                int(flags.costume),
                flags.notes.strip(),
            ),
        )
        row = conn.execute(
            "SELECT * FROM list_entries WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return _public(row)


def update_entry(user_id: int, entry_id: int, flags: EntryFlags) -> dict[str, Any]:
    init_lists()
    with connect() as conn:
        current = conn.execute(
            "SELECT * FROM list_entries WHERE id = ? AND user_id = ?",
            (entry_id, user_id),
        ).fetchone()
        if current is None:
            raise LookupError("That list entry is not yours.")
        species = species_by_id(current["species_id"])
        if species is None:
            raise ValueError(f"Unknown species '{current['species_id']}'.")
        check_entry(species, flags)
        conn.execute(
            """
            UPDATE list_entries SET
                form = ?, shiny = ?, dynamax = ?, gigantamax = ?, shadow = ?,
                purified = ?, lucky = ?, costume = ?, notes = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                flags.form.strip().lower(),
                int(flags.shiny),
                int(flags.dynamax),
                int(flags.gigantamax),
                int(flags.shadow),
                int(flags.purified),
                int(flags.lucky),
                int(flags.costume),
                flags.notes.strip(),
                entry_id,
                user_id,
            ),
        )
        row = conn.execute(
            "SELECT * FROM list_entries WHERE id = ?", (entry_id,)
        ).fetchone()
    return _public(row)


def delete_entry(user_id: int, entry_id: int) -> None:
    init_lists()
    with connect() as conn:
        cursor = conn.execute(
            "DELETE FROM list_entries WHERE id = ? AND user_id = ?",
            (entry_id, user_id),
        )
        if cursor.rowcount == 0:
            raise LookupError("That list entry is not yours.")
