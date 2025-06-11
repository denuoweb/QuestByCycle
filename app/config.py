"""Configuration loader using environment variables."""

from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)


def _get_env(key: str, default=None):
    """Return environment variable or default."""
    return os.getenv(key, default)


def _get_env_boolean(key: str, default: bool):
    """Retrieve a boolean environment variable."""
    val = os.getenv(key)
    if val is None:
        return default
    return val.lower() in ("true", "1", "yes")


def _get_env_integer(key: str, default: int):
    """Retrieve an integer environment variable."""
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _get_env_nullable(key: str, default=None):
    """Return ``None`` for falsey environment values."""
    val = os.getenv(key)
    if val is None:
        val = default
    if val in (False, "", "false", "False", None):
        return None
    return val


def load_config():
    """Build configuration using environment variables with reasonable defaults."""

    cfg = {
        "main": {
            "UPLOAD_FOLDER": _get_env("UPLOAD_FOLDER", "images"),
            "VERIFICATIONS": _get_env("VERIFICATIONS", "verifications"),
            "BADGE_IMAGE_DIR": _get_env("BADGE_IMAGE_DIR", "badge_images"),
            "TASKCSV": _get_env("TASKCSV", "csv"),
            "LOCAL_DOMAIN": _get_env("LOCAL_DOMAIN", "localhost:5000"),
            "FFMPEG_PATH": _get_env("FFMPEG_PATH", "ffmpeg"),
            "PLACEHOLDER_IMAGE": _get_env(
                "PLACEHOLDER_IMAGE", "images/default-placeholder.webp"
            ),
            "SQLALCHEMY_ECHO": _get_env_boolean("SQLALCHEMY_ECHO", False),
            "USE_TASK_QUEUE": _get_env_boolean("USE_TASK_QUEUE", True),
        },
        "encryption": {
            "DEFAULT_SUPER_ADMIN_USERNAME": _get_env(
                "DEFAULT_SUPER_ADMIN_USERNAME", "test"
            ),
            "DEFAULT_SUPER_ADMIN_PASSWORD": _get_env(
                "DEFAULT_SUPER_ADMIN_PASSWORD", "test"
            ),
            "DEFAULT_SUPER_ADMIN_EMAIL": _get_env(
                "DEFAULT_SUPER_ADMIN_EMAIL", "test@test.com"
            ),
            "SECRET_KEY": _get_env("SECRET_KEY", "replace this key"),
            "SESSION_COOKIE_SECURE": _get_env_boolean("SESSION_COOKIE_SECURE", False),
            "SESSION_COOKIE_NAME": _get_env(
                "SESSION_COOKIE_NAME", "QuestsByCycles_Session"
            ),
            "SESSION_COOKIE_SAMESITE": _get_env("SESSION_COOKIE_SAMESITE", "Lax"),
            "SESSION_COOKIE_DOMAIN": _get_env_nullable("SESSION_COOKIE_DOMAIN", False),
            "SESSION_REFRESH_EACH_REQUEST": _get_env_boolean(
                "SESSION_REFRESH_EACH_REQUEST", True
            ),
            "REMEMBER_COOKIE_DURATION_DAYS": _get_env_integer(
                "REMEMBER_COOKIE_DURATION_DAYS", 7
            ),
        },
        "openai": {
            "OPENAI_API_KEY": _get_env("OPENAI_API_KEY", ""),
        },
        "flask": {
            "SQLALCHEMY_DATABASE_URI": _get_env("SQLALCHEMY_DATABASE_URI", ""),
            "DEBUG": _get_env_boolean("DEBUG", True),
        },
        "mail": {
            "MAIL_SERVER": _get_env("MAIL_SERVER", ""),
            "MAIL_PORT": _get_env_integer("MAIL_PORT", 2525),
            "MAIL_USE_TLS": _get_env_boolean("MAIL_USE_TLS", True),
            "MAIL_USE_SSL": _get_env_boolean("MAIL_USE_SSL", False),
            "MAIL_USERNAME": _get_env("MAIL_USERNAME", ""),
            "MAIL_PASSWORD": _get_env("MAIL_PASSWORD", ""),
            "MAIL_DEFAULT_SENDER": _get_env(
                "MAIL_DEFAULT_SENDER", "info@questbycycle.org"
            ),
        },
        "social": {
            "twitter_username": _get_env("TWITTER_USERNAME", ""),
            "twitter_api_key": _get_env("TWITTER_API_KEY", ""),
            "twitter_api_secret": _get_env("TWITTER_API_SECRET", ""),
            "twitter_access_token": _get_env("TWITTER_ACCESS_TOKEN", ""),
            "twitter_access_token_secret": _get_env("TWITTER_ACCESS_TOKEN_SECRET", ""),
            "facebook_app_id": _get_env("FACEBOOK_APP_ID", ""),
            "facebook_app_secret": _get_env("FACEBOOK_APP_SECRET", ""),
            "facebook_access_token": _get_env("FACEBOOK_ACCESS_TOKEN", ""),
            "facebook_page_id": _get_env("FACEBOOK_PAGE_ID", ""),
            "instagram_access_token": _get_env("INSTAGRAM_ACCESS_TOKEN", ""),
            "instagram_user_id": _get_env("INSTAGRAM_USER_ID", ""),
        },
        "push": {
            "VAPID_PUBLIC_KEY": _get_env("VAPID_PUBLIC_KEY", ""),
            "VAPID_PRIVATE_KEY": _get_env("VAPID_PRIVATE_KEY", ""),
            "VAPID_ADMIN_EMAIL": _get_env("VAPID_ADMIN_EMAIL", "push@example.com"),
        },
        "redis": {
            "REDIS_URL": _get_env("REDIS_URL", "redis://localhost:6379/0"),
        },
        "twa": {
            "SHA256_CERT_FINGERPRINT": _get_env("TWA_SHA256_FINGERPRINT", ""),
        },
        "sqlalchemy_engine_options": {
            "pool_pre_ping": True,
            "pool_recycle": 3300,
        },
    }

    return cfg


SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 3300,
}
