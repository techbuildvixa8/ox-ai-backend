"""Environment-driven configuration for the auth foundation.

Values come from the process environment (loaded from a local .env via
python-dotenv). Nothing secret is committed; see .env.example for the keys.
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default)


# --- Google OAuth ---
GOOGLE_CLIENT_ID = _get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = _get("GOOGLE_CLIENT_SECRET")
OAUTH_REDIRECT_URI = _get("OAUTH_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

# Google OAuth 2.0 endpoints.
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_SCOPES = "openid email profile"

# --- Frontend ---
FRONTEND_URL = _get("FRONTEND_URL", "http://localhost:5173")

# --- Session JWT / cookies ---
JWT_SECRET = _get("JWT_SECRET", "change-me-to-a-long-random-secret")
JWT_ALGORITHM = "HS256"
JWT_TTL_SECONDS = int(_get("JWT_TTL_SECONDS", "604800"))  # 7 days

SESSION_COOKIE_NAME = "ox_session"
OAUTH_STATE_COOKIE_NAME = "oauth_state"
COOKIE_SECURE = _get("COOKIE_SECURE", "0") == "1"
# 'lax' lets the cookie survive the top-level redirect back from Google.
COOKIE_SAMESITE = "lax"

# --- Database ---
DATABASE_URL = _get("DATABASE_URL", "sqlite:///./ox_ai.db")
