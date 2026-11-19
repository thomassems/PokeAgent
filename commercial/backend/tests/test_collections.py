"""Pikachu checklist: verified rows only, and missing items become wants."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from services.accounts import connect
from services.curation import init_curation

_SEED = Path(__file__).resolve().parents[1] / "data" / "go_curated_seed.json"
_BANNED = ("leekduck", "scrapedduck", "pokeminers", "bulbapedia", "serebii")


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("TRAINERMON_DB", str(tmp_path / "collections.db"))
    return TestClient(app)


def _register(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "collector@example.com",
            "password": "correct horse",
            "trainer_name": "Casey",
            "city": "Toronto",
            "trainer_level": 40,
            "team": "mystic",
            "timezone": "America/Toronto",
            "age_confirmed": True,
        },
    )
    assert response.status_code == 200


def _pikachu_rows() -> list[dict[str, str]]:
    rows = json.loads(_SEED.read_text())["rows"]
    return [row for row in rows if row["species_id"] == "pikachu"]


def test_pikachu_seed_rows_are_sourced() -> None:
    rows = _pikachu_rows()
    costumes = {row["value"] for row in rows if row["kind"] == "costume"}
    backgrounds = {row["value"] for row in rows if row["kind"] == "background"}
    assert costumes
    assert backgrounds
    shiny_costumes = {row["value"] for row in rows if row["kind"] == "costume_shiny"}
    shiny_backgrounds = {
        row["value"] for row in rows if row["kind"] == "background_shiny"
    }
    assert shiny_costumes <= costumes
    assert shiny_backgrounds <= backgrounds
    for row in rows:
        assert row["source_url"].startswith("https://pokemongolive.com/")
        assert row["verified_at"] == "2026-11-19"
        assert row["verified_by"] == "hand-seed"
        blob = f"{row['source_url']} {row['notes']}".lower()
        assert not any(banned in blob for banned in _BANNED)
        if row["kind"] != "shiny":
            assert row["value"].replace("-", "").isalnum()


def test_checklist_counts_verified_rows_only(client: TestClient) -> None:
    _register(client)
    rows = _pikachu_rows()
    expected = sum(1 for row in rows if row["kind"] in {"costume", "background"})
    body = client.get("/api/collections/pikachu-costumes")
    assert body.status_code == 200
    payload = body.json()
    assert payload["have"] == 0
    assert payload["total"] == expected
    assert payload["total"] == len(payload["items"])
    assert all(item["owned"] is False for item in payload["items"])

    init_curation()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO curated_facts (
                species_id, kind, value, source_url, verified_at,
                verified_by, status, notes
            ) VALUES (
                'pikachu', 'costume', 'unapproved-hat',
                'https://pokemongolive.com/en/news/example',
                '2026-11-19', 'tester', 'draft', ''
            )
            """
        )
    after = client.get("/api/collections/pikachu-costumes").json()
    assert after["total"] == expected
    assert all(item["value"] != "unapproved-hat" for item in after["items"])


def test_mark_owned_and_add_missing_wants(client: TestClient) -> None:
    _register(client)
    first = client.get("/api/collections/pikachu-costumes").json()["items"][0]
    marked = client.post(
        "/api/collections/pikachu-costumes/items",
        json={
            "kind": first["kind"],
            "value": first["value"],
            "owned": True,
            "shiny": True,
        },
    )
    assert marked.status_code == 200
    assert marked.json()["have"] == 1
    owned = next(
        item for item in marked.json()["items"] if item["value"] == first["value"]
    )
    assert owned["owned"] is True
    assert owned["shiny"] is True

    wants = client.post("/api/collections/pikachu-costumes/wants")
    assert wants.status_code == 200
    assert wants.json()["added"] == wants.json()["total"] - 1
    again = client.post("/api/collections/pikachu-costumes/wants")
    assert again.json()["added"] == 0

    entries = client.get("/api/lists").json()["entries"]
    have = next(entry for entry in entries if entry["kind"] == "have")
    assert have["shiny"] is True
    if first["kind"] == "costume":
        assert have["form"] == first["value"]
        assert have["costume"] is True
    missing_wants = [entry for entry in entries if entry["kind"] == "want"]
    assert len(missing_wants) == wants.json()["added"]
    assert all(entry["species_id"] == "pikachu" for entry in missing_wants)


def test_stranger_is_rejected_and_the_gate_is_one_function(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    stranger = client.get("/api/collections")
    assert stranger.status_code == 401

    _register(client)
    monkeypatch.setattr("services.collections.checklists_open", lambda _user: False)
    gated = client.get("/api/collections")
    assert gated.status_code == 403
