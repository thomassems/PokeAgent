"""Admin curation. Drafts are not part of the public catalog."""

from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel

from api.community import require_user
from services.curation import list_facts, save_drafts, set_status

router = APIRouter()


class DraftIn(BaseModel):
    pasted: str
    source_url: str
    verified_at: str


@router.get("/api/curation")
def get_curation(trainermon_session: str | None = Cookie(default=None)) -> dict:
    user = require_user(trainermon_session)
    try:
        return {"facts": list_facts_for(user["email"])}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def list_facts_for(email: str) -> list[dict]:
    from services.accounts import is_admin

    if not is_admin(email):
        raise PermissionError("Curation is limited to admin accounts.")
    return list_facts()


@router.post("/api/curation/draft")
def post_draft(
    body: DraftIn, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    user = require_user(trainermon_session)
    try:
        return {
            "facts": save_drafts(
                user["email"], body.pasted, body.source_url, body.verified_at
            )
        }
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/curation/{fact_id}/approve")
def approve(
    fact_id: int, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    return _decide(fact_id, "approved", trainermon_session)


@router.post("/api/curation/{fact_id}/reject")
def reject(fact_id: int, trainermon_session: str | None = Cookie(default=None)) -> dict:
    return _decide(fact_id, "rejected", trainermon_session)


def _decide(fact_id: int, status: str, token: str | None) -> dict:
    user = require_user(token)
    try:
        return set_status(user["email"], fact_id, status)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
