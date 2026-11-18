"""Trade search is a filter over lists. It never returns a friend code."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from tools.trade_match import satisfies


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("TRAINERMON_DB", str(tmp_path / "trades.db"))
    return TestClient(app)


def _register(client: TestClient, email: str, name: str, city: str) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "correct horse",
            "trainer_name": name,
            "city": city,
        },
    )
    assert response.status_code == 200


def _add(client: TestClient, kind: str, species_id: str, **flags: bool) -> None:
    response = client.post(
        "/api/lists",
        json={"kind": kind, "species_id": species_id, **flags},
    )
    assert response.status_code == 200


def test_shiny_want_does_not_match_a_plain_have() -> None:
    want = {"species_id": "magikarp", "form": "", "shiny": True}
    plain = {"species_id": "magikarp", "form": "", "shiny": False}
    shiny = {"species_id": "magikarp", "form": "", "shiny": True}
    assert satisfies(want, plain) is False
    assert satisfies(want, shiny) is True
    assert satisfies({"species_id": "magikarp", "form": "", "shiny": False}, plain)


def test_city_filter_hides_email_and_friend_code(client: TestClient) -> None:
    _register(client, "avery@example.com", "Avery", "Toronto")
    _add(client, "want", "magikarp", shiny=True)
    _add(client, "have", "heracross")
    client.post("/api/auth/logout")

    _register(client, "jordan@example.com", "Jordan", "Toronto")
    _add(client, "want", "heracross")
    _add(client, "have", "magikarp", shiny=True)
    client.post("/api/auth/logout")

    _register(client, "sam@example.com", "Sam", "Montreal")
    _add(client, "have", "magikarp", shiny=True)
    client.post("/api/auth/logout")

    signed_in = client.post(
        "/api/auth/login",
        json={"email": "avery@example.com", "password": "correct horse"},
    )
    assert signed_in.status_code == 200
    toronto = client.get("/api/trades/search", params={"city": "toronto"})
    assert toronto.status_code == 200
    names = [row["trainer_name"] for row in toronto.json()["matches"]]
    assert names == ["Jordan"]
    match = toronto.json()["matches"][0]
    assert set(match) == {"trainer_name", "city", "they_have", "i_have"}
    assert match["they_have"][0]["name"] == "Magikarp"
    assert match["i_have"][0]["name"] == "Heracross"
    dumped = str(toronto.json())
    assert "friend_code" not in dumped
    assert "example.com" not in dumped

    everywhere = client.get("/api/trades/search", params={"city": "all"})
    everywhere_names = [row["trainer_name"] for row in everywhere.json()["matches"]]
    assert everywhere_names == ["Sam", "Jordan"]
