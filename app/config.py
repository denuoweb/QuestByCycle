import os
import tomli
from pathlib import Path
from dotenv import load_dotenv

                                                                               
                                                         
                                                                               
BASE_DIR = Path(__file__).resolve().parent                                   
PROJECT_ROOT = BASE_DIR.parent                                     
ENV_PATH = PROJECT_ROOT / ".env"
TOML_PATH = PROJECT_ROOT / "config.toml"
DEFAULT_TOML_PATH = PROJECT_ROOT / "config.toml.example"

                                                                               
                                                         
                                                                               
                                                                        
load_dotenv(dotenv_path=ENV_PATH)

                                                                               
                                                                    
                                                                               
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

def _get_env_nullable(key: str, default=None):
    """Retrieve an environment variable but return ``None`` for falsey values."""
    val = os.getenv(key)
    if val is None:
        val = default
    if val in (False, "", "false", "False", None):
        return None
    return val

                                                                               
                                                                       
                                                                               
if TOML_PATH.exists():
    with open(TOML_PATH, "rb") as f:
        _toml_config = tomli.load(f)
elif DEFAULT_TOML_PATH.exists():
    with open(DEFAULT_TOML_PATH, "rb") as f:
        _toml_config = tomli.load(f)
else:
    _toml_config = {}

                                                                               
                                                                              
                                                                               
