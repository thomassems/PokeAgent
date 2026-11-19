"""Collection checklists. Free until checklists_open says otherwise."""

from typing import Literal

from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel

from api.community import require_user
from services.collections import (
    add_missing_wants,
    get_collection,
    list_collections,
    set_owned,
)

router = APIRouter()


class OwnIn(BaseModel):
    kind: Literal["costume", "background"]
    value: str
    owned: bool
    shiny: bool = False


@router.get("/api/collections")
def get_collections(trainermon_session: str | None = Cookie(default=None)) -> dict:
    user = require_user(trainermon_session)
    try:
        return {"collections": list_collections(user)}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/api/collections/{collection_id}")
def get_one(
    collection_id: str, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    user = require_user(trainermon_session)
    try:
        return get_collection(user, collection_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/collections/{collection_id}/items")
def post_item(
    collection_id: str,
    body: OwnIn,
    trainermon_session: str | None = Cookie(default=None),
) -> dict:
    user = require_user(trainermon_session)
    try:
        return set_owned(
            user, collection_id, body.kind, body.value, body.owned, body.shiny
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/collections/{collection_id}/wants")
def post_wants(
    collection_id: str, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    user = require_user(trainermon_session)
    try:
        return add_missing_wants(user, collection_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
