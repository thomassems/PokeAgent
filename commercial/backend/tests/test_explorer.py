"""Explorer filters the hand-kept seed. Tags combine with AND."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_regional_and_name() -> None:
    regional = client.get("/api/explorer", params={"regional": "true"})
    names = [row["name"] for row in regional.json()["species"]]
    assert "Heracross" in names
    assert "Magikarp" not in names
    assert regional.json()["seed"] is True

    narrowed = client.get("/api/explorer", params={"regional": "true", "query": "tau"})
    assert [row["id"] for row in narrowed.json()["species"]] == ["tauros"]


def test_gigantamax_does_not_include_dynamax_only() -> None:
    rows = client.get("/api/explorer", params={"gigantamax": "true"}).json()["species"]
    ids = {row["id"] for row in rows}
    assert "melmetal" in ids
    assert "charizard" in ids
    assert "articuno" not in ids


def test_untradable_mythicals_stay_in_the_catalog() -> None:
    rows = client.get("/api/explorer", params={"mythical": "true"}).json()["species"]
    by_id = {row["id"]: row["tradable"] for row in rows}
    assert by_id["mew"] is False
    assert by_id["meltan"] is True