def load_config():
    """
    Returns a dictionary with the same structure as the TOML file, but with
    values overridden by environment variables when present.
    """
                                                                     
                                            
    sq_opts = _toml_config.get("sqlalchemy_engine_options", {})

                                                                                            
    cfg = {
        "main": {
            "UPLOAD_FOLDER": _get_env("UPLOAD_FOLDER", _toml_config["main"]["UPLOAD_FOLDER"]),
            "VERIFICATIONS": _get_env("VERIFICATIONS", _toml_config["main"]["VERIFICATIONS"]),
            "BADGE_IMAGE_DIR": _get_env("BADGE_IMAGE_DIR", _toml_config["main"]["BADGE_IMAGE_DIR"]),
            "TASKCSV": _get_env("TASKCSV", _toml_config["main"]["TASKCSV"]),
            "LOCAL_DOMAIN": _get_env("LOCAL_DOMAIN", _toml_config["main"]["LOCAL_DOMAIN"]),
            "FFMPEG_PATH": _get_env("FFMPEG_PATH", _toml_config["main"].get("FFMPEG_PATH", "ffmpeg")),
            "PLACEHOLDER_IMAGE": _get_env(
                "PLACEHOLDER_IMAGE",
                _toml_config["main"].get("PLACEHOLDER_IMAGE", "images/default-placeholder.webp"),
            ),
        },
        "encryption": {
            "DEFAULT_SUPER_ADMIN_USERNAME": _get_env(
                "DEFAULT_SUPER_ADMIN_USERNAME",
                _toml_config["encryption"]["DEFAULT_SUPER_ADMIN_USERNAME"]
            ),
            "DEFAULT_SUPER_ADMIN_PASSWORD": _get_env(
                "DEFAULT_SUPER_ADMIN_PASSWORD",
                _toml_config["encryption"]["DEFAULT_SUPER_ADMIN_PASSWORD"]
            ),
            "DEFAULT_SUPER_ADMIN_EMAIL": _get_env(
                "DEFAULT_SUPER_ADMIN_EMAIL",
                _toml_config["encryption"]["DEFAULT_SUPER_ADMIN_EMAIL"]
            ),
            "SECRET_KEY": _get_env("SECRET_KEY", _toml_config["encryption"]["SECRET_KEY"]),
            "SESSION_COOKIE_SECURE": _get_env_boolean(
                "SESSION_COOKIE_SECURE",
                _toml_config["encryption"]["SESSION_COOKIE_SECURE"]
            ),
            "SESSION_COOKIE_NAME": _get_env(
                "SESSION_COOKIE_NAME",
                _toml_config["encryption"]["SESSION_COOKIE_NAME"]
            ),
            "SESSION_COOKIE_SAMESITE": _get_env(
                "SESSION_COOKIE_SAMESITE",
                _toml_config["encryption"]["SESSION_COOKIE_SAMESITE"]
            ),
            "SESSION_COOKIE_DOMAIN": _get_env_nullable(
                "SESSION_COOKIE_DOMAIN",
                _toml_config["encryption"]["SESSION_COOKIE_DOMAIN"]
            ),
            "SESSION_REFRESH_EACH_REQUEST": _get_env_boolean(
                "SESSION_REFRESH_EACH_REQUEST",
                _toml_config["encryption"]["SESSION_REFRESH_EACH_REQUEST"]
            ),
            "REMEMBER_COOKIE_DURATION_DAYS": _get_env_integer(
                "REMEMBER_COOKIE_DURATION_DAYS",
                _toml_config["encryption"]["REMEMBER_COOKIE_DURATION_DAYS"]
            ),
        },
        "openai": {
            "OPENAI_API_KEY": _get_env(
                "OPENAI_API_KEY",
                _toml_config["openai"]["OPENAI_API_KEY"]
            ),
        },
        "flask": {
                                                                       
            "SQLALCHEMY_DATABASE_URI": _get_env(
                "SQLALCHEMY_DATABASE_URI",
                _toml_config["flask"]["SQLALCHEMY_DATABASE_URI"]
            ),
            "DEBUG": _get_env_boolean("DEBUG", _toml_config["flask"]["DEBUG"]),
        },
        "mail": {
            "MAIL_SERVER": _get_env("MAIL_SERVER", _toml_config["mail"]["MAIL_SERVER"]),
            "MAIL_PORT": _get_env_integer("MAIL_PORT", _toml_config["mail"]["MAIL_PORT"]),
            "MAIL_USE_TLS": _get_env_boolean("MAIL_USE_TLS", _toml_config["mail"]["MAIL_USE_TLS"]),
            "MAIL_USE_SSL": _get_env_boolean("MAIL_USE_SSL", _toml_config["mail"]["MAIL_USE_SSL"]),
            "MAIL_USERNAME": _get_env("MAIL_USERNAME", _toml_config["mail"]["MAIL_USERNAME"]),
            "MAIL_PASSWORD": _get_env("MAIL_PASSWORD", _toml_config["mail"]["MAIL_PASSWORD"]),
            "MAIL_DEFAULT_SENDER": _get_env(
                "MAIL_DEFAULT_SENDER",
                _toml_config["mail"]["MAIL_DEFAULT_SENDER"]
            ),
        },
        "social": {
            "twitter_username": _get_env("TWITTER_USERNAME", _toml_config["social"]["twitter_username"]),
            "twitter_api_key": _get_env("TWITTER_API_KEY", _toml_config["social"]["twitter_api_key"]),
            "twitter_api_secret": _get_env("TWITTER_API_SECRET", _toml_config["social"]["twitter_api_secret"]),
            "twitter_access_token": _get_env("TWITTER_ACCESS_TOKEN", _toml_config["social"]["twitter_access_token"]),
            "twitter_access_token_secret": _get_env(
                "TWITTER_ACCESS_TOKEN_SECRET",
                _toml_config["social"]["twitter_access_token_secret"]
            ),
            "facebook_app_id": _get_env("FACEBOOK_APP_ID", _toml_config["social"]["facebook_app_id"]),
            "facebook_app_secret": _get_env("FACEBOOK_APP_SECRET", _toml_config["social"]["facebook_app_secret"]),
            "facebook_access_token": _get_env("FACEBOOK_ACCESS_TOKEN", _toml_config["social"]["facebook_access_token"]),
            "facebook_page_id": _get_env("FACEBOOK_PAGE_ID", _toml_config["social"]["facebook_page_id"]),
            "instagram_access_token": _get_env("INSTAGRAM_ACCESS_TOKEN", _toml_config["social"]["instagram_access_token"]),
            "instagram_user_id": _get_env("INSTAGRAM_USER_ID", _toml_config["social"]["instagram_user_id"]),
        },

        "push": {
            "VAPID_PUBLIC_KEY": _get_env("VAPID_PUBLIC_KEY", _toml_config.get("push", {}).get("VAPID_PUBLIC_KEY", "")),
            "VAPID_PRIVATE_KEY": _get_env("VAPID_PRIVATE_KEY", _toml_config.get("push", {}).get("VAPID_PRIVATE_KEY", "")),
            "VAPID_ADMIN_EMAIL": _get_env("VAPID_ADMIN_EMAIL", _toml_config.get("push", {}).get("VAPID_ADMIN_EMAIL", "push@example.com")),
        },

        "twa": {
            "SHA256_CERT_FINGERPRINT": _get_env(
                "TWA_SHA256_FINGERPRINT",
                _toml_config.get("twa", {}).get("SHA256_CERT_FINGERPRINT", ""),
            ),
        },
 
                                                                                       
                                                                                       
                                                                                       
        "sqlalchemy_engine_options": {
            "pool_pre_ping": sq_opts.get("pool_pre_ping", True),
            "pool_recycle": sq_opts.get("pool_recycle", 3300),
        },
    }

    return cfg

                                                                               
                                                                         
                                                                                    
                                                                               
SQLALCHEMY_ENGINE_OPTIONS = {
                                                                 
                                                                                      
    "pool_pre_ping": True,
    "pool_recycle": 3300,
}