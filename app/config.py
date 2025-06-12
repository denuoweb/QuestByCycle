"""Configuration loader using environment variables.

This module exposes :func:`load_config` which returns a structured
``AppConfig`` instance composed of dataclasses for each configuration
section.  Using dataclasses provides type hints and an easy way to
access configuration values without deep dictionary lookups.
"""

from pathlib import Path
from dataclasses import dataclass
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


@dataclass
class MainConfig:
    """Configuration options for general application behavior."""

    UPLOAD_FOLDER: str
    VERIFICATIONS: str
    BADGE_IMAGE_DIR: str
    TASKCSV: str
    LOCAL_DOMAIN: str
    FFMPEG_PATH: str
    PLACEHOLDER_IMAGE: str
    SQLALCHEMY_ECHO: bool
    GCS_BUCKET: str | None
    GCS_BASE_URL: str | None
    GCS_STORAGE_CLASS: str


@dataclass
class EncryptionConfig:
    """Security and session related configuration."""

    DEFAULT_SUPER_ADMIN_USERNAME: str
    DEFAULT_SUPER_ADMIN_PASSWORD: str
    DEFAULT_SUPER_ADMIN_EMAIL: str
    SECRET_KEY: str
    SESSION_COOKIE_SECURE: bool
    SESSION_COOKIE_NAME: str
    SESSION_COOKIE_SAMESITE: str
    SESSION_COOKIE_DOMAIN: str | None
    SESSION_REFRESH_EACH_REQUEST: bool
    REMEMBER_COOKIE_DURATION_DAYS: int


@dataclass
class OpenAIConfig:
    OPENAI_API_KEY: str


@dataclass
class FlaskConfig:
    SQLALCHEMY_DATABASE_URI: str
    DEBUG: bool


@dataclass
class MailConfig:
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_USE_TLS: bool
    MAIL_USE_SSL: bool
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_DEFAULT_SENDER: str


@dataclass
class SocialConfig:
    twitter_username: str
    twitter_api_key: str
    twitter_api_secret: str
    twitter_access_token: str
    twitter_access_token_secret: str
    facebook_app_id: str
    facebook_app_secret: str
    facebook_access_token: str
    facebook_page_id: str
    instagram_access_token: str
    instagram_user_id: str


@dataclass
class PushConfig:
    VAPID_PUBLIC_KEY: str
    VAPID_PRIVATE_KEY: str
    VAPID_ADMIN_EMAIL: str


@dataclass
class TWAConfig:
    SHA256_CERT_FINGERPRINT: str


@dataclass
class SQLAlchemyEngineOptions:
    pool_pre_ping: bool
    pool_recycle: int


@dataclass
class AppConfig:
    main: MainConfig
    encryption: EncryptionConfig
    openai: OpenAIConfig
    flask: FlaskConfig
    mail: MailConfig
    social: SocialConfig
    push: PushConfig
    twa: TWAConfig
    sqlalchemy_engine_options: SQLAlchemyEngineOptions


