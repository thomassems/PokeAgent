"""Curated GO facts. Drafts stay hidden until an admin approves them.

The app does not fetch the source URL. A human pastes the announcement,
and the model may only use that paste.
"""

import json
import os
from pathlib import Path
from typing import Any

from data.go_catalog import base_catalog
from services.accounts import connect, init_db, is_admin

_SEED = Path(__file__).resolve().parents[1] / "data" / "go_curated_seed.json"
_KINDS = {
    "shiny",
    "dynamax",
    "gigantamax",
    "costume",
    "trade_rule",
    "background",
    "dynamax_costume",
    "gigantamax_costume",
}


def init_curation() -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS curated_facts (
                id INTEGER PRIMARY KEY,
                species_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                value TEXT NOT NULL,
                source_url TEXT NOT NULL,
                verified_at TEXT NOT NULL,
                verified_by TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (status IN ('draft', 'approved', 'rejected')),
                notes TEXT NOT NULL DEFAULT '',
                UNIQUE (species_id, kind, value, source_url)
            )
            """
        )
        existing = {
            (row["species_id"], row["kind"], row["value"], row["source_url"])
            for row in conn.execute(
                "SELECT species_id, kind, value, source_url FROM curated_facts"
            )
        }
        for row in json.loads(_SEED.read_text())["rows"]:
            key = (row["species_id"], row["kind"], row["value"], row["source_url"])
            if key in existing:
                continue
            conn.execute(
                """
                INSERT INTO curated_facts (
                    species_id, kind, value, source_url, verified_at,
                    verified_by, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, 'approved', ?)
                """,
                (
                    row["species_id"],
                    row["kind"],
                    row["value"],
                    row["source_url"],
                    row["verified_at"],
                    row["verified_by"],
                    row["notes"],
                ),
            )


def approved_facts() -> list[dict[str, Any]]:
    init_curation()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM curated_facts
            WHERE status = 'approved'
            ORDER BY id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def list_facts() -> list[dict[str, Any]]:
    init_curation()
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM curated_facts ORDER BY status, id"
        ).fetchall()
    return [dict(row) for row in rows]


def _require_admin(email: str) -> None:
    if not is_admin(email):
        raise PermissionError("Curation is limited to admin accounts.")


def _check_source(source_url: str, verified_at: str) -> tuple[str, str]:
    url = source_url.strip()
    if not url.startswith("https://") or len(url) > 300:
        raise ValueError("Add an https source link.")
    day = verified_at.strip()
    parts = day.split("-")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError("Verified date must look like 2026-11-18.")
    if len(parts[0]) != 4 or len(parts[1]) != 2 or len(parts[2]) != 2:
        raise ValueError("Verified date must look like 2026-11-18.")
    return url, day


def _species_id(name: str) -> str:
    needle = name.strip().lower()
    matches = [
        item.id
        for item in base_catalog()
        if item.name.lower() == needle or item.id == needle.replace(" ", "-")
    ]
    if len(matches) != 1:
        raise ValueError(f"Unknown species '{name}'.")
    return matches[0]


def parse_drafts(text: str) -> list[dict[str, str]]:
    """Pull a JSON array out of a model reply. No network."""
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
        raw = raw.rsplit("```", 1)[0]
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("The draft was not a JSON list.")
    payload = json.loads(raw[start : end + 1])
    if not isinstance(payload, list):
        raise ValueError("The draft was not a JSON list.")
    drafts: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "")
        if kind not in _KINDS:
            continue
        value = str(item.get("value") or "").strip()
        if kind in {
            "shiny",
            "dynamax",
            "gigantamax",
            "dynamax_costume",
            "gigantamax_costume",
        }:
            value = "true"
        if kind == "trade_rule":
            value = "untradable"
        if kind == "background":
            value = value.lower().replace(" ", "-")
            if not value.replace("-", "").isalnum():
                continue
        if not value:
            continue
        raw_name = item.get("species_name") or item.get("species_id") or ""
        species = _species_id(str(raw_name))
        drafts.append({"species_id": species, "kind": kind, "value": value})
    if not drafts:
        raise ValueError("No catalog rows could be drafted from that paste.")
    return drafts


def draft_prompt(pasted: str) -> str:
    return (
        "You draft Pokémon GO catalog rows from the pasted announcement only. "
        "Do not add species the paste does not name. Reply with a JSON array "
        "and nothing else. Each item has species_name, kind, and value. "
        "kind is one of shiny, dynamax, gigantamax, costume, trade_rule, "
        "background, dynamax_costume, gigantamax_costume. "
        "For shiny, dynamax, gigantamax, dynamax_costume, and "
        "gigantamax_costume, value is true. "
        "dynamax_costume means the paste released that costume on the "
        "Dynamax form. A Dynamax mention alone is dynamax, not a costume. "
        "For costume, value is a short form name such as scarf. "
        "For background, value is a short slug such as dynamax-trails. "
        "For trade_rule, value is untradable.\n\n"
        f"{pasted.strip()}"
    )


def complete_draft(prompt: str) -> str:
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        raise RuntimeError("Drafting needs ANTHROPIC_API_KEY on the server.")
    import anthropic

    client = anthropic.Anthropic()
    model = os.environ.get("TRAINERMON_DRAFT_MODEL", "deepseek-v4-flash")
    message = client.messages.create(
        model=model,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    block = message.content[0]
    text = getattr(block, "text", "")
    if not text:
        raise RuntimeError("The draft model returned no text.")
    return text


def save_drafts(
    email: str,
    pasted: str,
    source_url: str,
    verified_at: str,
    completer: Any = None,
) -> list[dict[str, Any]]:
    _require_admin(email)
    url, day = _check_source(source_url, verified_at)
    if len(pasted.strip()) < 20:
        raise ValueError("Paste the announcement text first.")
    complete = completer or complete_draft
    parsed = parse_drafts(complete(draft_prompt(pasted)))
    init_curation()
    saved: list[dict[str, Any]] = []
    with connect() as conn:
        for item in parsed:
            conn.execute(
                """
                INSERT OR IGNORE INTO curated_facts (
                    species_id, kind, value, source_url, verified_at,
                    verified_by, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, 'draft', '')
                """,
                (item["species_id"], item["kind"], item["value"], url, day, email),
            )
            row = conn.execute(
                """
                SELECT * FROM curated_facts
                WHERE species_id = ? AND kind = ? AND value = ? AND source_url = ?
                """,
                (item["species_id"], item["kind"], item["value"], url),
            ).fetchone()
            if row is not None:
                saved.append(dict(row))
    return saved


def set_status(email: str, fact_id: int, status: str) -> dict[str, Any]:
    _require_admin(email)
    if status not in {"approved", "rejected"}:
        raise ValueError("Choose approved or rejected.")
    init_curation()
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM curated_facts WHERE id = ?", (fact_id,)
        ).fetchone()
        if row is None:
            raise LookupError("That curated row does not exist.")
        if not row["source_url"] or not row["verified_at"]:
            raise ValueError("A row needs a source link and a verified date.")
        verified_by = row["verified_by"]
        if status == "approved":
            verified_by = email
        conn.execute(
            """
            UPDATE curated_facts
            SET status = ?, verified_by = ?
            WHERE id = ?
            """,
            (status, verified_by, fact_id),
        )
        updated = conn.execute(
            "SELECT * FROM curated_facts WHERE id = ?", (fact_id,)
        ).fetchone()
    return dict(updated)
