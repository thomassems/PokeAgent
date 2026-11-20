"""Reports stay off Explorer until a curator approves the draft they open."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from services.reports import REPORT_OPEN_CAP


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("TRAINERMON_DB", str(tmp_path / "reports.db"))
    monkeypatch.setenv("TRAINERMON_ADMINS", "admin@example.com")
    return TestClient(app)


def _register(client: TestClient, email: str) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "correct horse",
            "trainer_name": "Ada",
            "city": "Toronto",
            "trainer_level": 40,
            "team": "mystic",
            "timezone": "America/Toronto",
            "age_confirmed": True,
        },
    )
    assert response.status_code == 200


def test_stranger_cannot_report(client: TestClient) -> None:
    response = client.post(
        "/api/reports",
        json={"species_id": "pikachu", "tag": "missing", "note": "A hat is missing."},
    )
    assert response.status_code == 401


def test_confirm_opens_a_draft_and_explorer_stays_the_same(client: TestClient) -> None:
    _register(client, "fan@example.com")
    filed = client.post(
        "/api/reports",
        json={
            "species_id": "pikachu",
            "tag": "missing",
            "note": "Detective hat is not listed.",
        },
    )
    assert filed.status_code == 200
    body = filed.json()
    assert body["species_id"] == "pikachu"
    assert body["tag"] == "missing"
    assert body["status"] == "open"
    assert body["created_at"]
    assert body["user_id"]

    stranger_queue = client.get("/api/reports")
    assert stranger_queue.status_code == 403

    client.post(
        "/api/auth/register",
        json={
            "email": "admin@example.com",
            "password": "correct horse",
            "trainer_name": "Thomas",
            "city": "Toronto",
            "trainer_level": 40,
            "team": "mystic",
            "timezone": "America/Toronto",
            "age_confirmed": True,
        },
    )
    before = client.get("/api/explorer", params={"query": "pikachu"}).json()
    pikachu = next(row for row in before["species"] if row["id"] == "pikachu")
    assert "detective-hat" not in pikachu["forms"]

    confirmed = client.post(
        f"/api/reports/{body['id']}/confirm",
        json={
            "kind": "costume",
            "value": "detective-hat",
            "source_url": "https://pokemongolive.com/news/example",
            "verified_at": "2026-11-20",
        },
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"
    assert confirmed.json()["draft"]["status"] == "draft"

    after = client.get("/api/explorer", params={"query": "pikachu"}).json()
    pikachu = next(row for row in after["species"] if row["id"] == "pikachu")
    assert "detective-hat" not in pikachu["forms"]

    queue = client.get("/api/reports")
    assert queue.status_code == 200
    assert queue.json()["reports"] == []


def test_open_report_cap(client: TestClient) -> None:
    _register(client, "fan@example.com")
    for index in range(REPORT_OPEN_CAP):
        response = client.post(
            "/api/reports",
            json={
                "species_id": "pikachu",
                "tag": "wrong",
                "note": f"Flag {index} looks wrong.",
            },
        )
        assert response.status_code == 200
    blocked = client.post(
        "/api/reports",
        json={"species_id": "eevee", "tag": "missing", "note": "One more hat."},
    )
    assert blocked.status_code == 400


def test_reject_hides_the_report(client: TestClient) -> None:
    _register(client, "admin@example.com")
    filed = client.post(
        "/api/reports",
        json={
            "species_id": "eevee",
            "tag": "wrong",
            "note": "This shiny flag is wrong.",
        },
    )
    rejected = client.post(f"/api/reports/{filed.json()['id']}/reject")
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert client.get("/api/reports").json()["reports"] == []
