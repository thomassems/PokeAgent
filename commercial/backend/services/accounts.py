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
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

_COOKIE = "trainermon_session"
_SESSION_DAYS = 14
_HASH_ROUNDS = 120_000


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
                created_at TEXT NOT NULL
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


def public_user(row: sqlite3.Row) -> dict[str, Any]:
    """Owner profile. friend_code is included because this is their own row."""
    return {
        "id": row["id"],
        "email": row["email"],
        "trainer_name": row["trainer_name"],
        "city": row["city"],
        "friend_code": row["friend_code"] or "",
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
    cleaned = (city or "").strip() or "Toronto"
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


def register(
    email: str,
    password: str,
    trainer_name: str,
    city: str | None,
    friend_code: str | None,
) -> tuple[dict[str, Any], str]:
    cleaned_email = _validate_email(email)
    _validate_password(password)
    name = _validate_name(trainer_name)
    place = _validate_city(city)
    code = _validate_friend_code(friend_code)
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
                email, password_hash, trainer_name, city, friend_code, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                cleaned_email,
                _hash_password(password),
                name,
                place,
                code,
                _iso(_now()),
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


def update_profile(
    user_id: int, trainer_name: str, city: str, friend_code: str | None
) -> dict[str, Any]:
    name = _validate_name(trainer_name)
    place = _validate_city(city)
    code = _validate_friend_code(friend_code)
    init_db()
    with connect() as conn:
        conn.execute(
            """
            UPDATE users SET trainer_name = ?, city = ?, friend_code = ? WHERE id = ?
            """,
            (name, place, code, user_id),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return public_user(row)
