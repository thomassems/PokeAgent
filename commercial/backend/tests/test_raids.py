"""Paid waits ahead of Free. Friend codes stay hidden until both opt in."""

import json

import pytest
from fastapi.testclient import TestClient

from api.main import app
from services.accounts import connect


def _register(client: TestClient, email: str, name: str, code: str) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "correct horse",
            "trainer_name": name,
            "city": "Toronto",
            "friend_code": code,
            "trainer_level": 40,
            "team": "mystic",
            "timezone": "America/Toronto",
            "age_confirmed": True,
        },
    )
    assert response.status_code == 200


def _opt_in(client: TestClient) -> None:
    response = client.post("/api/raids/opt-in", json={"enabled": True})
    assert response.status_code == 200
    assert response.json()["raid_opt_in"] is True


@pytest.fixture
def clients(tmp_path, monkeypatch: pytest.MonkeyPatch) -> dict[str, TestClient]:
    monkeypatch.setenv("TRAINERMON_DB", str(tmp_path / "raids.db"))
    monkeypatch.setenv("TRAINERMON_ADMINS", "admin@example.com")
    made = {name: TestClient(app) for name in ("host", "free", "paid", "admin")}
    _register(made["host"], "host@example.com", "Host", "111122223333")
    _register(made["free"], "free@example.com", "Free", "222233334444")
    _register(made["paid"], "paid@example.com", "Paid", "333344445555")
    _register(made["admin"], "admin@example.com", "Admin", "444455556666")
    with connect() as conn:
        conn.execute(
            "UPDATE users SET plan = 'paid' WHERE email = ?",
            ("paid@example.com",),
        )
    return made


def test_paid_is_offered_before_an_earlier_free_request(
    clients: dict[str, TestClient],
) -> None:
    closed = clients["host"].post(
        "/api/raids",
        json={
            "species_id": "mewtwo",
            "starts_at": "2026-11-21T18:00:00+00:00",
        },
    )
    assert closed.status_code == 400

    _opt_in(clients["host"])
    created = clients["host"].post(
        "/api/raids",
        json={
            "species_id": "mewtwo",
            "starts_at": "2026-11-21T18:00:00+00:00",
        },
    )
    assert created.status_code == 200
    raid_id = created.json()["id"]
    assert created.json()["city"] == "Toronto"
    assert "email" not in created.json()
    assert "111122223333" not in json.dumps(created.json())

    blocked = clients["free"].post(f"/api/raids/{raid_id}/join")
    assert blocked.status_code == 400

    _opt_in(clients["free"])
    _opt_in(clients["paid"])
    assert clients["free"].post(f"/api/raids/{raid_id}/join").status_code == 200
    assert clients["paid"].post(f"/api/raids/{raid_id}/join").status_code == 200

    queue = clients["host"].get(f"/api/raids/{raid_id}/queue").json()["queue"]
    assert [row["trainer_name"] for row in queue] == ["Paid", "Free"]
    assert queue[0]["raid_priority"] == "paid"
    dumped = json.dumps(queue)
    assert "email" not in queue[0]
    assert "@" not in dumped
    assert "333344445555" not in dumped

    clients["paid"].post("/api/raids/opt-in", json={"enabled": False})
    refused = clients["host"].post(
        f"/api/raids/{raid_id}/accept",
        json={"user_id": queue[0]["user_id"]},
    )
    assert refused.status_code == 400

    _opt_in(clients["paid"])
    accepted = clients["host"].post(
        f"/api/raids/{raid_id}/accept",
        json={"user_id": queue[0]["user_id"]},
    )
    assert accepted.status_code == 200
    assert accepted.json()["friend_code"] == "333344445555"

    public = clients["free"].get("/api/raids").json()
    assert "333344445555" not in json.dumps(public)
    assert "host@example.com" not in json.dumps(public)

    seat = clients["paid"].get(f"/api/raids/{raid_id}").json()
    assert seat["host_friend_code"] == "111122223333"
    waiting = clients["free"].get(f"/api/raids/{raid_id}").json()
    assert "host_friend_code" not in waiting


def test_a_report_can_close_a_lobby(clients: dict[str, TestClient]) -> None:
    _opt_in(clients["host"])
    created = clients["host"].post(
        "/api/raids",
        json={"species_id": "mewtwo", "starts_at": "2026-11-21T18:00:00+00:00"},
    )
    raid_id = created.json()["id"]
    reported = clients["free"].post(
        f"/api/raids/{raid_id}/report",
        json={"reason": "paid_hosting"},
    )
    assert reported.status_code == 200
    hidden = clients["free"].get("/api/raids/reports")
    assert hidden.status_code == 403
    listed = clients["admin"].get("/api/raids/reports")
    assert listed.status_code == 200
    assert listed.json()["reports"][0]["reason"] == "paid_hosting"
    cancelled = clients["admin"].post(
        f"/api/raids/{raid_id}/status",
        json={"status": "cancelled"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
