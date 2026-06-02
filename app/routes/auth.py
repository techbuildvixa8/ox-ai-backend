"""Passwordless email auth + session routes.

The email is the identity — no passwords, no Google OAuth. Submitting an email
creates the user if needed and starts a JWT httpOnly cookie session.

Exposes exactly what the frontend expects:
    POST /auth/email    -> { email } : upsert user + set session cookie
    GET  /auth/session  -> current user JSON or 401
    GET  /auth/logout   -> clear session
"""
import re

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import config
from app.db import get_db
from app.models.user import User
from app.security import (
    clear_session_cookie,
    create_session_token,
    get_current_user,
    set_session_cookie,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Pragmatic email shape check (not full RFC 5322; enough to reject obvious junk).
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmailLoginRequest(BaseModel):
    email: str


def _user_json(user: User) -> dict:
    return {"id": str(user.id), "email": user.email, "name": user.name}


@router.post("/email")
def email_login(
    payload: EmailLoginRequest,
    db: Session = Depends(get_db),
) -> Response:
    """Create the user if new, then start a session. No password required."""
    email = payload.email.strip().lower()
    if not _EMAIL_RE.match(email):
        return JSONResponse(status_code=422, content={"detail": "invalid email"})

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        # Derive a friendly default name from the local-part on first login.
        user = User(email=email, name=email.split("@", 1)[0])
        db.add(user)
        db.commit()
        db.refresh(user)

    response = JSONResponse(content=_user_json(user))
    set_session_cookie(response, create_session_token(user))
    return response


@router.get("/session")
def session(user: User | None = Depends(get_current_user)) -> Response:
    """Return the current user as JSON, or 401 when unauthenticated."""
    if user is None:
        return JSONResponse(status_code=401, content={"detail": "unauthenticated"})
    return JSONResponse(content=_user_json(user))


@router.get("/logout")
def logout() -> Response:
    """Clear the session cookie."""
    response = JSONResponse(content={"ok": True})
    clear_session_cookie(response)
    return response