def load_config() -> AppConfig:
    """Build configuration using environment variables with reasonable defaults."""

    return AppConfig(
        main=MainConfig(
            UPLOAD_FOLDER=_get_env("UPLOAD_FOLDER", "images"),
            VERIFICATIONS=_get_env("VERIFICATIONS", "verifications"),
            BADGE_IMAGE_DIR=_get_env("BADGE_IMAGE_DIR", "badge_images"),
            TASKCSV=_get_env("TASKCSV", "csv"),
            LOCAL_DOMAIN=_get_env("LOCAL_DOMAIN", "localhost:5000"),
            FFMPEG_PATH=_get_env("FFMPEG_PATH", "ffmpeg"),
            PLACEHOLDER_IMAGE=_get_env("PLACEHOLDER_IMAGE", "images/default-placeholder.webp"),
            SQLALCHEMY_ECHO=_get_env_boolean("SQLALCHEMY_ECHO", False),
            GCS_BUCKET=_get_env_nullable("GCS_BUCKET"),
            GCS_BASE_URL=_get_env_nullable("GCS_BASE_URL"),
            GCS_STORAGE_CLASS=_get_env("GCS_STORAGE_CLASS", "ARCHIVE"),
        ),
        encryption=EncryptionConfig(
            DEFAULT_SUPER_ADMIN_USERNAME=_get_env("DEFAULT_SUPER_ADMIN_USERNAME", "test"),
            DEFAULT_SUPER_ADMIN_PASSWORD=_get_env("DEFAULT_SUPER_ADMIN_PASSWORD", "test"),
            DEFAULT_SUPER_ADMIN_EMAIL=_get_env("DEFAULT_SUPER_ADMIN_EMAIL", "test@test.com"),
            SECRET_KEY=_get_env("SECRET_KEY", "replace this key"),
            SESSION_COOKIE_SECURE=_get_env_boolean("SESSION_COOKIE_SECURE", False),
            SESSION_COOKIE_NAME=_get_env("SESSION_COOKIE_NAME", "QuestsByCycles_Session"),
            SESSION_COOKIE_SAMESITE=_get_env("SESSION_COOKIE_SAMESITE", "Lax"),
            SESSION_COOKIE_DOMAIN=_get_env_nullable("SESSION_COOKIE_DOMAIN", False),
            SESSION_REFRESH_EACH_REQUEST=_get_env_boolean("SESSION_REFRESH_EACH_REQUEST", True),
            REMEMBER_COOKIE_DURATION_DAYS=_get_env_integer("REMEMBER_COOKIE_DURATION_DAYS", 7),
        ),
        openai=OpenAIConfig(
            OPENAI_API_KEY=_get_env("OPENAI_API_KEY", ""),
        ),
        flask=FlaskConfig(
            SQLALCHEMY_DATABASE_URI=_get_env("SQLALCHEMY_DATABASE_URI", ""),
            DEBUG=_get_env_boolean("DEBUG", True),
        ),
        mail=MailConfig(
            MAIL_SERVER=_get_env("MAIL_SERVER", ""),
            MAIL_PORT=_get_env_integer("MAIL_PORT", 2525),
            MAIL_USE_TLS=_get_env_boolean("MAIL_USE_TLS", True),
            MAIL_USE_SSL=_get_env_boolean("MAIL_USE_SSL", False),
            MAIL_USERNAME=_get_env("MAIL_USERNAME", ""),
            MAIL_PASSWORD=_get_env("MAIL_PASSWORD", ""),
            MAIL_DEFAULT_SENDER=_get_env("MAIL_DEFAULT_SENDER", "info@questbycycle.org"),
        ),
        social=SocialConfig(
            twitter_username=_get_env("TWITTER_USERNAME", ""),
            twitter_api_key=_get_env("TWITTER_API_KEY", ""),
            twitter_api_secret=_get_env("TWITTER_API_SECRET", ""),
            twitter_access_token=_get_env("TWITTER_ACCESS_TOKEN", ""),
            twitter_access_token_secret=_get_env("TWITTER_ACCESS_TOKEN_SECRET", ""),
            facebook_app_id=_get_env("FACEBOOK_APP_ID", ""),
            facebook_app_secret=_get_env("FACEBOOK_APP_SECRET", ""),
            facebook_access_token=_get_env("FACEBOOK_ACCESS_TOKEN", ""),
            facebook_page_id=_get_env("FACEBOOK_PAGE_ID", ""),
            instagram_access_token=_get_env("INSTAGRAM_ACCESS_TOKEN", ""),
            instagram_user_id=_get_env("INSTAGRAM_USER_ID", ""),
        ),
        push=PushConfig(
            VAPID_PUBLIC_KEY=_get_env("VAPID_PUBLIC_KEY", ""),
            VAPID_PRIVATE_KEY=_get_env("VAPID_PRIVATE_KEY", ""),
            VAPID_ADMIN_EMAIL=_get_env("VAPID_ADMIN_EMAIL", "push@example.com"),
        ),
        twa=TWAConfig(
            SHA256_CERT_FINGERPRINT=_get_env("TWA_SHA256_FINGERPRINT", ""),
        ),
        sqlalchemy_engine_options=SQLAlchemyEngineOptions(
            pool_pre_ping=True,
            pool_recycle=3300,
        ),
    )

SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 3300,
}
