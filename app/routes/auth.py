"""Google OAuth + session routes.

Implements the Authorization Code flow directly with httpx (no extra OAuth
dependency) so we fully control the CSRF state cookie and the session cookie.

Exposes exactly what the frontend expects:
    GET /auth/google           -> redirect to Google
    GET /auth/google/callback  -> exchange code, upsert user, set session, return to app
    GET /auth/session          -> current user JSON or 401
    GET /auth/logout           -> clear session, return to app
"""
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
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


@router.get("/google")
def google_login() -> RedirectResponse:
    """Begin Google sign-in: redirect to the consent screen.

    A random `state` is set as a short-lived httpOnly cookie and echoed to
    Google so the callback can verify it (CSRF protection).
    """
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": config.OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": config.GOOGLE_SCOPES,
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    response = RedirectResponse(url=f"{config.GOOGLE_AUTH_URL}?{urlencode(params)}")
    response.set_cookie(
        key=config.OAUTH_STATE_COOKIE_NAME,
        value=state,
        max_age=600,
        httponly=True,
        secure=config.COOKIE_SECURE,
        samesite=config.COOKIE_SAMESITE,
        path="/",
    )
    return response


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    """Handle Google's redirect: verify state, exchange code, upsert user."""
    error = request.query_params.get("error")
    if error:
        return RedirectResponse(url=f"{config.FRONTEND_URL}/chat?auth_error={error}")

    code = request.query_params.get("code")
    state = request.query_params.get("state")
    expected_state = request.cookies.get(config.OAUTH_STATE_COOKIE_NAME)

    if not code or not state or not expected_state or state != expected_state:
        return RedirectResponse(url=f"{config.FRONTEND_URL}/chat?auth_error=invalid_state")

    async with httpx.AsyncClient(timeout=15) as client:
        token_res = await client.post(
            config.GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": config.GOOGLE_CLIENT_ID,
                "client_secret": config.GOOGLE_CLIENT_SECRET,
                "redirect_uri": config.OAUTH_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
        )
        if token_res.status_code != 200:
            return RedirectResponse(url=f"{config.FRONTEND_URL}/chat?auth_error=token_exchange")
        access_token = token_res.json().get("access_token")
        if not access_token:
            return RedirectResponse(url=f"{config.FRONTEND_URL}/chat?auth_error=no_access_token")

        userinfo_res = await client.get(
            config.GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_res.status_code != 200:
            return RedirectResponse(url=f"{config.FRONTEND_URL}/chat?auth_error=userinfo")
        info = userinfo_res.json()

    google_sub = info.get("sub")
    email = info.get("email")
    if not google_sub or not email:
        return RedirectResponse(url=f"{config.FRONTEND_URL}/chat?auth_error=incomplete_profile")

    # Upsert: create the user on first login, otherwise refresh profile fields.
    user = db.query(User).filter(User.google_sub == google_sub).first()
    if user is None:
        user = User(
            google_sub=google_sub,
            email=email,
            name=info.get("name"),
            avatar_url=info.get("picture"),
        )
        db.add(user)
    else:
        user.email = email
        user.name = info.get("name")
        user.avatar_url = info.get("picture")
    db.commit()
    db.refresh(user)

    response = RedirectResponse(url=f"{config.FRONTEND_URL}/chat")
    set_session_cookie(response, create_session_token(user))
    # State cookie has served its purpose.
    response.delete_cookie(config.OAUTH_STATE_COOKIE_NAME, path="/")
    return response


@router.get("/session")
def session(user: User | None = Depends(get_current_user)) -> Response:
    """Return the current user as JSON, or 401 when unauthenticated."""
    if user is None:
        return JSONResponse(status_code=401, content={"detail": "unauthenticated"})
    return JSONResponse(
        content={
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "avatarUrl": user.avatar_url,
        }
    )


@router.get("/logout")
def logout() -> Response:
    """Clear the session cookie and return to the frontend."""
    response = RedirectResponse(url=config.FRONTEND_URL)
    clear_session_cookie(response)
    return response
