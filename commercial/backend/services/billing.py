"""One Paid tier, charged by Lemon Squeezy in test mode only.

Checkout and webhooks follow the current docs (checked 20 November 2026):
https://docs.lemonsqueezy.com/api/checkouts/create-checkout
https://docs.lemonsqueezy.com/help/webhooks/signing-requests
https://docs.lemonsqueezy.com/help/getting-started/test-mode

The prices live on the two variants in the Lemon Squeezy dashboard:
$4.99 a month and $49.99 a year. This module does not set a custom price.
A live event, a live-looking key, or test mode left off is refused.
"""

import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from typing import Any

from services.accounts import connect, init_db

# Modest on purpose. API cost stays the limit. Thomas can change these.
FREE_DAILY_RUNS = 5
PAID_DAILY_RUNS = 20
PAID_STATUSES = {"active", "on_trial"}
_API = "https://api.lemonsqueezy.com/v1/checkouts"


def init_billing() -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assistant_usage (
                user_id INTEGER NOT NULL,
                day TEXT NOT NULL,
                runs INTEGER NOT NULL,
                PRIMARY KEY (user_id, day)
            )
            """
        )


def test_mode_enabled() -> bool:
    return os.environ.get("LEMONSQUEEZY_TEST_MODE", "").strip() == "true"


def _require_test_mode() -> None:
    if not test_mode_enabled():
        raise RuntimeError("Lemon Squeezy test mode is off.")


def _api_key() -> str:
    _require_test_mode()
    key = os.environ.get("LEMONSQUEEZY_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Lemon Squeezy is not configured.")
    if "live" in key.lower():
        raise RuntimeError("A live Lemon Squeezy key is refused.")
    return key


def _variant(interval: str) -> str:
    if interval == "month":
        name = "LEMONSQUEEZY_VARIANT_MONTHLY"
    elif interval == "year":
        name = "LEMONSQUEEZY_VARIANT_YEARLY"
    else:
        raise ValueError("Choose month or year.")
    value = os.environ.get(name, "").strip()
    if not value.isdigit():
        raise RuntimeError("Lemon Squeezy variant is not configured.")
    return value


def _configured_variants() -> set[str]:
    found = set()
    for name in ("LEMONSQUEEZY_VARIANT_MONTHLY", "LEMONSQUEEZY_VARIANT_YEARLY"):
        value = os.environ.get(name, "").strip()
        if value.isdigit():
            found.add(value)
    return found


def create_checkout(user_id: int, email: str, interval: str) -> str:
    """Ask Lemon Squeezy for a test checkout URL. No card is charged here."""
    key = _api_key()
    store = os.environ.get("LEMONSQUEEZY_STORE_ID", "").strip()
    if not store.isdigit():
        raise RuntimeError("Lemon Squeezy store is not configured.")
    variant = _variant(interval)
    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "test_mode": True,
                "product_options": {"enabled_variants": [int(variant)]},
                "checkout_data": {
                    "email": email,
                    "custom": {"user_id": str(user_id)},
                },
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": store}},
                "variant": {"data": {"type": "variants", "id": variant}},
            },
        }
    }
    body = json.dumps(payload).encode()
    request = urllib.request.Request(
        _API,
        data=body,
        headers={
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            parsed = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise RuntimeError("Lemon Squeezy refused the checkout.") from exc
    attributes = parsed.get("data", {}).get("attributes", {})
    if attributes.get("test_mode") is not True:
        raise RuntimeError("Lemon Squeezy did not return a test checkout.")
    url = attributes.get("url")
    if not isinstance(url, str) or not url.startswith("https://"):
        raise RuntimeError("Lemon Squeezy did not return a checkout URL.")
    return url


def _signature_ok(secret: str, body: bytes, header: str) -> bool:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    try:
        return hmac.compare_digest(digest, header.strip())
    except ValueError:
        return False


def _paid_until(attributes: dict[str, Any]) -> bool:
    status = str(attributes.get("status") or "")
    if status in PAID_STATUSES:
        return True
    if status != "cancelled":
        return False
    ends = attributes.get("ends_at")
    if not isinstance(ends, str) or not ends:
        return False
    try:
        end = datetime.fromisoformat(ends.replace("Z", "+00:00"))
    except ValueError:
        return False
    return end > datetime.now(UTC)


def apply_webhook(body: bytes, signature: str) -> dict[str, Any]:
    """Signed test-mode subscription events set or clear Paid.

    The signature is HMAC-SHA256 of the raw body, hex, in X-Signature.
    """
    _require_test_mode()
    secret = os.environ.get("LEMONSQUEEZY_WEBHOOK_SECRET", "").strip()
    if not secret or not _signature_ok(secret, body, signature):
        raise PermissionError("Bad signature.")
    payload = json.loads(body)
    meta = payload.get("meta") or {}
    event = str(meta.get("event_name") or "")
    if not event.startswith("subscription_"):
        return {"ignored": True, "reason": "not a subscription"}
    data = payload.get("data") or {}
    attributes = data.get("attributes") or {}
    if attributes.get("test_mode") is not True:
        raise ValueError("Live Lemon Squeezy events are refused.")
    variant = str(attributes.get("variant_id") or "")
    if variant not in _configured_variants():
        return {"ignored": True, "reason": "unknown variant"}
    user_id = _user_id(meta, attributes)
    if user_id is None:
        return {"ignored": True, "reason": "unknown account"}
    plan = "paid" if _paid_until(attributes) else "free"
    portal = ""
    urls = attributes.get("urls") or {}
    if isinstance(urls, dict):
        portal = str(urls.get("customer_portal") or "")
    init_billing()
    with connect() as conn:
        conn.execute(
            """
            UPDATE users
            SET plan = ?, lemon_subscription_id = ?, lemon_status = ?,
                lemon_portal_url = ?
            WHERE id = ?
            """,
            (
                plan,
                str(data.get("id") or ""),
                str(attributes.get("status") or ""),
                portal,
                user_id,
            ),
        )
    return {"plan": plan, "user_id": user_id}


def _user_id(meta: dict[str, Any], attributes: dict[str, Any]) -> int | None:
    custom = meta.get("custom_data") or {}
    raw = custom.get("user_id") if isinstance(custom, dict) else None
    init_billing()
    with connect() as conn:
        if raw is not None and str(raw).isdigit():
            row = conn.execute(
                "SELECT id FROM users WHERE id = ?", (int(raw),)
            ).fetchone()
            if row is not None:
                return int(row["id"])
        email = str(attributes.get("user_email") or "").strip().lower()
        if not email:
            return None
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if row is None:
        return None
    return int(row["id"])


def entitlement(user_id: int) -> dict[str, Any]:
    init_billing()
    with connect() as conn:
        row = conn.execute(
            "SELECT plan, lemon_status, lemon_portal_url FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    plan = "free"
    portal = ""
    status = ""
    if row is not None and row["plan"] == "paid":
        plan = "paid"
        portal = row["lemon_portal_url"] or ""
        status = row["lemon_status"] or ""
    return {
        "plan": plan,
        "raid_priority": "paid" if plan == "paid" else "free",
        "assistant_cap": PAID_DAILY_RUNS if plan == "paid" else FREE_DAILY_RUNS,
        "lemon_status": status,
        "portal_url": portal,
        "test_mode": test_mode_enabled(),
        "monthly_usd": "4.99",
        "yearly_usd": "49.99",
    }


def reserve_run(user_id: int) -> None:
    """Count one assistant run. Raises when today's cap is used."""
    cap = entitlement(user_id)["assistant_cap"]
    day = datetime.now(UTC).date().isoformat()
    init_billing()
    with connect() as conn:
        row = conn.execute(
            "SELECT runs FROM assistant_usage WHERE user_id = ? AND day = ?",
            (user_id, day),
        ).fetchone()
        used = int(row["runs"]) if row is not None else 0
        if used >= cap:
            raise ValueError("Daily assistant cap reached.")
        conn.execute(
            """
            INSERT INTO assistant_usage (user_id, day, runs)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, day) DO UPDATE SET runs = runs + 1
            """,
            (user_id, day),
        )
