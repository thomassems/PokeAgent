"""Explorer filters the hand-kept seed. Tags combine with AND."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_regional_and_name() -> None:
    regional = client.get("/api/explorer", params={"regional": "true"})
    names = [row["name"] for row in regional.json()["species"]]
    assert "Heracross" in names
    assert "Magikarp" not in names
    assert regional.json()["seed"] is False

    narrowed = client.get("/api/explorer", params={"regional": "true", "query": "tau"})
    assert [row["id"] for row in narrowed.json()["species"]] == ["tauros"]


def test_gigantamax_does_not_include_dynamax_only() -> None:
    rows = client.get("/api/explorer", params={"gigantamax": "true"}).json()["species"]
    ids = {row["id"] for row in rows}
    assert "machamp" in ids
    assert "bulbasaur" not in ids
    assert "articuno" not in ids


def test_untradable_mythicals_stay_in_the_catalog() -> None:
    rows = client.get("/api/explorer", params={"mythical": "true"}).json()["species"]
    by_id = {row["id"]: row["tradable"] for row in rows}
    assert by_id["mew"] is False
    assert by_id["meltan"] is True


def test_exact_species_keeps_unknown_axes_and_rejects_bad_combos() -> None:
    named = client.get("/api/explorer", params={"query": "Magikarp", "dynamax": "true"})
    assert named.status_code == 200
    assert [row["id"] for row in named.json()["species"]] == ["magikarp"]
    assert named.json()["unverified"] == []

    by_id = client.get(
        "/api/explorer", params={"species_id": "magikarp", "gigantamax": "true"}
    )
    assert by_id.status_code == 200
    assert by_id.json()["unverified"] == ["Gigantamax"]

    costume = client.get(
        "/api/explorer",
        params={"species_id": "magikarp", "dynamax": "true", "costume": "true"},
    )
    assert costume.status_code == 400
    assert "costume" in costume.json()["detail"]

    shiny = client.get(
        "/api/explorer", params={"species_id": "magikarp", "shiny": "true"}
    )
    assert shiny.status_code == 200
    assert [row["id"] for row in shiny.json()["species"]] == ["magikarp"]
    variants = shiny.json()["species"][0]["variants"]
    assert variants["dynamax"] == "verified"
    assert variants["shiny"] == "verified"
    assert variants["gigantamax"] == "unknown"
    assert {item["id"] for item in variants["backgrounds"]} == {"dynamax-trails"}

    unknown_form = client.get("/api/explorer", params={"form": "not-a-form"})
    assert unknown_form.status_code == 400
