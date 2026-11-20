"""Curated GO facts. Drafts stay hidden until an admin approves them.

The app does not fetch the source URL. A human pastes the announcement,
and the model may only use that paste.
"""

import json
import os
from pathlib import Path
from typing import Any

from data.go_catalog import base_catalog, variant_label
from services.accounts import connect, init_db, is_admin

_CREATE_FACTS = """
CREATE TABLE curated_facts (
    id INTEGER PRIMARY KEY,
    species_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    value TEXT NOT NULL,
    source_url TEXT NOT NULL,
    verified_at TEXT NOT NULL,
    verified_by TEXT NOT NULL,
    status TEXT NOT NULL
        CHECK (status IN ('draft', 'approved', 'rejected', 'merged')),
    notes TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL DEFAULT 'official'
        CHECK (source_type IN ('official', 'community')),
    community_source_url TEXT NOT NULL DEFAULT '',
    community_aliases TEXT NOT NULL DEFAULT '',
    merged_into TEXT NOT NULL DEFAULT '',
    UNIQUE (species_id, kind, value, source_url)
)
"""
_KIND_LABELS = {
    "shiny": "Shiny",
    "dynamax": "Dynamax",
    "gigantamax": "Gigantamax",
    "costume": "Costume",
    "trade_rule": "Trade rule",
    "background": "Background",
    "dynamax_costume": "Dynamax costume",
    "gigantamax_costume": "Gigantamax costume",
    "costume_shiny": "Shiny costume",
    "background_shiny": "Shiny background",
}

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
    "costume_shiny",
    "background_shiny",
}


def init_curation() -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            _CREATE_FACTS.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1)
        )
        _ensure_fact_shape(conn)
        existing = {
            (row["species_id"], row["kind"], row["value"], row["source_url"])
            for row in conn.execute(
                "SELECT species_id, kind, value, source_url FROM curated_facts"
            )
        }
        for row in json.loads(_SEED.read_text())["rows"]:
            key = (row["species_id"], row["kind"], row["value"], row["source_url"])
            community_source = str(row.get("community_source_url") or "")
            aliases = _alias_text(row)
            merged_into = str(row.get("merged_into") or "")
            if key in existing:
                # A later import may attach a community URL or an alias.
                # It does not change an approved row's status or its notes.
                if community_source:
                    conn.execute(
                        """
                        UPDATE curated_facts
                        SET community_source_url = ?
                        WHERE species_id = ? AND kind = ? AND value = ?
                          AND source_url = ? AND community_source_url = ''
                        """,
                        (community_source, *key),
                    )
                if aliases:
                    conn.execute(
                        """
                        UPDATE curated_facts
                        SET community_aliases = ?
                        WHERE species_id = ? AND kind = ? AND value = ?
                          AND source_url = ? AND community_aliases = ''
                        """,
                        (aliases, *key),
                    )
                if merged_into:
                    conn.execute(
                        """
                        UPDATE curated_facts
                        SET status = 'merged', merged_into = ?
                        WHERE species_id = ? AND kind = ? AND value = ?
                          AND source_url = ? AND status = 'draft'
                        """,
                        (merged_into, *key),
                    )
                continue
            conn.execute(
                """
                INSERT INTO curated_facts (
                    species_id, kind, value, source_url, verified_at,
                    verified_by, status, notes, source_type,
                    community_source_url, community_aliases, merged_into
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["species_id"],
                    row["kind"],
                    row["value"],
                    row["source_url"],
                    row["verified_at"],
                    row["verified_by"],
                    _seed_status(row),
                    row["notes"],
                    _source_type(row),
                    community_source,
                    aliases,
                    merged_into,
                ),
            )


def _fact_columns(conn: Any) -> set[str]:
    return {row[1] for row in conn.execute("PRAGMA table_info(curated_facts)")}


def _ensure_fact_shape(conn: Any) -> None:
    """Add alias columns, and rebuild when status cannot be merged.

    SQLite will not change a CHECK constraint in place. A database created
    before merged aliases is copied into a table that allows that status.
    """
    sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'curated_facts'"
    ).fetchone()
    if sql is None or "'merged'" not in (sql[0] or ""):
        _rebuild_facts(conn)
        return
    columns = _fact_columns(conn)
    if "community_aliases" not in columns:
        conn.execute(
            """
            ALTER TABLE curated_facts
            ADD COLUMN community_aliases TEXT NOT NULL DEFAULT ''
            """
        )
    if "merged_into" not in columns:
        conn.execute(
            """
            ALTER TABLE curated_facts
            ADD COLUMN merged_into TEXT NOT NULL DEFAULT ''
            """
        )


def _rebuild_facts(conn: Any) -> None:
    columns = _fact_columns(conn)
    conn.execute("ALTER TABLE curated_facts RENAME TO curated_facts_old")
    conn.execute(_CREATE_FACTS)

    def column(name: str, default: str) -> str:
        if name in columns:
            return name
        return default

    conn.execute(
        f"""
        INSERT INTO curated_facts (
            id, species_id, kind, value, source_url, verified_at, verified_by,
            status, notes, source_type, community_source_url, community_aliases,
            merged_into
        )
        SELECT
            id, species_id, kind, value, source_url, verified_at, verified_by,
            status, notes,
            {column("source_type", "'official'")},
            {column("community_source_url", "''")},
            {column("community_aliases", "''")},
            {column("merged_into", "''")}
        FROM curated_facts_old
        """
    )
    conn.execute("DROP TABLE curated_facts_old")


def _alias_text(row: dict[str, Any]) -> str:
    raw = row.get("community_aliases") or ""
    if isinstance(raw, list):
        parts = [str(item).strip() for item in raw if str(item).strip()]
    else:
        parts = [part.strip() for part in str(raw).split(",") if part.strip()]
    return ",".join(parts)


def _source_type(row: dict[str, Any]) -> str:
    source_type = str(row.get("source_type") or "official")
    if source_type not in {"official", "community"}:
        raise ValueError(
            f"Source type must be official or community, not {source_type}."
        )
    return source_type


def _seed_status(row: dict[str, Any]) -> str:
    """Older seed rows omit status and stay approved.

    Rows added after the Pikachu slice set status to draft. Thomas approves
    those on /curate. The loader does not promote a draft on its own.
    A merged row is a community duplicate of an official costume.
    """
    status = str(row.get("status") or "approved")
    if status not in {"draft", "approved", "merged"}:
        raise ValueError(
            f"Seed status must be draft, approved, or merged, not {status}."
        )
    return status


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
    names = {item.id: item.name for item in base_catalog()}
    with connect() as conn:
        rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT * FROM curated_facts
                ORDER BY status, species_id, kind, value
                """
            )
        ]
    confirmed = _confirmed_shiny(rows)
    for row in rows:
        row["label"] = variant_label(str(row["kind"]), str(row["value"]))
        row["species_name"] = names.get(row["species_id"], row["species_id"])
        row["kind_label"] = _KIND_LABELS.get(str(row["kind"]), str(row["kind"]))
        row["aliases"] = [
            part for part in str(row.get("community_aliases") or "").split(",") if part
        ]
        row["shiny"] = _shiny_label(row, confirmed)
    return rows


