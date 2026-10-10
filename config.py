"""Application configuration, read from environment variables.

Nothing sensitive is hardcoded here. Secrets and administrator credentials
must be supplied through the environment (or a local, untracked .env file).
"""
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _env_bool(name, default):
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name, default):
    try:
        return int(os.environ.get(name, "").strip())
    except ValueError:
        return default


def _data_dir():
    raw = (os.environ.get("DATA_DIR") or "").strip()
    if not raw:
        return BASE_DIR / "data"
    path = Path(raw)
    return path if path.is_absolute() else BASE_DIR / path


def load_config():
    """Build the configuration dictionary from the current environment."""
    app_env = (os.environ.get("APP_ENV") or "development").strip().lower()
    is_production = app_env == "production"

    return {
        "APP_ENV": app_env,
        "SECRET_KEY": os.environ.get("SECRET_KEY") or None,
        # Administrator credentials. Prefer ADMIN_PASSWORD_HASH; ADMIN_PASSWORD
        # is accepted for convenience and is hashed in memory at startup.
        "ADMIN_USERNAME": (os.environ.get("ADMIN_USERNAME") or "admin").strip(),
        "ADMIN_PASSWORD_HASH": os.environ.get("ADMIN_PASSWORD_HASH") or None,
        "ADMIN_PASSWORD": os.environ.get("ADMIN_PASSWORD") or None,
        # Storage.
        "DATA_DIR": _data_dir(),
        "SAMPLE_DATA_FILE": BASE_DIR / "data" / "sample_data" / "students_sample.json",
        "SEED_SAMPLE_DATA": _env_bool("SEED_SAMPLE_DATA", True),
        # Deployment behind a reverse proxy such as Render.
        "TRUST_PROXY": _env_bool("TRUST_PROXY", False),
        # Session and cookie hardening.
        "SESSION_COOKIE_NAME": "sms_session",
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": _env_bool("SESSION_COOKIE_SECURE", is_production),
        "PERMANENT_SESSION_LIFETIME": timedelta(hours=8),
        "MAX_CONTENT_LENGTH": 64 * 1024,
        # Login throttling.
        "LOGIN_MAX_ATTEMPTS": _env_int("LOGIN_MAX_ATTEMPTS", 5),
        "LOGIN_LOCKOUT_SECONDS": _env_int("LOGIN_LOCKOUT_SECONDS", 300),
        # Presentation.
        "PER_PAGE": 10,
    }
