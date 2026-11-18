"""Local accounts: register, sign in, and a friend code that stays private."""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("TRAINERMON_DB", str(tmp_path / "accounts.db"))
    monkeypatch.setenv("SHARE_FRIEND_CODES", "")
    return TestClient(app)


def test_register_login_and_profile(client: TestClient) -> None:
    created = client.post(
        "/api/auth/register",
        json={
            "email": "Avery@example.com",
            "password": "correct horse",
            "trainer_name": "Avery",
            "city": "",
            "friend_code": "1234 5678 9012",
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert body["email"] == "avery@example.com"
    assert body["city"] == "Toronto"
    assert body["friend_code"] == "123456789012"
    assert "password" not in body

    me = client.get("/api/me")
    assert me.status_code == 200
    assert me.json()["trainer_name"] == "Avery"

    updated = client.patch(
        "/api/me",
        json={"trainer_name": "Ave", "city": "Toronto", "friend_code": ""},
    )
    assert updated.status_code == 200
    assert updated.json()["friend_code"] == ""

    client.post("/api/auth/logout")
    assert client.get("/api/me").status_code == 401

    signed_in = client.post(
        "/api/auth/login",
        json={"email": "avery@example.com", "password": "correct horse"},
    )
    assert signed_in.status_code == 200
    assert client.get("/api/me").json()["trainer_name"] == "Ave"


def test_bad_password_and_duplicate_email(client: TestClient) -> None:
    payload = {
        "email": "sam@example.com",
        "password": "long-enough",
        "trainer_name": "Sam",
        "city": "Toronto",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 200
    client.post("/api/auth/logout")
    again = client.post("/api/auth/register", json=payload)
    assert again.status_code == 400
    wrong = client.post(
        "/api/auth/login",
        json={"email": "sam@example.com", "password": "nope-nope"},
    )
    assert wrong.status_code == 401
    assert client.get("/api/me").status_code == 401


def test_friend_code_must_be_twelve_digits(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "jo@example.com",
            "password": "long-enough",
            "trainer_name": "Jo",
            "friend_code": "123",
        },
    )
    assert response.status_code == 400
    assert "12 digits" in response.json()["detail"]
