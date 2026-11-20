"""Test-mode checkout and the Lemon Squeezy webhook. No live charges."""

from fastapi import APIRouter, Cookie, HTTPException, Request
from pydantic import BaseModel

from api.community import require_user
from services.billing import apply_webhook, create_checkout, entitlement

router = APIRouter()


class CheckoutIn(BaseModel):
    interval: str


@router.get("/api/billing")
def get_billing(trainermon_session: str | None = Cookie(default=None)) -> dict:
    user = require_user(trainermon_session)
    return entitlement(user["id"])


@router.post("/api/billing/checkout")
def post_checkout(
    body: CheckoutIn, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    user = require_user(trainermon_session)
    try:
        url = create_checkout(user["id"], user["email"], body.interval)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"url": url}


@router.post("/api/billing/webhook")
async def post_webhook(request: Request) -> dict:
    body = await request.body()
    signature = request.headers.get("x-signature", "")
    try:
        return apply_webhook(body, signature)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
