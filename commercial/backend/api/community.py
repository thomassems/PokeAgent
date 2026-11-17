"""Accounts for the commercial app. Lists and search are added beside these routes.

No route reads a Pokémon GO account. Friend codes are not returned to anyone
except the owner, and SHARE_FRIEND_CODES does not change that.
"""

from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel, Field

from services.accounts import (
    cookie_name,
    login,
    logout,
    register,
    update_profile,
    user_from_token,
)

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
