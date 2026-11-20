"""Remote-raid lobbies. Paid waits ahead of Free. There is no chat.

Friend codes are shown only after both trainers have opted in and the
host has accepted the seat. The app does not read a game account, sell
passes, or pay a host. MAX_JOINERS is this app's cap, not the game's.
"""

import sqlite3
from datetime import UTC, datetime
from typing import Any

from services.accounts import connect, init_db, is_admin
from services.catalog import species_by_id

MAX_JOINERS = 5
LIMIT_NOTE = "The remote-raid limit is yours to follow. This app cannot see it."
_REPORTS = {"account", "coins", "paid_hosting"}


def init_raids() -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS raids (
                id INTEGER PRIMARY KEY,
                host_id INTEGER NOT NULL REFERENCES users(id),
                species_id TEXT NOT NULL,
                city TEXT NOT NULL,
                starts_at TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (status IN ('open', 'full', 'started', 'cancelled')),
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS raid_requests (
                id INTEGER PRIMARY KEY,
                raid_id INTEGER NOT NULL REFERENCES raids(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                status TEXT NOT NULL
                    CHECK (status IN ('waiting', 'accepted')),
                created_at TEXT NOT NULL,
                UNIQUE (raid_id, user_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS raid_reports (
                id INTEGER PRIMARY KEY,
                raid_id INTEGER NOT NULL REFERENCES raids(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                reason TEXT NOT NULL
                    CHECK (reason IN ('account', 'coins', 'paid_hosting')),
                created_at TEXT NOT NULL
            )
            """
        )


def set_opt_in(user_id: int, enabled: bool) -> dict[str, Any]:
    init_raids()
    with connect() as conn:
        row = conn.execute(
            "SELECT friend_code FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None:
            raise LookupError("That account does not exist.")
        if enabled and not row["friend_code"]:
            raise ValueError("Add a friend code before opting in.")
        conn.execute(
            "UPDATE users SET raid_opt_in = ? WHERE id = ?",
            (1 if enabled else 0, user_id),
        )
    return {"raid_opt_in": enabled}


def _opted_in(conn: Any, user_id: int) -> bool:
    row = conn.execute(
        "SELECT friend_code, raid_opt_in FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    return bool(row and row["friend_code"] and row["raid_opt_in"] == 1)


def create_lobby(
    user_id: int, species_id: str, starts_at: str, city: str
) -> dict[str, Any]:
    species = species_by_id(species_id.strip().lower())
    if species is None:
        raise ValueError("Unknown species.")
    try:
        datetime.fromisoformat(starts_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Start time must be a date and time.") from exc
    init_raids()
    with connect() as conn:
        if not _opted_in(conn, user_id):
            raise ValueError("Opt in with a friend code before hosting.")
        host = conn.execute(
            "SELECT city FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        place = city.strip() or (host["city"] if host else "") or "Toronto"
        if len(place) > 64:
            raise ValueError("City names are limited to 64 characters.")
        cursor = conn.execute(
            """
            INSERT INTO raids (
                host_id, species_id, city, starts_at, status, created_at
            ) VALUES (?, ?, ?, ?, 'open', ?)
            """,
            (
                user_id,
                species.id,
                place,
                starts_at,
                datetime.now(UTC).isoformat(timespec="seconds"),
            ),
        )
        raid_id = int(cursor.lastrowid or 0)
    return lobby_view(user_id, raid_id)


def _accepted_count(conn: Any, raid_id: int) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS n FROM raid_requests
        WHERE raid_id = ? AND status = 'accepted'
        """,
        (raid_id,),
    ).fetchone()
    return int(row["n"])


def _public(conn: Any, raid: Any) -> dict[str, Any]:
    host = conn.execute(
        "SELECT trainer_name FROM users WHERE id = ?", (raid["host_id"],)
    ).fetchone()
    species = species_by_id(raid["species_id"])
    return {
        "id": raid["id"],
        "species_id": raid["species_id"],
        "species_name": species.name if species else raid["species_id"],
        "city": raid["city"],
        "starts_at": raid["starts_at"],
        "status": raid["status"],
        "host_name": host["trainer_name"] if host else "",
        "seats": _accepted_count(conn, raid["id"]),
        "max_seats": MAX_JOINERS,
        "limit_note": LIMIT_NOTE,
    }


def list_lobbies() -> list[dict[str, Any]]:
    init_raids()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM raids
            WHERE status IN ('open', 'full', 'started')
            ORDER BY starts_at, id
            """
        ).fetchall()
        return [_public(conn, row) for row in rows]


def lobby_view(user_id: int, raid_id: int) -> dict[str, Any]:
    """Public fields, plus friend codes only for an accepted pair."""
    init_raids()
    with connect() as conn:
        raid = conn.execute("SELECT * FROM raids WHERE id = ?", (raid_id,)).fetchone()
        if raid is None:
            raise LookupError("That lobby does not exist.")
        view = _public(conn, raid)
        if user_id == raid["host_id"]:
            accepted = conn.execute(
                """
                SELECT users.trainer_name, users.friend_code
                FROM raid_requests
                JOIN users ON users.id = raid_requests.user_id
                WHERE raid_requests.raid_id = ? AND raid_requests.status = 'accepted'
                ORDER BY raid_requests.id
                """,
                (raid_id,),
            ).fetchall()
            view["party"] = [
                {"trainer_name": row["trainer_name"], "friend_code": row["friend_code"]}
                for row in accepted
            ]
            return view
        mine = conn.execute(
            """
            SELECT status FROM raid_requests
            WHERE raid_id = ? AND user_id = ?
            """,
            (raid_id, user_id),
        ).fetchone()
        if mine is not None and mine["status"] == "accepted":
            host = conn.execute(
                "SELECT trainer_name, friend_code FROM users WHERE id = ?",
                (raid["host_id"],),
            ).fetchone()
            view["host_friend_code"] = host["friend_code"] if host else ""
    return view


def join_lobby(user_id: int, raid_id: int) -> dict[str, Any]:
    init_raids()
    with connect() as conn:
        if not _opted_in(conn, user_id):
            raise ValueError("Opt in with a friend code before joining.")
        raid = conn.execute("SELECT * FROM raids WHERE id = ?", (raid_id,)).fetchone()
        if raid is None:
            raise LookupError("That lobby does not exist.")
        if raid["host_id"] == user_id:
            raise ValueError("The host already has a seat.")
        if raid["status"] != "open":
            raise ValueError("That lobby is not open.")
        try:
            conn.execute(
                """
                INSERT INTO raid_requests (raid_id, user_id, status, created_at)
                VALUES (?, ?, 'waiting', ?)
                """,
                (
                    raid_id,
                    user_id,
                    datetime.now(UTC).isoformat(timespec="seconds"),
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("You are already in this lobby.") from exc
    return {"status": "waiting"}


def queue_for_host(user_id: int, raid_id: int) -> list[dict[str, Any]]:
    """Paid first, then whoever asked earlier. No emails and no codes."""
    init_raids()
    with connect() as conn:
        raid = conn.execute(
            "SELECT host_id FROM raids WHERE id = ?", (raid_id,)
        ).fetchone()
        if raid is None:
            raise LookupError("That lobby does not exist.")
        if raid["host_id"] != user_id:
            raise PermissionError("Only the host can see the queue.")
        rows = conn.execute(
            """
            SELECT raid_requests.user_id, raid_requests.created_at,
                   users.trainer_name, users.plan
            FROM raid_requests
            JOIN users ON users.id = raid_requests.user_id
            WHERE raid_requests.raid_id = ? AND raid_requests.status = 'waiting'
            ORDER BY CASE WHEN users.plan = 'paid' THEN 0 ELSE 1 END,
                     raid_requests.created_at, raid_requests.id
            """,
            (raid_id,),
        ).fetchall()
    return [
        {
            "user_id": row["user_id"],
            "trainer_name": row["trainer_name"],
            "raid_priority": "paid" if row["plan"] == "paid" else "free",
            "requested_at": row["created_at"],
        }
        for row in rows
    ]


def accept_joiner(host_id: int, raid_id: int, joiner_id: int) -> dict[str, Any]:
    init_raids()
    with connect() as conn:
        raid = conn.execute("SELECT * FROM raids WHERE id = ?", (raid_id,)).fetchone()
        if raid is None:
            raise LookupError("That lobby does not exist.")
        if raid["host_id"] != host_id:
            raise PermissionError("Only the host can accept a seat.")
        if raid["status"] != "open":
            raise ValueError("That lobby is not open.")
        if not _opted_in(conn, joiner_id):
            raise ValueError("That trainer has not opted in.")
        request = conn.execute(
            """
            SELECT id FROM raid_requests
            WHERE raid_id = ? AND user_id = ? AND status = 'waiting'
            """,
            (raid_id, joiner_id),
        ).fetchone()
        if request is None:
            raise LookupError("That trainer is not waiting.")
        if _accepted_count(conn, raid_id) >= MAX_JOINERS:
            raise ValueError("That lobby is full.")
        conn.execute(
            "UPDATE raid_requests SET status = 'accepted' WHERE id = ?",
            (request["id"],),
        )
        if _accepted_count(conn, raid_id) >= MAX_JOINERS:
            conn.execute("UPDATE raids SET status = 'full' WHERE id = ?", (raid_id,))
        joiner = conn.execute(
            "SELECT trainer_name, friend_code FROM users WHERE id = ?",
            (joiner_id,),
        ).fetchone()
    return {
        "trainer_name": joiner["trainer_name"],
        "friend_code": joiner["friend_code"],
    }


def set_status(user_id: int, raid_id: int, status: str) -> dict[str, Any]:
    if status not in {"started", "cancelled"}:
        raise ValueError("Choose started or cancelled.")
    init_raids()
    with connect() as conn:
        raid = conn.execute("SELECT * FROM raids WHERE id = ?", (raid_id,)).fetchone()
        if raid is None:
            raise LookupError("That lobby does not exist.")
        host = raid["host_id"] == user_id
        if not host and not _email_is_admin(conn, user_id):
            raise PermissionError("Only the host can change this lobby.")
        if raid["status"] == "cancelled":
            raise ValueError("That lobby is already cancelled.")
        conn.execute("UPDATE raids SET status = ? WHERE id = ?", (status, raid_id))
    return lobby_view(user_id, raid_id)


def _email_is_admin(conn: Any, user_id: int) -> bool:
    row = conn.execute("SELECT email FROM users WHERE id = ?", (user_id,)).fetchone()
    return bool(row and is_admin(row["email"]))


def report_lobby(user_id: int, raid_id: int, reason: str) -> dict[str, Any]:
    if reason not in _REPORTS:
        raise ValueError("Choose account, coins, or paid hosting.")
    init_raids()
    with connect() as conn:
        raid = conn.execute("SELECT id FROM raids WHERE id = ?", (raid_id,)).fetchone()
        if raid is None:
            raise LookupError("That lobby does not exist.")
        cursor = conn.execute(
            """
            INSERT INTO raid_reports (raid_id, user_id, reason, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                raid_id,
                user_id,
                reason,
                datetime.now(UTC).isoformat(timespec="seconds"),
            ),
        )
    return {"id": cursor.lastrowid, "reason": reason}


def list_reports(email: str) -> list[dict[str, Any]]:
    if not is_admin(email):
        raise PermissionError("Raid reports are reviewed by admin accounts.")
    init_raids()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT raid_reports.id, raid_reports.raid_id, raid_reports.reason,
                   raid_reports.created_at, raids.species_id, raids.status
            FROM raid_reports
            JOIN raids ON raids.id = raid_reports.raid_id
            ORDER BY raid_reports.id
            """
        ).fetchall()
    return [dict(row) for row in rows]
