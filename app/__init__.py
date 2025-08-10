import logging
import os
import atexit

from flask import (
    current_app,
    Flask,
    render_template,
    flash,
    redirect,
    url_for,
    jsonify,
    request,
)
from urllib.parse import urlparse, urlunparse
from flask_login import LoginManager, current_user
from werkzeug.exceptions import HTTPException

from app.auth import auth_bp
from app.admin import admin_bp, create_super_admin
from app.main import main_bp
from app.games import games_bp
from app.quests import quests_bp
from app.badges import badges_bp
from app.profile import profile_bp
from app.webfinger import webfinger_bp
from app.notifications import notifications_bp
from app.push import push_bp
from .scheduler import create_scheduler, shutdown_scheduler
from app.tasks import init_queue
from app.activitypub_utils import ap_bp
from app.ai import ai_bp
from app.models import db
from .config import load_config
from flask_wtf.csrf import CSRFProtect, CSRFError
from datetime import timedelta
from logging.handlers import RotatingFileHandler
from flask_humanify import Humanify

                        
                            
                        
login_manager = LoginManager()
csrf = CSRFProtect()
# Use a grid-based challenge to make automated registrations harder.
humanify = Humanify(challenge_type="one_click")

                        
                
                        
if not os.path.exists("logs"):
    os.mkdir("logs")

log_level = logging.DEBUG if os.getenv("FLASK_DEBUG") or os.getenv("DEBUG") else logging.INFO

logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        RotatingFileHandler("logs/application.log", maxBytes=10240, backupCount=10),
        logging.StreamHandler(),
    ],
    force=True,
)
logger = logging.getLogger(__name__)

                        
                   
                        
_original_url_for = url_for

def _url_for(*args, **kwargs):
    try:
        url = _original_url_for(*args, **kwargs)
    except RuntimeError:
        app = current_app._get_current_object()
        with app.test_request_context():
            url = _original_url_for(*args, **kwargs)

    app = current_app._get_current_object()
    if app.config.get("TESTING"):
        p = urlparse(url)
        return urlunparse(("", "", p.path, p.params, p.query, p.fragment))
    return url

                        
                      
                        
