"""Local accounts: register, sign in, and a friend code that stays private."""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("TRAINERMON_DB", str(tmp_path / "accounts.db"))
    monkeypatch.setenv("SHARE_FRIEND_CODES", "")
    return TestClient(app)


def test_register_login_and_profile(client: TestClient) -> None:
    created = client.post(
        "/api/auth/register",
        json={
            "email": "Avery@example.com",
            "password": "correct horse",
            "trainer_name": "Avery",
            "city": "",
            "friend_code": "1234 5678 9012",
            "trainer_level": 42,
            "team": "mystic",
            "timezone": "America/Toronto",
            "age_confirmed": True,
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert body["email"] == "avery@example.com"
    assert body["city"] == "Toronto"
    assert body["friend_code"] == "123456789012"
    assert body["trainer_level"] == 42
    assert body["team"] == "mystic"
    assert body["timezone"] == "America/Toronto"
    assert body["region"] == "Americas"
    assert "password" not in body

    me = client.get("/api/me")
    assert me.status_code == 200
    assert me.json()["trainer_name"] == "Avery"

    updated = client.patch(
        "/api/me",
        json={
            "trainer_name": "Ave",
            "city": "Toronto",
            "friend_code": "",
            "trainer_level": 43,
            "team": "valor",
            "timezone": "America/Vancouver",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["friend_code"] == ""
    assert updated.json()["trainer_level"] == 43
    assert updated.json()["team"] == "valor"
    assert updated.json()["region"] == "Americas"

    client.post("/api/auth/logout")
    assert client.get("/api/me").status_code == 401

    signed_in = client.post(
        "/api/auth/login",
        json={"email": "avery@example.com", "password": "correct horse"},
    )
    assert signed_in.status_code == 200
    assert client.get("/api/me").json()["trainer_name"] == "Ave"


def test_bad_password_and_duplicate_email(client: TestClient) -> None:
    payload = {
        "email": "sam@example.com",
        "password": "long-enough",
        "trainer_name": "Sam",
        "city": "Toronto",
        "trainer_level": 20,
        "team": "instinct",
        "timezone": "Europe/London",
        "age_confirmed": True,
    }
    assert client.post("/api/auth/register", json=payload).status_code == 200
    client.post("/api/auth/logout")
    again = client.post("/api/auth/register", json=payload)
    assert again.status_code == 400
    wrong = client.post(
        "/api/auth/login",
        json={"email": "sam@example.com", "password": "nope-nope"},
    )
    assert wrong.status_code == 401
    assert client.get("/api/me").status_code == 401


def test_friend_code_must_be_twelve_digits(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "jo@example.com",
            "password": "long-enough",
            "trainer_name": "Jo",
            "friend_code": "123",
            "trainer_level": 8,
            "team": "mystic",
            "timezone": "America/Toronto",
            "age_confirmed": True,
        },
    )
    assert response.status_code == 400
    assert "12 digits" in response.json()["detail"]


def test_under_13_cannot_register(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "kid@example.com",
            "password": "long-enough",
            "trainer_name": "Kid",
            "trainer_level": 5,
            "team": "mystic",
            "timezone": "America/Toronto",
            "age_confirmed": False,
        },
    )
    assert response.status_code == 400
    assert "13" in response.json()["detail"]


def test_level_team_and_timezone_are_checked(client: TestClient) -> None:
    base = {
        "email": "level@example.com",
        "password": "long-enough",
        "trainer_name": "Lee",
        "trainer_level": 80,
        "team": "valor",
        "timezone": "Asia/Tokyo",
        "age_confirmed": True,
    }
    assert client.post("/api/auth/register", json=base).status_code == 200
    client.post("/api/auth/logout")

    too_high = {**base, "email": "high@example.com", "trainer_level": 81}
    too_low = {**base, "email": "low@example.com", "trainer_level": 0}
    bad_team = {**base, "email": "team@example.com", "team": "rocket"}
    bad_zone = {**base, "email": "zone@example.com", "timezone": "Mars/Phobos"}
    for payload, needle in (
        (too_high, "1 to 80"),
        (too_low, "1 to 80"),
        (bad_team, "Mystic"),
        (bad_zone, "timezone"),
    ):
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 400
        assert needle in response.json()["detail"]


def test_old_database_gains_profile_columns(tmp_path, monkeypatch) -> None:
    import sqlite3

    db = tmp_path / "old.db"
    monkeypatch.setenv("TRAINERMON_DB", str(db))
    raw = sqlite3.connect(db)
    raw.execute(
        """
        CREATE TABLE users (
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
    raw.commit()
    raw.close()

    from services.accounts import connect, init_db

    init_db()
    with connect() as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
    assert {"trainer_level", "team", "timezone", "region", "age_ok"} <= columns
