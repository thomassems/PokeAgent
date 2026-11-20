"""Local accounts. SQLite, so tests and dev need no hosted database.

Friend codes are stored for the owner. Other people do not receive them.
SHARE_FRIEND_CODES is reserved for a contact method Thomas has not chosen.
It defaults off, and no route reads it to publish a code.
"""

import hashlib
import hmac
import os
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_COOKIE = "trainermon_session"
_SESSION_DAYS = 14
_HASH_ROUNDS = 120_000
_LEVEL_MIN = 1
_LEVEL_MAX = 80

# One list, not a setting. The browser sends an IANA zone. The trainer never
# picks it. Region is a coarse label stored beside that zone.
TEAMS: dict[str, str] = {
    "mystic": "Mystic",
    "valor": "Valor",
    "instinct": "Instinct",
}
_REGION_PREFIXES: tuple[tuple[str, str], ...] = (
    ("America/", "Americas"),
    ("Europe/", "Europe"),
    ("Africa/", "Africa"),
    ("Asia/", "Asia"),
    ("Australia/", "Oceania"),
    ("Pacific/", "Oceania"),
    ("Atlantic/", "Atlantic"),
    ("Indian/", "Indian Ocean"),
    ("Antarctica/", "Antarctica"),
    ("UTC", "UTC"),
)


@dataclass(frozen=True)
class TrainerDetails:
    trainer_name: str
    city: str | None
    friend_code: str | None
    trainer_level: int
    team: str
    timezone: str


def cookie_name() -> str:
    return _COOKIE


