"""Authentication — POST /api/auth/login, GET /api/auth/config."""
from __future__ import annotations
import hmac
import hashlib
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


def compute_token(password: str, secret: str) -> str:
    """Derive a stable auth token from password + secret key."""
    return hmac.new(secret.encode(), password.encode(), hashlib.sha256).hexdigest()


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str


@router.get("/auth/config")
async def auth_config():
    """Tell the frontend whether a password is required."""
    settings = get_settings()
    return {"auth_required": bool(settings.auth_password)}


@router.post("/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest) -> LoginResponse:
    settings = get_settings()

    # Auth disabled — any (or no) password works
    if not settings.auth_password:
        return LoginResponse(token="no-auth")

    expected = compute_token(settings.auth_password, settings.secret_key)
    given = compute_token(req.password, settings.secret_key)

    try:
        valid = hmac.compare_digest(given, expected)
    except (TypeError, ValueError):
        valid = False

    if not valid:
        raise HTTPException(status_code=401, detail="Invalid password")

    return LoginResponse(token=expected)
