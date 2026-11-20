"""Lemon Squeezy stays in test mode. A live event never grants Paid."""

import hashlib
import hmac
import io
import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from agents.events import TraceEvent
from api import main
from services.billing import FREE_DAILY_RUNS, reserve_run


def _sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _event(
    email: str,
    *,
    status: str = "active",
    test_mode: bool = True,
    variant: str = "11",
    user_id: int | None = 1,
    ends_at: str | None = None,
) -> bytes:
    payload: dict[str, Any] = {
        "meta": {
            "event_name": "subscription_created",
            "custom_data": {"user_id": str(user_id)} if user_id else {},
        },
        "data": {
            "type": "subscriptions",
            "id": "sub_1",
            "attributes": {
                "variant_id": int(variant),
                "user_email": email,
                "status": status,
                "test_mode": test_mode,
                "ends_at": ends_at,
                "urls": {"customer_portal": "https://example.test/billing"},
            },
        },
    }
    return json.dumps(payload).encode()


def _client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("TRAINERMON_DB", str(tmp_path / "billing.db"))
    monkeypatch.setenv("LEMONSQUEEZY_TEST_MODE", "true")
    monkeypatch.setenv("LEMONSQUEEZY_API_KEY", "test_key")
    monkeypatch.setenv("LEMONSQUEEZY_STORE_ID", "9")
    monkeypatch.setenv("LEMONSQUEEZY_VARIANT_MONTHLY", "11")
    monkeypatch.setenv("LEMONSQUEEZY_VARIANT_YEARLY", "12")
    monkeypatch.setenv("LEMONSQUEEZY_WEBHOOK_SECRET", "signing-secret")
    return TestClient(main.app)


def _register(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "ada@example.com",
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


def test_checkout_is_test_mode_and_a_live_key_is_refused(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    _register(client)

    class FakeResponse(io.BytesIO):
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

    def fake_urlopen(request: Any, timeout: int = 20) -> FakeResponse:
        sent = json.loads(request.data.decode())
        assert sent["data"]["attributes"]["test_mode"] is True
        assert "custom_price" not in sent["data"]["attributes"]
        body = json.dumps(
            {
                "data": {
                    "attributes": {
                        "test_mode": True,
                        "url": "https://checkout.example.test/buy",
                    }
                }
            }
        ).encode()
        return FakeResponse(body)

    monkeypatch.setattr("services.billing.urllib.request.urlopen", fake_urlopen)
    response = client.post("/api/billing/checkout", json={"interval": "month"})
    assert response.status_code == 200
    assert response.json()["url"].startswith("https://")

    monkeypatch.setenv("LEMONSQUEEZY_API_KEY", "live_secret")
    refused = client.post("/api/billing/checkout", json={"interval": "year"})
    assert refused.status_code == 503

    monkeypatch.setenv("LEMONSQUEEZY_API_KEY", "test_key")
    monkeypatch.setenv("LEMONSQUEEZY_TEST_MODE", "")
    off = client.post("/api/billing/checkout", json={"interval": "month"})
    assert off.status_code == 503


def test_webhook_grants_and_removes_paid(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    _register(client)
    secret = "signing-secret"
    body = _event("ada@example.com")
    bad = client.post(
        "/api/billing/webhook",
        content=body,
        headers={"x-signature": "nope"},
    )
    assert bad.status_code == 401
    assert client.get("/api/billing").json()["plan"] == "free"

    ok = client.post(
        "/api/billing/webhook",
        content=body,
        headers={"x-signature": _sign(secret, body)},
    )
    assert ok.status_code == 200
    billing = client.get("/api/billing").json()
    assert billing["plan"] == "paid"
    assert billing["raid_priority"] == "paid"
    assert billing["assistant_cap"] == 20
    assert billing["monthly_usd"] == "4.99"
    assert billing["yearly_usd"] == "49.99"

    live = _event("ada@example.com", test_mode=False)
    refused = client.post(
        "/api/billing/webhook",
        content=live,
        headers={"x-signature": _sign(secret, live)},
    )
    assert refused.status_code == 400
    assert client.get("/api/billing").json()["plan"] == "paid"

    other = _event("ada@example.com", variant="99")
    ignored = client.post(
        "/api/billing/webhook",
        content=other,
        headers={"x-signature": _sign(secret, other)},
    )
    assert ignored.status_code == 200
    assert ignored.json()["ignored"] is True

    ended = _event("ada@example.com", status="expired")
    cleared = client.post(
        "/api/billing/webhook",
        content=ended,
        headers={"x-signature": _sign(secret, ended)},
    )
    assert cleared.status_code == 200
    assert client.get("/api/billing").json()["plan"] == "free"
    assert client.get("/api/billing").json()["raid_priority"] == "free"


def test_signed_in_assistant_stops_at_the_free_cap(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = _client(tmp_path, monkeypatch)
    _register(client)

    def fail_if_called(*args: object, **kwargs: object) -> list[TraceEvent]:
        raise AssertionError("the agent should not start")

    monkeypatch.setitem(main.AGENTS, "custom", fail_if_called)
    for _ in range(FREE_DAILY_RUNS):
        reserve_run(1)
    response = client.post("/api/runs", json={"prompt": "one more"})
    assert response.status_code == 200
    assert "Daily assistant cap reached." in response.text