def _confirmed_shiny(rows: list[dict[str, Any]]) -> set[tuple[str, str, str]]:
    """Species, costume or background, and value where a source row says shiny.

    Rejected and merged rows do not confirm a shiny release. A draft shiny
    row still counts: the source said so, and approval is a separate step.
    """
    base = {"costume_shiny": "costume", "background_shiny": "background"}
    found: set[tuple[str, str, str]] = set()
    for row in rows:
        kind = base.get(str(row["kind"]))
        if kind is None or row["status"] in {"rejected", "merged"}:
            continue
        found.add((str(row["species_id"]), kind, str(row["value"])))
    return found


def _shiny_label(
    row: dict[str, Any], confirmed: set[tuple[str, str, str]]
) -> str | None:
    kind = str(row["kind"])
    if kind in {"costume", "background"}:
        key = (str(row["species_id"]), kind, str(row["value"]))
        return "confirmed" if key in confirmed else "unknown"
    if kind in {"costume_shiny", "background_shiny", "shiny"}:
        if row["status"] in {"rejected", "merged"}:
            return "unknown"
        return "confirmed"
    return None


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
        if kind in {"background", "costume", "costume_shiny", "background_shiny"}:
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
        "background, dynamax_costume, gigantamax_costume, costume_shiny, "
        "background_shiny. "
        "For shiny, dynamax, gigantamax, dynamax_costume, and "
        "gigantamax_costume, value is true. "
        "dynamax_costume means the paste released that costume on the "
        "Dynamax form. A Dynamax mention alone is dynamax, not a costume. "
        "For costume, value is a short form name such as scarf. "
        "costume_shiny means that costume can be shiny. Its value is the "
        "costume slug. "
        "For background, value is a short slug such as dynamax-trails. "
        "background_shiny means that background encounter can be shiny. "
        "Its value is the background slug. "
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
    updated = set_statuses(email, [fact_id], status)
    return updated[0]


def set_statuses(email: str, fact_ids: list[int], status: str) -> list[dict[str, Any]]:
    """Approve or reject every id. One failure rolls the whole batch back.

    Approval records the admin email in verified_by, the same field a single
    approval writes. Rejection leaves verified_by as it was. A merged alias
    cannot be approved on its own, or the costume would exist twice.
    """
    _require_admin(email)
    if status not in {"approved", "rejected"}:
        raise ValueError("Choose approved or rejected.")
    if not fact_ids:
        raise ValueError("Select at least one row.")
    init_curation()
    updated: list[dict[str, Any]] = []
    with connect() as conn:
        for fact_id in fact_ids:
            row = conn.execute(
                "SELECT * FROM curated_facts WHERE id = ?", (fact_id,)
            ).fetchone()
            if row is None:
                raise LookupError("That curated row does not exist.")
            if row["status"] == "merged" or row["merged_into"]:
                raise ValueError("That community code is an alias of an official row.")
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
            fresh = conn.execute(
                "SELECT * FROM curated_facts WHERE id = ?", (fact_id,)
            ).fetchone()
            updated.append(dict(fresh))
    return updated