def create_app(config_overrides=None):
    app = Flask(__name__)

                                   
    inscopeconfig = load_config()

                                                    
    app.config.update({
        "SECRET_KEY": inscopeconfig.encryption.SECRET_KEY,
        "SQLALCHEMY_DATABASE_URI": inscopeconfig.flask.SQLALCHEMY_DATABASE_URI,
        "DEBUG": inscopeconfig.flask.DEBUG,
        "SQLALCHEMY_ECHO": inscopeconfig.main.SQLALCHEMY_ECHO,
        "SESSION_COOKIE_SECURE": inscopeconfig.encryption.SESSION_COOKIE_SECURE,
        "SESSION_COOKIE_NAME": inscopeconfig.encryption.SESSION_COOKIE_NAME,
        "SESSION_COOKIE_SAMESITE": inscopeconfig.encryption.SESSION_COOKIE_SAMESITE,
        "SESSION_COOKIE_DOMAIN": inscopeconfig.encryption.SESSION_COOKIE_DOMAIN,
        "SESSION_REFRESH_EACH_REQUEST": inscopeconfig.encryption.SESSION_REFRESH_EACH_REQUEST,
        "REMEMBER_COOKIE_DURATION": timedelta(days=inscopeconfig.encryption.REMEMBER_COOKIE_DURATION_DAYS),
        "UPLOAD_FOLDER": inscopeconfig.main.UPLOAD_FOLDER,
        "VERIFICATIONS": inscopeconfig.main.VERIFICATIONS,
        "BADGE_IMAGE_DIR": inscopeconfig.main.BADGE_IMAGE_DIR,
        "TASKCSV": inscopeconfig.main.TASKCSV,
        "LOCAL_DOMAIN": inscopeconfig.main.LOCAL_DOMAIN,
        "FFMPEG_PATH": inscopeconfig.main.FFMPEG_PATH,
        "PLACEHOLDER_IMAGE": inscopeconfig.main.PLACEHOLDER_IMAGE,
        "GCS_BUCKET": inscopeconfig.main.GCS_BUCKET,
        "GCS_BASE_URL": inscopeconfig.main.GCS_BASE_URL,
        "GCS_STORAGE_CLASS": inscopeconfig.main.GCS_STORAGE_CLASS,
        "ASSET_VERSION": inscopeconfig.main.ASSET_VERSION,
        "MAIL_SERVER": inscopeconfig.mail.MAIL_SERVER,
        "MAIL_PORT": inscopeconfig.mail.MAIL_PORT,
        "MAIL_USE_SSL": inscopeconfig.mail.MAIL_USE_SSL,
        "MAIL_USE_TLS": inscopeconfig.mail.MAIL_USE_TLS,
        "MAIL_USERNAME": inscopeconfig.mail.MAIL_USERNAME,
        "MAIL_PASSWORD": inscopeconfig.mail.MAIL_PASSWORD,
        "MAIL_DEFAULT_SENDER": inscopeconfig.mail.MAIL_DEFAULT_SENDER,
        "OPENAI_API_KEY": inscopeconfig.openai.OPENAI_API_KEY,
        "TWITTER_USERNAME": inscopeconfig.social.twitter_username,
        "TWITTER_API_KEY": inscopeconfig.social.twitter_api_key,
        "TWITTER_API_SECRET": inscopeconfig.social.twitter_api_secret,
        "TWITTER_ACCESS_TOKEN": inscopeconfig.social.twitter_access_token,
        "TWITTER_ACCESS_TOKEN_SECRET": inscopeconfig.social.twitter_access_token_secret,
        "FACEBOOK_APP_ID": inscopeconfig.social.facebook_app_id,
        "FACEBOOK_APP_SECRET": inscopeconfig.social.facebook_app_secret,
        "FACEBOOK_ACCESS_TOKEN": inscopeconfig.social.facebook_access_token,
        "FACEBOOK_PAGE_ID": inscopeconfig.social.facebook_page_id,
        "INSTAGRAM_ACCESS_TOKEN": inscopeconfig.social.instagram_access_token,
        "INSTAGRAM_USER_ID": inscopeconfig.social.instagram_user_id,
        "TWA_SHA256_FINGERPRINT": inscopeconfig.twa.SHA256_CERT_FINGERPRINT,
        "WTF_CSRF_ENABLED": not inscopeconfig.flask.DEBUG,
        "VAPID_PUBLIC_KEY":  inscopeconfig.push.VAPID_PUBLIC_KEY,
        "VAPID_PRIVATE_KEY": inscopeconfig.push.VAPID_PRIVATE_KEY,
        "VAPID_ADMIN_EMAIL": inscopeconfig.push.VAPID_ADMIN_EMAIL,
        "PAYPAL_CLIENT_ID": inscopeconfig.paypal.PAYPAL_CLIENT_ID,
        "PAYPAL_CLIENT_SECRET": inscopeconfig.paypal.PAYPAL_CLIENT_SECRET,
        "PAYPAL_API_BASE": inscopeconfig.paypal.PAYPAL_API_BASE,
        "DEFAULT_SUPER_ADMIN_USERNAME": inscopeconfig.encryption.DEFAULT_SUPER_ADMIN_USERNAME,
        "DEFAULT_SUPER_ADMIN_PASSWORD": inscopeconfig.encryption.DEFAULT_SUPER_ADMIN_PASSWORD,
        "DEFAULT_SUPER_ADMIN_EMAIL": inscopeconfig.encryption.DEFAULT_SUPER_ADMIN_EMAIL,
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_pre_ping": inscopeconfig.sqlalchemy_engine_options.pool_pre_ping,
            "pool_recycle": inscopeconfig.sqlalchemy_engine_options.pool_recycle,
        },
    })

    if config_overrides:
        app.config.update(config_overrides)

    if app.config.get("TESTING") and not app.config.get("SERVER_NAME"):
        app.config["SERVER_NAME"] = "localhost:5000"
        app.config.setdefault("USE_TASK_QUEUE", False)
    else:
        app.config.setdefault("SERVER_NAME", inscopeconfig.main.LOCAL_DOMAIN)
        app.config.setdefault("PREFERRED_URL_SCHEME", "http")

                              
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    if not app.config.get("TESTING"):
        humanify.init_app(app)
        humanify.register_middleware(
            action="challenge",
            endpoint_patterns=["auth.login", "auth.register"],
        )

                                                
    with app.app_context():
        db.create_all()
        create_super_admin(app)
        init_queue(app)

                            
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(ai_bp, url_prefix="/ai")
    app.register_blueprint(games_bp, url_prefix="/games")
    app.register_blueprint(quests_bp, url_prefix="/quests")
    app.register_blueprint(badges_bp, url_prefix="/badges")
    app.register_blueprint(profile_bp, url_prefix="/profile")
    app.register_blueprint(ap_bp, url_prefix="/users")
    app.register_blueprint(notifications_bp, url_prefix="/notifications")
    app.register_blueprint(push_bp, url_prefix="/push")
    app.register_blueprint(webfinger_bp)
    app.register_blueprint(main_bp)

    csrf.exempt(ap_bp)
    login_manager.login_view = "auth.login"

    @login_manager.unauthorized_handler
    def unauthorized_callback():
        """Return JSON response for unauthorized AJAX requests."""
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.accept_json:
            return jsonify({"error": "Unauthorized"}), 401
        return redirect(url_for("auth.login", next=request.url))

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import db
        from app.models.user import User
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            logger.error("Invalid user_id in session: %s", user_id)
            return None

    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning("404 error at %s: %s", request.path, error)
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error: {error}")
        db.session.rollback()
        return render_template("500.html"), 500

    @app.errorhandler(429)
    def too_many_requests(e):
        logger.warning(f"429 error: {e}")
        return render_template("429.html"), 429

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        logger.warning(
            "CSRF failure on %s: %s form=%s headers=%s",
            request.path,
            e.description,
            dict(request.form),
            {k: v for k, v in request.headers.items() if k.startswith('X-CSRF')},
        )
        return jsonify(success=False, message="CSRF token missing or incorrect"), 400

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return e
        logger.error(f"Unhandled Exception: {e}")
        flash("An unexpected error occurred. Please try again later.", "error")
        return redirect(url_for("main.index"))

    @app.context_processor
    def inject_logout_form():
        from app.forms import LogoutForm
        placeholder_url = url_for(
            'static', filename=current_app.config['PLACEHOLDER_IMAGE']
        )
        return dict(
            logout_form=LogoutForm(),
            placeholder_image=placeholder_url,
        )


    @app.context_processor
    def inject_selected_game_id():
        if current_user.is_authenticated:
            return dict(selected_game_id=current_user.selected_game_id or 0)
        else:
            return dict(selected_game_id=None)

    @app.context_processor
    def inject_asset_version():
        return dict(asset_version=current_app.config["ASSET_VERSION"])

    if not (app.debug and os.environ.get("WERKZEUG_RUN_MAIN") is None):
        create_scheduler(app)
        atexit.register(lambda: shutdown_scheduler(app, wait=False))

    return app
