"""Drafts stay hidden until an admin approves them."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from services.curation import parse_drafts


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("TRAINERMON_DB", str(tmp_path / "curation.db"))
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


def test_parse_drafts_reads_a_json_fence() -> None:
    drafts = parse_drafts(
        '```json\n[{"species_name":"Wooloo","kind":"dynamax","value":"true"}]\n```'
    )
    assert drafts == [{"species_id": "wooloo", "kind": "dynamax", "value": "true"}]


def test_draft_is_hidden_until_approved(client: TestClient) -> None:
    _register(client, "admin@example.com")

    def fake(_prompt: str) -> str:
        return '[{"species_name":"Pikachu","kind":"costume","value":"test-cap"}]'

    from services.curation import save_drafts

    saved = save_drafts(
        "admin@example.com",
        "Pikachu in a party hat will appear. If you are lucky, it can be shiny.",
        "https://example.com/official-post",
        "2026-11-18",
        completer=fake,
    )
    assert saved[0]["status"] == "draft"
    before = client.get("/api/explorer", params={"query": "pikachu"}).json()
    pikachu = next(row for row in before["species"] if row["id"] == "pikachu")
    assert "test-cap" not in pikachu["forms"]

    approved = client.post(f"/api/curation/{saved[0]['id']}/approve")
    assert approved.status_code == 200
    after = client.get("/api/explorer", params={"query": "pikachu"}).json()
    pikachu = next(row for row in after["species"] if row["id"] == "pikachu")
    assert "test-cap" in pikachu["forms"]


def test_stranger_cannot_curate(client: TestClient) -> None:
    _register(client, "fan@example.com")
    response = client.get("/api/curation")
    assert response.status_code == 403
