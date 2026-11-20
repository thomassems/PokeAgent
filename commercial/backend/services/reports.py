"""Player reports. Confirming one opens a draft. It does not publish it.

Only an admin can confirm or reject. TRAINERMON_ADMINS is that list, and
for now it is Thomas. A report never edits Explorer by itself.
"""

from datetime import UTC, datetime
from typing import Any

from services.accounts import connect, init_db, is_admin
from services.catalog import species_by_id
from services.curation import init_curation, save_manual_draft

# Open reports a trainer may have at once. Enforced here, not in a prompt.
REPORT_OPEN_CAP = 10
_TAGS = {"wrong", "missing"}
_NOTE_MAX = 280


def init_reports() -> None:
    init_db()
    init_curation()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                species_id TEXT NOT NULL,
                tag TEXT NOT NULL CHECK (tag IN ('wrong', 'missing')),
                note TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (status IN ('open', 'confirmed', 'rejected')),
                draft_id INTEGER,
                created_at TEXT NOT NULL
            )
            """
        )


def file_report(user_id: int, species_id: str, tag: str, note: str) -> dict[str, Any]:
    init_reports()
    if tag not in _TAGS:
        raise ValueError("Choose wrong or missing.")
    text = note.strip()
    if not text or len(text) > _NOTE_MAX:
        raise ValueError("Add a short note.")
    species = species_by_id(species_id.strip().lower())
    if species is None:
        raise ValueError("Unknown species.")
    with connect() as conn:
        open_count = conn.execute(
            """
            SELECT COUNT(*) AS n FROM reports
            WHERE user_id = ? AND status = 'open'
            """,
            (user_id,),
        ).fetchone()["n"]
        if open_count >= REPORT_OPEN_CAP:
            raise ValueError("You already have 10 open reports.")
        cursor = conn.execute(
            """
            INSERT INTO reports (
                user_id, species_id, tag, note, status, created_at
            ) VALUES (?, ?, ?, ?, 'open', ?)
            """,
            (
                user_id,
                species.id,
                tag,
                text,
                datetime.now(UTC).isoformat(timespec="seconds"),
            ),
        )
        row = conn.execute(
            "SELECT * FROM reports WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return dict(row)


def list_open(email: str) -> list[dict[str, Any]]:
    if not is_admin(email):
        raise PermissionError("Reports are reviewed by admin accounts.")
    init_reports()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT reports.*, users.trainer_name
            FROM reports
            JOIN users ON users.id = reports.user_id
            WHERE reports.status = 'open'
            ORDER BY reports.id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def confirm_report(
    email: str,
    report_id: int,
    kind: str,
    value: str,
    source_url: str,
    verified_at: str,
) -> dict[str, Any]:
    """Thomas confirms by opening a draft. The public row stays unchanged."""
    if not is_admin(email):
        raise PermissionError("Reports are reviewed by admin accounts.")
    init_reports()
    with connect() as conn:
        report = conn.execute(
            "SELECT * FROM reports WHERE id = ?", (report_id,)
        ).fetchone()
    if report is None:
        raise LookupError("That report does not exist.")
    if report["status"] != "open":
        raise ValueError("That report is already closed.")
    draft = save_manual_draft(
        email,
        report["species_id"],
        kind,
        value,
        source_url,
        verified_at,
        report["note"],
    )
    with connect() as conn:
        conn.execute(
            """
            UPDATE reports
            SET status = 'confirmed', draft_id = ?
            WHERE id = ?
            """,
            (draft["id"], report_id),
        )
        updated = conn.execute(
            "SELECT * FROM reports WHERE id = ?", (report_id,)
        ).fetchone()
    result = dict(updated)
    result["draft"] = draft
    return result


def reject_report(email: str, report_id: int) -> dict[str, Any]:
    if not is_admin(email):
        raise PermissionError("Reports are reviewed by admin accounts.")
    init_reports()
    with connect() as conn:
        report = conn.execute(
            "SELECT * FROM reports WHERE id = ?", (report_id,)
        ).fetchone()
        if report is None:
            raise LookupError("That report does not exist.")
        if report["status"] != "open":
            raise ValueError("That report is already closed.")
        conn.execute(
            "UPDATE reports SET status = 'rejected' WHERE id = ?",
            (report_id,),
        )
        updated = conn.execute(
            "SELECT * FROM reports WHERE id = ?", (report_id,)
        ).fetchone()
    return dict(updated)
