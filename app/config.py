# =============================================================================
# app/config.py
#
# Revised to read environment variables first (via python‐dotenv),
# then fall back to values from "config/config.toml".
# =============================================================================

import os
import toml
from pathlib import Path
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# 1. Determine the path to the TOML file and the .env file.
# -----------------------------------------------------------------------------
# We assume:
#   - config/config.toml  (static, version‐controlled)
#   - .env (in the project root, not version‐controlled)
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent  # e.g., "<project_root>/app"
PROJECT_ROOT = BASE_DIR.parent              # "<project_root>"
ENV_PATH = PROJECT_ROOT / ".env"
TOML_PATH = PROJECT_ROOT / "config.toml"

# -----------------------------------------------------------------------------
# 2. Load environment variables from ".env" if it exists.
# -----------------------------------------------------------------------------
# This call populates os.environ with keys found in the .env file.
# If no .env is present, it silently does nothing.
# -----------------------------------------------------------------------------
load_dotenv(dotenv_path=ENV_PATH)

# -----------------------------------------------------------------------------
# 3. Helper functions to coerce types when reading from environment.
# -----------------------------------------------------------------------------
def _get_env(key: str, default=None):
    """
    Retrieves the environment variable 'key'. If not set, returns 'default'.
    """
    return os.getenv(key, default)

def _get_env_boolean(key: str, default: bool):
    """
    Retrieves a boolean environment variable. If the value is one of
    'true', 'True', '1', 'yes', 'YES', returns True. Otherwise, if
    'false', 'False', '0', 'no', 'NO', returns False. If not in environment,
    returns the default.
    """
    val = os.getenv(key)
    if val is None:
        return default
    return val.lower() in ("true", "1", "yes")

def _get_env_integer(key: str, default: int):
    """
    Retrieves an integer environment variable. If not set or invalid,
    returns the default.
    """
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default

# -----------------------------------------------------------------------------
# 4. Load the TOML file into a dictionary. If it is missing, error out.
# -----------------------------------------------------------------------------
if not TOML_PATH.exists():
    raise FileNotFoundError(f"Configuration file not found at {TOML_PATH}")

_toml_config = toml.load(TOML_PATH)

