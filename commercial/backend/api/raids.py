"""Remote-raid lobbies. No chat, no game-account fields, no live charge."""

from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel

from api.community import require_user
from services.raids import (
    accept_joiner,
    create_lobby,
    join_lobby,
    list_lobbies,
    list_reports,
    lobby_view,
    queue_for_host,
    report_lobby,
    set_opt_in,
    set_status,
)

router = APIRouter()


class OptIn(BaseModel):
    enabled: bool


class LobbyIn(BaseModel):
    species_id: str
    starts_at: str
    city: str = ""


class AcceptIn(BaseModel):
    user_id: int


class StatusIn(BaseModel):
    status: str


class ReportIn(BaseModel):
    reason: str


def _http(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/api/raids")
def get_raids() -> dict:
    return {"lobbies": list_lobbies()}


@router.post("/api/raids/opt-in")
def post_opt_in(
    body: OptIn, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    user = require_user(trainermon_session)
    try:
        return set_opt_in(user["id"], body.enabled)
    except (ValueError, LookupError) as exc:
        raise _http(exc) from exc


@router.post("/api/raids")
def post_raid(
    body: LobbyIn, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    user = require_user(trainermon_session)
    try:
        return create_lobby(user["id"], body.species_id, body.starts_at, body.city)
    except (ValueError, LookupError) as exc:
        raise _http(exc) from exc


@router.get("/api/raids/reports")
def get_reports(trainermon_session: str | None = Cookie(default=None)) -> dict:
    user = require_user(trainermon_session)
    try:
        return {"reports": list_reports(user["email"])}
    except PermissionError as exc:
        raise _http(exc) from exc


@router.get("/api/raids/{raid_id}")
def get_raid(
    raid_id: int, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    user = require_user(trainermon_session)
    try:
        return lobby_view(user["id"], raid_id)
    except LookupError as exc:
        raise _http(exc) from exc


@router.post("/api/raids/{raid_id}/join")
def post_join(
    raid_id: int, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    user = require_user(trainermon_session)
    try:
        return join_lobby(user["id"], raid_id)
    except (ValueError, LookupError) as exc:
        raise _http(exc) from exc


@router.get("/api/raids/{raid_id}/queue")
def get_queue(
    raid_id: int, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    user = require_user(trainermon_session)
    try:
        return {"queue": queue_for_host(user["id"], raid_id)}
    except (PermissionError, LookupError) as exc:
        raise _http(exc) from exc


@router.post("/api/raids/{raid_id}/accept")
def post_accept(
    raid_id: int,
    body: AcceptIn,
    trainermon_session: str | None = Cookie(default=None),
) -> dict:
    user = require_user(trainermon_session)
    try:
        return accept_joiner(user["id"], raid_id, body.user_id)
    except (PermissionError, LookupError, ValueError) as exc:
        raise _http(exc) from exc


@router.post("/api/raids/{raid_id}/status")
def post_status(
    raid_id: int,
    body: StatusIn,
    trainermon_session: str | None = Cookie(default=None),
) -> dict:
    user = require_user(trainermon_session)
    try:
        return set_status(user["id"], raid_id, body.status)
    except (PermissionError, LookupError, ValueError) as exc:
        raise _http(exc) from exc


@router.post("/api/raids/{raid_id}/report")
def post_report(
    raid_id: int,
    body: ReportIn,
    trainermon_session: str | None = Cookie(default=None),
) -> dict:
    user = require_user(trainermon_session)
    try:
        return report_lobby(user["id"], raid_id, body.reason)
    except (LookupError, ValueError) as exc:
        raise _http(exc) from exc