def db_path() -> Path:
    raw = os.environ.get("TRAINERMON_DB", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parents[1] / "data" / "local.db"


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                trainer_name TEXT NOT NULL,
                city TEXT NOT NULL,
                friend_code TEXT,
                created_at TEXT NOT NULL,
                age_ok INTEGER,
                trainer_level INTEGER,
                team TEXT,
                timezone TEXT,
                region TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                expires_at TEXT NOT NULL
            )
            """
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        # Databases created before these columns existed still need them.
        additions = {
            "age_ok": "ALTER TABLE users ADD COLUMN age_ok INTEGER",
            "trainer_level": "ALTER TABLE users ADD COLUMN trainer_level INTEGER",
            "team": "ALTER TABLE users ADD COLUMN team TEXT",
            "timezone": "ALTER TABLE users ADD COLUMN timezone TEXT",
            "region": "ALTER TABLE users ADD COLUMN region TEXT",
            "plan": "ALTER TABLE users ADD COLUMN plan TEXT",
            "lemon_subscription_id": (
                "ALTER TABLE users ADD COLUMN lemon_subscription_id TEXT"
            ),
            "lemon_status": "ALTER TABLE users ADD COLUMN lemon_status TEXT",
            "lemon_portal_url": "ALTER TABLE users ADD COLUMN lemon_portal_url TEXT",
            "raid_opt_in": "ALTER TABLE users ADD COLUMN raid_opt_in INTEGER",
        }
        for name, statement in additions.items():
            if name not in columns:
                conn.execute(statement)


def is_admin(email: str) -> bool:
    """TRAINERMON_ADMINS is a comma-separated list of account emails."""
    allowed = {
        item.strip().lower()
        for item in os.environ.get("TRAINERMON_ADMINS", "").split(",")
        if item.strip()
    }
    return email.strip().lower() in allowed


def official_sprites_enabled() -> bool:
    """Reserved. Default off. This build has no sprite files either way."""
    return os.environ.get("SHOW_OFFICIAL_SPRITES", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def share_friend_codes() -> bool:
    """Reserved switch. Default off. Publishing a code is not implemented."""
    return os.environ.get("SHARE_FRIEND_CODES", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _HASH_ROUNDS)
    return f"{salt.hex()}${digest.hex()}"


def _password_ok(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split("$", 1)
    check = _hash_password(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(check, f"{salt_hex}${digest_hex}")


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.isoformat()


def profile_choices() -> dict[str, Any]:
    """Teams and level bounds the account form is allowed to submit."""
    return {
        "trainer_level_min": _LEVEL_MIN,
        "trainer_level_max": _LEVEL_MAX,
        "teams": [{"id": team_id, "name": name} for team_id, name in TEAMS.items()],
    }


def public_user(row: sqlite3.Row) -> dict[str, Any]:
    """Owner profile. friend_code is included because this is their own row."""
    keys = row.keys()
    level = row["trainer_level"] if "trainer_level" in keys else None
    return {
        "id": row["id"],
        "email": row["email"],
        "trainer_name": row["trainer_name"],
        "city": row["city"],
        "friend_code": row["friend_code"] or "",
        "trainer_level": level,
        "team": (row["team"] or "") if "team" in keys else "",
        "timezone": (row["timezone"] or "") if "timezone" in keys else "",
        "region": (row["region"] or "") if "region" in keys else "",
    }


def _validate_email(email: str) -> str:
    cleaned = email.strip().lower()
    if "@" not in cleaned or "." not in cleaned.split("@", 1)[1]:
        raise ValueError("Enter an email address.")
    return cleaned


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValueError("Use at least 8 characters.")


def _validate_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned or len(cleaned) > 32:
        raise ValueError("Enter a trainer name up to 32 characters.")
    return cleaned


def _validate_city(city: str | None) -> str:
    cleaned = (city or "").strip()
    if len(cleaned) > 64:
        raise ValueError("City names are limited to 64 characters.")
    return cleaned


def _validate_friend_code(code: str | None) -> str | None:
    cleaned = (code or "").strip().replace(" ", "")
    if not cleaned:
        return None
    if len(cleaned) != 12 or not cleaned.isdigit():
        raise ValueError("A friend code is 12 digits, or leave it blank.")
    return cleaned


def _validate_level(level: int) -> int:
    if isinstance(level, bool) or not isinstance(level, int):
        raise ValueError("Trainer level is a whole number from 1 to 80.")
    if level < _LEVEL_MIN or level > _LEVEL_MAX:
        raise ValueError("Trainer level is a whole number from 1 to 80.")
    return level


def _validate_team(team: str) -> str:
    cleaned = team.strip().lower()
    if cleaned not in TEAMS:
        raise ValueError("Pick a team: Mystic, Valor, or Instinct.")
    return cleaned


def _validate_timezone(timezone: str) -> tuple[str, str]:
    cleaned = timezone.strip() or "UTC"
    try:
        ZoneInfo(cleaned)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("That timezone could not be read.") from exc
    region = "UTC"
    for prefix, name in _REGION_PREFIXES:
        if cleaned == prefix or cleaned.startswith(prefix):
            region = name
            break
    return cleaned, region


def _checked_details(
    details: TrainerDetails,
) -> tuple[str, str, str | None, int, str, str, str]:
    name = _validate_name(details.trainer_name)
    place = _validate_city(details.city)
    code = _validate_friend_code(details.friend_code)
    level = _validate_level(details.trainer_level)
    team = _validate_team(details.team)
    timezone, region = _validate_timezone(details.timezone)
    return name, place, code, level, team, timezone, region


def register(
    email: str,
    password: str,
    details: TrainerDetails,
    age_confirmed: bool,
) -> tuple[dict[str, Any], str]:
    if not age_confirmed:
        raise ValueError("Trainermon is for trainers aged 13 and over.")
    cleaned_email = _validate_email(email)
    _validate_password(password)
    name, place, code, level, team, timezone, region = _checked_details(details)
    init_db()
    with connect() as conn:
        exists = conn.execute(
            "SELECT id FROM users WHERE email = ?", (cleaned_email,)
        ).fetchone()
        if exists is not None:
            raise ValueError("An account with that email already exists.")
        cursor = conn.execute(
            """
            INSERT INTO users (
                email, password_hash, trainer_name, city, friend_code,
                created_at, age_ok, trainer_level, team, timezone, region
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cleaned_email,
                _hash_password(password),
                name,
                place,
                code,
                _iso(_now()),
                1,
                level,
                team,
                timezone,
                region,
            ),
        )
        user_id = int(cursor.lastrowid)
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        token = _new_session(conn, user_id)
    return public_user(row), token


def login(email: str, password: str) -> tuple[dict[str, Any], str]:
    cleaned = email.strip().lower()
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (cleaned,)).fetchone()
        if row is None or not _password_ok(password, row["password_hash"]):
            raise PermissionError("Email or password is wrong.")
        token = _new_session(conn, int(row["id"]))
    return public_user(row), token


def _new_session(conn: sqlite3.Connection, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires = _iso(_now() + timedelta(days=_SESSION_DAYS))
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
        (token_hash, user_id, expires),
    )
    return token


def logout(token: str | None) -> None:
    if not token:
        return
    init_db()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))


def user_from_token(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    init_db()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT users.* FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ? AND sessions.expires_at > ?
            """,
            (token_hash, _iso(_now())),
        ).fetchone()
    if row is None:
        return None
    return public_user(row)


def update_profile(user_id: int, details: TrainerDetails) -> dict[str, Any]:
    """Edit the fields the trainer can see. Timezone stays as stored."""
    name = _validate_name(details.trainer_name)
    place = _validate_city(details.city)
    code = _validate_friend_code(details.friend_code)
    level = _validate_level(details.trainer_level)
    team = _validate_team(details.team)
    init_db()
    with connect() as conn:
        conn.execute(
            """
            UPDATE users SET
                trainer_name = ?, city = ?, friend_code = ?,
                trainer_level = ?, team = ?
            WHERE id = ?
            """,
            (name, place, code, level, team, user_id),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return public_user(row)
