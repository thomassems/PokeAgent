"""Curate labels, shiny state, alias merges, and bulk decisions."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from data.costume_aliases import COSTUME_ALIASES
from data.go_catalog import format_slug, variant_label
from services.accounts import connect, init_db
from services.curation import init_curation, list_facts

_SEED = Path(__file__).resolve().parents[1] / "data" / "go_curated_seed.json"


def test_slug_fallback_reads_as_an_event_name() -> None:
    assert format_slug("gotour-2024-a") == "GO Tour 2024 (A)"
    assert format_slug("gotour-2024-a-02") == "GO Tour 2024 (A) 02"
    assert format_slug("flying-5th-anniv") == "Flying 5th anniversary"
    assert format_slug("halloween-2021-noevolve") == "Halloween 2021"
    assert variant_label("costume", "doctor") == "Ph.D."
    assert variant_label("costume", "pop-star") == "Pop Star"
    assert variant_label("costume", "rock-star") == "Rock Star"


def test_seed_merges_community_codes_into_the_official_row() -> None:
    rows = json.loads(_SEED.read_text())["rows"]
    for alias in COSTUME_ALIASES:
        official = next(
            row
            for row in rows
            if row["species_id"] == alias.species_id
            and row["kind"] == "costume"
            and row["value"] == alias.official
            and row.get("source_type", "official") == "official"
        )
        community = next(
            row
            for row in rows
            if row["species_id"] == alias.species_id
            and row["kind"] == "costume"
            and row["value"] == alias.community
            and row.get("source_type") == "community"
        )
        assert alias.because in official["notes"]
        assert alias.community in official["community_aliases"]
        assert community["status"] == "merged"
        assert community["merged_into"] == alias.official
        assert official.get("status", "approved") != "merged"


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("TRAINERMON_DB", str(tmp_path / "curate.db"))
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


def test_list_marks_confirmed_shiny_and_hides_nothing_from_the_payload(
    client: TestClient,
) -> None:
    _register(client, "admin@example.com")
    facts = client.get("/api/curation").json()["facts"]
    rayquaza = next(
        row
        for row in facts
        if row["species_id"] == "pikachu" and row["value"] == "rayquaza-hat"
    )
    worlds = next(
        row
        for row in facts
        if row["species_id"] == "pikachu"
        and row["value"] == "worlds-2022"
        and row["kind"] == "costume"
    )
    doctor = next(
        row
        for row in facts
        if row["species_id"] == "pikachu" and row["value"] == "doctor"
    )
    merged = next(
        row
        for row in facts
        if row["species_id"] == "pikachu" and row["value"] == "hoenn-2020-noevolve"
    )
    assert "hoenn-2020-noevolve" in rayquaza["aliases"]
    assert rayquaza["label"] == "Rayquaza hat"
    assert rayquaza["shiny"] == "unknown"
    assert worlds["shiny"] == "confirmed"
    assert doctor["label"] == "Ph.D."
    assert doctor["shiny"] == "unknown"
    assert doctor["status"] == "approved"
    assert doctor["verified_by"] == "auto-verifier"
    assert doctor["verification"]["verdict"] == "auto-approve"
    assert doctor["verification"]["urls"]
    assert merged["status"] == "merged"


def test_bulk_approve_records_the_admin_and_bulk_reject_does_not(
    client: TestClient,
) -> None:
    _register(client, "admin@example.com")
    facts = client.get("/api/curation").json()["facts"]
    pop_star = next(row for row in facts if row["value"] == "pop-star")
    rock_star = next(row for row in facts if row["value"] == "rock-star")
    approved = client.post(
        "/api/curation/bulk",
        json={"ids": [pop_star["id"], rock_star["id"]], "status": "approved"},
    )
    assert approved.status_code == 200
    assert {row["verified_by"] for row in approved.json()["facts"]} == {
        "admin@example.com"
    }
    after = client.get("/api/explorer", params={"query": "pikachu"}).json()
    pikachu = next(row for row in after["species"] if row["id"] == "pikachu")
    assert "pop-star" in pikachu["forms"]
    assert "rock-star" in pikachu["forms"]
    assert "hoenn-2020-noevolve" not in pikachu["forms"]

    festive = next(
        row
        for row in facts
        if row["species_id"] == "pikachu" and row["value"] == "festive-hat"
    )
    rejected = client.post(
        "/api/curation/bulk",
        json={"ids": [festive["id"]], "status": "rejected"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["facts"][0]["verified_by"] == festive["verified_by"]
    assert rejected.json()["facts"][0]["status"] == "rejected"


def test_unapprove_records_the_admin_and_drops_the_checklist_row(
    client: TestClient,
) -> None:
    _register(client, "admin@example.com")
    facts = client.get("/api/curation").json()["facts"]
    doctor = next(row for row in facts if row["value"] == "doctor")
    before = client.get("/api/collections/pikachu-costumes").json()
    assert any(item["value"] == "doctor" for item in before["items"])
    returned = client.post(f"/api/curation/{doctor['id']}/unapprove")
    assert returned.status_code == 200
    assert returned.json()["status"] == "draft"
    assert returned.json()["verified_by"] == "admin@example.com"
    after = client.get("/api/collections/pikachu-costumes").json()
    assert after["total"] == before["total"] - 1
    assert all(item["value"] != "doctor" for item in after["items"])


def test_merged_alias_and_stranger_cannot_be_bulk_approved(client: TestClient) -> None:
    _register(client, "admin@example.com")
    facts = client.get("/api/curation").json()["facts"]
    merged = next(row for row in facts if row["value"] == "hoenn-2020-noevolve")
    denied = client.post(
        "/api/curation/bulk",
        json={"ids": [merged["id"]], "status": "approved"},
    )
    assert denied.status_code == 400
    client.post("/api/auth/logout")
    _register(client, "fan@example.com")
    response = client.post(
        "/api/curation/bulk",
        json={"ids": [merged["id"]], "status": "approved"},
    )
    assert response.status_code == 403


def test_old_database_accepts_a_merged_status(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TRAINERMON_DB", str(tmp_path / "old.db"))
    init_db()
    seed_row = next(
        row
        for row in json.loads(_SEED.read_text())["rows"]
        if row["value"] == "hoenn-2020-noevolve"
    )
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE curated_facts (
                id INTEGER PRIMARY KEY,
                species_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                value TEXT NOT NULL,
                source_url TEXT NOT NULL,
                verified_at TEXT NOT NULL,
                verified_by TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (status IN ('draft', 'approved', 'rejected')),
                notes TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conn.execute(
            """
            INSERT INTO curated_facts (
                species_id, kind, value, source_url, verified_at, verified_by,
                status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, 'draft', 'old import')
            """,
            (
                seed_row["species_id"],
                seed_row["kind"],
                seed_row["value"],
                seed_row["source_url"],
                seed_row["verified_at"],
                seed_row["verified_by"],
            ),
        )
    init_curation()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT status, merged_into FROM curated_facts
            WHERE value = 'hoenn-2020-noevolve'
            """
        ).fetchone()
        table_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'curated_facts'"
        ).fetchone()[0]
    assert row["status"] == "merged"
    assert row["merged_into"] == "rayquaza-hat"
    assert "'merged'" in table_sql
    listed = list_facts()
    doctor = next(item for item in listed if item["value"] == "doctor")
    assert doctor["label"] == "Ph.D."
