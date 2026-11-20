"""Player reports and the admin queue. Confirming does not publish."""

from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel

from api.community import require_user
from services.reports import (
    confirm_report,
    file_report,
    list_open,
    reject_report,
)

router = APIRouter()


class ReportIn(BaseModel):
    species_id: str
    tag: str
    note: str


class ConfirmIn(BaseModel):
    kind: str
    value: str
    source_url: str
    verified_at: str


@router.post("/api/reports")
def post_report(
    body: ReportIn, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    user = require_user(trainermon_session)
    try:
        return file_report(user["id"], body.species_id, body.tag, body.note)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/reports")
def get_reports(trainermon_session: str | None = Cookie(default=None)) -> dict:
    user = require_user(trainermon_session)
    try:
        return {"reports": list_open(user["email"])}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/api/reports/{report_id}/confirm")
def post_confirm(
    report_id: int,
    body: ConfirmIn,
    trainermon_session: str | None = Cookie(default=None),
) -> dict:
    user = require_user(trainermon_session)
    try:
        return confirm_report(
            user["email"],
            report_id,
            body.kind,
            body.value,
            body.source_url,
            body.verified_at,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/reports/{report_id}/reject")
def post_reject(
    report_id: int, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    user = require_user(trainermon_session)
    try:
        return reject_report(user["email"], report_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
