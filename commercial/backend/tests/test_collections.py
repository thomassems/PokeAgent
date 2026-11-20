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


def _approved(row: dict[str, str]) -> bool:
    return row.get("status", "approved") == "approved"


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
        status = row.get("status", "approved")
        assert status in {"approved", "draft", "merged"}
        source_type = row.get("source_type", "official")
        if source_type == "community":
            assert row["verified_by"] == "community-import"
            assert row["source_url"].startswith("https://pokemon-go-api.github.io/")
            if status == "merged":
                assert row.get("merged_into")
            else:
                assert status == "draft"
        else:
            assert status in {"approved", "draft"}
            assert row["verified_by"] == "hand-seed"
            assert row["source_url"].startswith("https://pokemongolive.com/")
        if status == "approved":
            assert row["verified_at"] == "2026-11-19"
        elif source_type != "community":
            assert row["verified_at"] == "2026-11-20"
        blob = " ".join(
            (
                row["source_url"],
                row.get("community_source_url", ""),
                row["notes"],
            )
        ).lower()
        assert not any(banned in blob for banned in _BANNED)
        if row["kind"] != "shiny":
            assert row["value"].replace("-", "").isalnum()


def test_new_costume_rows_stay_draft_until_approved() -> None:
    rows = json.loads(_SEED.read_text())["rows"]
    drafts = [row for row in rows if row.get("status") == "draft"]
    assert drafts
    assert {row["kind"] for row in drafts} >= {"costume", "background"}
    for row in drafts:
        if row.get("source_type") == "community":
            assert row["verified_at"]
            assert row["verified_by"] == "community-import"
            assert row["source_url"].startswith("https://pokemon-go-api.github.io/")
        else:
            assert row["verified_at"] == "2026-11-20"
            assert row["verified_by"] == "hand-seed"
        assert row["source_url"].startswith("https://")
    approved = [row for row in rows if _approved(row)]
    assert all("status" not in row or row["status"] == "approved" for row in approved)


def test_checklist_counts_verified_rows_only(client: TestClient) -> None:
    _register(client)
    rows = _pikachu_rows()
    expected = sum(
        1 for row in rows if row["kind"] in {"costume", "background"} and _approved(row)
    )
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


def test_every_costumed_species_has_a_collection() -> None:
    seed = json.loads(_SEED.read_text())["rows"]
    definitions = json.loads(
        Path(__file__)
        .resolve()
        .parents[1]
        .joinpath("data/collections.json")
        .read_text()
    )["collections"]
    by_species = {item["species_id"]: item for item in definitions}
    wanted: dict[str, set[str]] = {}
    for row in seed:
        if row["kind"] in {"costume", "background"}:
            wanted.setdefault(row["species_id"], set()).add(row["kind"])
    assert set(by_species) == set(wanted)
    for species, kinds in wanted.items():
        assert set(by_species[species]["kinds"]) == kinds


def test_a_draft_only_collection_totals_zero(client: TestClient) -> None:
    _register(client)
    body = client.get("/api/collections/eevee-costumes")
    assert body.status_code == 200
    payload = body.json()
    assert payload["total"] == 0
    assert payload["items"] == []
    listing = client.get("/api/collections").json()["collections"]
    assert any(item["id"] == "eevee-costumes" for item in listing)


def test_stranger_is_rejected_and_the_gate_is_one_function(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    stranger = client.get("/api/collections")
    assert stranger.status_code == 401

    _register(client)
    monkeypatch.setattr("services.collections.checklists_open", lambda _user: False)
    gated = client.get("/api/collections")
    assert gated.status_code == 403