# -----------------------------------------------------------------------------
# 5. Now build a new config dictionary, where each section’s keys
#    prefer environment variables and fall back to TOML.
# -----------------------------------------------------------------------------
def load_config():
    """
    Returns a dictionary structured like the TOML (with sections), but
    values are pulled from the environment when available.
    """
    cfg = {
        "main": {
            "UPLOAD_FOLDER": _get_env("UPLOAD_FOLDER", _toml_config["main"]["UPLOAD_FOLDER"]),
            "VERIFICATIONS": _get_env("VERIFICATIONS", _toml_config["main"]["VERIFICATIONS"]),
            "BADGE_IMAGE_DIR": _get_env("BADGE_IMAGE_DIR", _toml_config["main"]["BADGE_IMAGE_DIR"]),
            "TASKCSV": _get_env("TASKCSV", _toml_config["main"]["TASKCSV"]),
            "LOCAL_DOMAIN": _get_env("LOCAL_DOMAIN", _toml_config["main"]["LOCAL_DOMAIN"]),
        },
        "encryption": {
            "DEFAULT_SUPER_ADMIN_USERNAME": _get_env("DEFAULT_SUPER_ADMIN_USERNAME",
                                                     _toml_config["encryption"]["DEFAULT_SUPER_ADMIN_USERNAME"]),
            "DEFAULT_SUPER_ADMIN_PASSWORD": _get_env("DEFAULT_SUPER_ADMIN_PASSWORD",
                                                     _toml_config["encryption"]["DEFAULT_SUPER_ADMIN_PASSWORD"]),
            "DEFAULT_SUPER_ADMIN_EMAIL": _get_env("DEFAULT_SUPER_ADMIN_EMAIL",
                                                  _toml_config["encryption"]["DEFAULT_SUPER_ADMIN_EMAIL"]),
            "SECRET_KEY": _get_env("SECRET_KEY", _toml_config["encryption"]["SECRET_KEY"]),
            "SESSION_COOKIE_SECURE": _get_env_boolean("SESSION_COOKIE_SECURE",
                                                      _toml_config["encryption"]["SESSION_COOKIE_SECURE"]),
            "SESSION_COOKIE_NAME": _get_env("SESSION_COOKIE_NAME",
                                           _toml_config["encryption"]["SESSION_COOKIE_NAME"]),
            "SESSION_COOKIE_SAMESITE": _get_env("SESSION_COOKIE_SAMESITE",
                                                _toml_config["encryption"]["SESSION_COOKIE_SAMESITE"]),
            "SESSION_COOKIE_DOMAIN": _get_env("SESSION_COOKIE_DOMAIN",
                                             _toml_config["encryption"]["SESSION_COOKIE_DOMAIN"]),
            "SESSION_REFRESH_EACH_REQUEST": _get_env_boolean("SESSION_REFRESH_EACH_REQUEST",
                                                            _toml_config["encryption"]["SESSION_REFRESH_EACH_REQUEST"]),
            "REMEMBER_COOKIE_DURATION_DAYS": _get_env_integer("REMEMBER_COOKIE_DURATION_DAYS",
                                                              _toml_config["encryption"]["REMEMBER_COOKIE_DURATION_DAYS"]),
        },
        "openai": {
            "OPENAI_API_KEY": _get_env("OPENAI_API_KEY", _toml_config["openai"]["OPENAI_API_KEY"]),
        },
        "flask": {
            # The DATABASE URI is almost always environment‐specific and contains secrets.
            "SQLALCHEMY_DATABASE_URI": _get_env("SQLALCHEMY_DATABASE_URI",
                                               _toml_config["flask"]["SQLALCHEMY_DATABASE_URI"]),
            "DEBUG": _get_env_boolean("DEBUG", _toml_config["flask"]["DEBUG"]),
        },
        "mail": {
            "MAIL_SERVER": _get_env("MAIL_SERVER", _toml_config["mail"]["MAIL_SERVER"]),
            "MAIL_PORT": _get_env_integer("MAIL_PORT", _toml_config["mail"]["MAIL_PORT"]),
            "MAIL_USE_TLS": _get_env_boolean("MAIL_USE_TLS", _toml_config["mail"]["MAIL_USE_TLS"]),
            "MAIL_USE_SSL": _get_env_boolean("MAIL_USE_SSL", _toml_config["mail"]["MAIL_USE_SSL"]),
            "MAIL_USERNAME": _get_env("MAIL_USERNAME", _toml_config["mail"]["MAIL_USERNAME"]),
            "MAIL_PASSWORD": _get_env("MAIL_PASSWORD", _toml_config["mail"]["MAIL_PASSWORD"]),
            "MAIL_DEFAULT_SENDER": _get_env("MAIL_DEFAULT_SENDER", _toml_config["mail"]["MAIL_DEFAULT_SENDER"]),
        },
        "social": {
            "twitter_username": _get_env("TWITTER_USERNAME", _toml_config["social"]["twitter_username"]),
            "twitter_api_key": _get_env("TWITTER_API_KEY", _toml_config["social"]["twitter_api_key"]),
            "twitter_api_secret": _get_env("TWITTER_API_SECRET", _toml_config["social"]["twitter_api_secret"]),
            "twitter_access_token": _get_env("TWITTER_ACCESS_TOKEN", _toml_config["social"]["twitter_access_token"]),
            "twitter_access_token_secret": _get_env("TWITTER_ACCESS_TOKEN_SECRET",
                                                    _toml_config["social"]["twitter_access_token_secret"]),
            "facebook_app_id": _get_env("FACEBOOK_APP_ID", _toml_config["social"]["facebook_app_id"]),
            "facebook_app_secret": _get_env("FACEBOOK_APP_SECRET", _toml_config["social"]["facebook_app_secret"]),
            "facebook_access_token": _get_env("FACEBOOK_ACCESS_TOKEN", _toml_config["social"]["facebook_access_token"]),
            "facebook_page_id": _get_env("FACEBOOK_PAGE_ID", _toml_config["social"]["facebook_page_id"]),
            "instagram_access_token": _get_env("INSTAGRAM_ACCESS_TOKEN",
                                               _toml_config["social"]["instagram_access_token"]),
            "instagram_user_id": _get_env("INSTAGRAM_USER_ID", _toml_config["social"]["instagram_user_id"]),
        },
        "socketio": {
            "SERVER_URL": _get_env("SOCKETIO_SERVER_URL", _toml_config["socketio"]["SERVER_URL"]),
        },
        "sqlalchemy_engine_options": {
            # We preserve pool_pre_ping and pool_recycle exactly as in TOML;
            # typically these are not overridden in environment.
            "pool_pre_ping": _toml_config["sqlalchemy_engine_options"]["pool_pre_ping"],
            "pool_recycle": _toml_config["sqlalchemy_engine_options"]["pool_recycle"],
        },
    }

    return cfg

# Expose the SQLALCHEMY_ENGINE_OPTIONS as a top‐level variable (for direct import)
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 3300  # seconds; or you could use cfg['sqlalchemy_engine_options']['pool_recycle']
}
