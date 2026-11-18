"""Want and have lists: mythicals are blocked, special trades are labelled."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from data.go_catalog import EntryFlags, apply_facts, base_catalog, check_entry
from tools.trade_rules import trade_notes


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("TRAINERMON_DB", str(tmp_path / "lists.db"))
    return TestClient(app)


def _register(client: TestClient, email: str) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "correct horse",
            "trainer_name": "Avery",
            "city": "Toronto",
            "age_confirmed": True,
        },
    )
    assert response.status_code == 200


def test_mythical_is_blocked_and_meltan_is_not(client: TestClient) -> None:
    _register(client, "avery@example.com")
    blocked = client.post(
        "/api/lists",
        json={"kind": "want", "species_id": "mew"},
    )
    assert blocked.status_code == 400
    assert "cannot be traded" in blocked.json()["detail"]

    allowed = client.post(
        "/api/lists",
        json={"kind": "have", "species_id": "meltan"},
    )
    assert allowed.status_code == 200
    assert allowed.json()["name"] == "Meltan"

    shiny = client.post(
        "/api/lists",
        json={"kind": "want", "species_id": "magikarp", "shiny": True},
    )
    assert shiny.status_code == 200
    assert any("Special Trade" in note for note in shiny.json()["trade_notes"])
    assert any("Forever Friends" in note for note in shiny.json()["trade_notes"])


def test_shiny_legendary_and_shadow_notes() -> None:
    mewtwo = next(item for item in base_catalog() if item.id == "mewtwo")
    notes = trade_notes(mewtwo, shiny=True, shadow=True)
    assert any("Good Friends" in note for note in notes)
    assert any("Forever Friends" in note for note in notes)
    assert any("cannot be traded remotely" in note for note in notes)

    magikarp = next(item for item in base_catalog() if item.id == "magikarp")
    plain = trade_notes(magikarp, shiny=False, shadow=False)
    assert plain == ["A remote trade needs Forever Friends."]
    shiny = apply_facts(
        magikarp,
        [
            {
                "species_id": "magikarp",
                "kind": "shiny",
                "value": "true",
                "status": "approved",
            }
        ],
    )
    check_entry(shiny, EntryFlags(shiny=True))
    with pytest.raises(ValueError, match="not marked Dynamax"):
        check_entry(magikarp, EntryFlags(dynamax=True))


def test_crud_and_unknown_species(client: TestClient) -> None:
    _register(client, "avery@example.com")
    missing = client.get("/api/lists")
    assert missing.json()["entries"] == []

    created = client.post(
        "/api/lists",
        json={
            "kind": "want",
            "species_id": "lapras",
            "form": "scarf",
            "costume": True,
            "notes": "scarf",
        },
    )
    assert created.status_code == 200
    entry_id = created.json()["id"]

    bad_form = client.patch(
        f"/api/lists/{entry_id}",
        json={"form": "alolan", "costume": True},
    )
    assert bad_form.status_code == 400

    updated = client.patch(
        f"/api/lists/{entry_id}",
        json={"form": "scarf", "costume": True, "lucky": True},
    )
    assert updated.status_code == 200
    assert updated.json()["lucky"] is True

    unknown = client.post(
        "/api/lists", json={"kind": "have", "species_id": "missingno"}
    )
    assert unknown.status_code == 400

    deleted = client.delete(f"/api/lists/{entry_id}")
    assert deleted.status_code == 200
    assert client.get("/api/lists").json()["entries"] == []

    stranger = client.delete(f"/api/lists/{entry_id}")
    assert stranger.status_code == 404
