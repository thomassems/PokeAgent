"""Accounts for the commercial app. Lists and search are added beside these routes.

No route reads a Pokémon GO account. Friend codes are not returned to anyone
except the owner, and SHARE_FRIEND_CODES does not change that.
"""

from typing import Literal

from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel, Field

from data.go_catalog import EntryFlags, catalog, filter_catalog
from services.accounts import (
    cookie_name,
    login,
    logout,
    register,
    update_profile,
    user_from_token,
)
from services.lists import add_entry, delete_entry, list_entries, update_entry
from services.trades import search_trades

router = APIRouter()
_MAX_AGE = 14 * 24 * 60 * 60


class RegisterIn(BaseModel):
    email: str
    password: str
    trainer_name: str
    city: str = "Toronto"
    friend_code: str = ""


class LoginIn(BaseModel):
    email: str
    password: str


class ProfileIn(BaseModel):
    trainer_name: str
    city: str = Field(default="Toronto")
    friend_code: str = ""


class EntryIn(BaseModel):
    kind: Literal["want", "have"]
    species_id: str
    form: str = ""
    shiny: bool = False
    dynamax: bool = False
    gigantamax: bool = False
    shadow: bool = False
    purified: bool = False
    lucky: bool = False
    costume: bool = False
    notes: str = ""


class EntryPatch(BaseModel):
    form: str = ""
    shiny: bool = False
    dynamax: bool = False
    gigantamax: bool = False
    shadow: bool = False
    purified: bool = False
    lucky: bool = False
    costume: bool = False
    notes: str = ""


def _flags(body: EntryIn | EntryPatch) -> EntryFlags:
    return EntryFlags(
        form=body.form,
        shiny=body.shiny,
        dynamax=body.dynamax,
        gigantamax=body.gigantamax,
        shadow=body.shadow,
        purified=body.purified,
        lucky=body.lucky,
        costume=body.costume,
        notes=body.notes,
    )


def _set_session(response: Response, token: str) -> None:
    response.set_cookie(
        cookie_name(),
        token,
        httponly=True,
        samesite="lax",
        max_age=_MAX_AGE,
        path="/",
    )


def require_user(token: str | None) -> dict:
    user = user_from_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in first.")
    return user


@router.post("/api/auth/register")
def register_account(body: RegisterIn, response: Response) -> dict:
    try:
        user, token = register(
            body.email, body.password, body.trainer_name, body.city, body.friend_code
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _set_session(response, token)
    return user


@router.post("/api/auth/login")
def login_account(body: LoginIn, response: Response) -> dict:
    try:
        user, token = login(body.email, body.password)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    _set_session(response, token)
    return user


@router.post("/api/auth/logout")
def logout_account(
    response: Response, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    logout(trainermon_session)
    response.delete_cookie(cookie_name(), path="/")
    return {"ok": True}


@router.get("/api/me")
def me(trainermon_session: str | None = Cookie(default=None)) -> dict:
    return require_user(trainermon_session)


@router.patch("/api/me")
def patch_me(
    body: ProfileIn, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    user = require_user(trainermon_session)
    try:
        return update_profile(
            user["id"], body.trainer_name, body.city, body.friend_code
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/catalog")
def get_catalog() -> list[dict]:
    return [item.model_dump() for item in catalog()]


@router.get("/api/lists")
def get_lists(trainermon_session: str | None = Cookie(default=None)) -> dict:
    user = require_user(trainermon_session)
    return {"entries": list_entries(user["id"])}


@router.post("/api/lists")
def post_list(
    body: EntryIn, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    user = require_user(trainermon_session)
    try:
        return add_entry(user["id"], body.kind, _flags(body), body.species_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/api/lists/{entry_id}")
def patch_list(
    entry_id: int,
    body: EntryPatch,
    trainermon_session: str | None = Cookie(default=None),
) -> dict:
    user = require_user(trainermon_session)
    try:
        return update_entry(user["id"], entry_id, _flags(body))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/api/lists/{entry_id}")
def remove_list(
    entry_id: int, trainermon_session: str | None = Cookie(default=None)
) -> dict:
    user = require_user(trainermon_session)
    try:
        delete_entry(user["id"], entry_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}


@router.get("/api/trades/search")
def trade_search(
    city: str = "Toronto",
    trainermon_session: str | None = Cookie(default=None),
) -> dict:
    user = require_user(trainermon_session)
    return {"city": city, "matches": search_trades(user["id"], city)}


@router.get("/api/explorer")
def explorer(
    query: str = "",
    shiny: bool = False,
    dynamax: bool = False,
    gigantamax: bool = False,
    shadow: bool = False,
    costume: bool = False,
    regional: bool = False,
    mythical: bool = False,
    legendary: bool = False,
) -> dict:
    return {
        "seed": True,
        "species": filter_catalog(
            query=query,
            shiny=shiny,
            dynamax=dynamax,
            gigantamax=gigantamax,
            shadow=shadow,
            costume=costume,
            regional=regional,
            mythical=mythical,
            legendary=legendary,
        ),
    }
