"""Environment-driven configuration for the auth foundation.

Values come from the process environment (loaded from a local .env via
python-dotenv). Nothing secret is committed; see .env.example for the keys.
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default)


# --- Frontend ---
# Used for CORS allow_origins (credentialed requests cannot use "*").
FRONTEND_URL = _get("FRONTEND_URL", "http://localhost:5173")

# --- Session JWT / cookies ---
JWT_SECRET = _get("JWT_SECRET", "change-me-to-a-long-random-secret")
JWT_ALGORITHM = "HS256"
JWT_TTL_SECONDS = int(_get("JWT_TTL_SECONDS", "604800"))  # 7 days

SESSION_COOKIE_NAME = "ox_session"
COOKIE_SECURE = _get("COOKIE_SECURE", "0") == "1"
COOKIE_SAMESITE = "lax"

# --- Database ---
DATABASE_URL = _get("DATABASE_URL", "sqlite:///./ox_ai.db")
