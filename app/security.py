"""JWT session helpers + the current-user dependency.

The session is a signed JWT stored in an httpOnly cookie. This module owns:
  - issuing the JWT (create_session_token),
  - setting/clearing the session cookie on a Response,
  - resolving the authenticated user from the request cookie (get_current_user).
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session

from app import config
from app.db import get_db
from app.models.user import User


def create_session_token(user: User) -> str:
    """Issue a signed session JWT for a user."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=config.JWT_TTL_SECONDS)).timestamp()),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def _decode(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=config.SESSION_COOKIE_NAME,
        value=token,
        max_age=config.JWT_TTL_SECONDS,
        httponly=True,
        secure=config.COOKIE_SECURE,
        samesite=config.COOKIE_SAMESITE,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=config.SESSION_COOKIE_NAME,
        httponly=True,
        secure=config.COOKIE_SECURE,
        samesite=config.COOKIE_SAMESITE,
        path="/",
    )


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Return the authenticated user from the session cookie, or None."""
    token = request.cookies.get(config.SESSION_COOKIE_NAME)
    if not token:
        return None
    payload = _decode(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    try:
        return db.get(User, int(user_id))
    except (TypeError, ValueError):
        return None
