"""Utility package exposing helpers across the application."""
from __future__ import annotations

import csv
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse

from flask import current_app, request, url_for
from html_sanitizer import Sanitizer
from sqlalchemy.exc import SQLAlchemyError

from ..models import (
    db,
    Badge,
    Game,
    Quest,
    QuestSubmission,
    ShoutBoardMessage,
    User,
    UserIP,
)
from app.constants import UTC

# ----------------------------------------------------------------------------
# General helpers
# ----------------------------------------------------------------------------

ALLOWED_TAGS = {
    "a", "b", "i", "u", "em", "strong", "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "blockquote", "code", "pre", "br", "div", "span", "ul", "ol", "li", "hr",
    "sub", "sup", "s", "strike", "font", "img", "video", "figure",
}

_ATTRS = {
    "a": {"href", "title", "target", "rel", "class", "id"},
    "img": {"src", "alt", "width", "height", "class", "id"},
    "video": {"src", "width", "height", "controls", "class", "id"},
    "font": {"color", "face", "size", "class", "id"},
}
for _tag in ALLOWED_TAGS:
    _ATTRS.setdefault(_tag, set()).update({"class", "id"})

SANITIZER = Sanitizer(
    {
        "tags": ALLOWED_TAGS,
        "attributes": _ATTRS,
        "empty": {"br", "hr", "img"},
        "separate": {"a", "p", "li"},
        "whitespace": {"br"},
    }
)

REQUEST_TIMEOUT = 5


def safe_url_for(*args, **kwargs):
    """Generate a URL and strip scheme and host during tests."""
    try:
        url = url_for(*args, **kwargs)
    except RuntimeError:
        app = current_app._get_current_object()
        with app.test_request_context():
            url = url_for(*args, **kwargs)
    if current_app.config.get("TESTING"):
        p = urlparse(url)
        return urlunparse(("", "", p.path, p.params, p.query, p.fragment))
    return url


def sanitize_html(html_content: str | None) -> str | None:
    """Return sanitized HTML or ``None`` for empty input.

    Parameters
    ----------
    html_content:
        Raw HTML content which may be ``None``.
    """
    if html_content is None:
        return None
    return SANITIZER.sanitize(html_content)


def get_int_param(name: str, *, source=None, default: int | None = None) -> int | None:
    """Safely retrieve an integer parameter from the request.

    Parameters
    ----------
    name:
        The parameter name to fetch.
    source:
        The data source, defaults to ``request.args``.
    default:
        Value returned if the parameter is missing or invalid.

    Returns
    -------
    int | None
        Parsed integer or ``default`` when conversion fails.
    """

    source = source or request.args
    raw = source.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def format_db_error(error: Exception) -> str:
    """Return a concise description for a database error."""
    orig = getattr(error, "orig", None)
    if orig is None:
        return str(error)
    diag = getattr(orig, "diag", None)
    primary = getattr(diag, "message_primary", None) if diag else None
    detail = getattr(diag, "message_detail", None) if diag else None
    message = primary or str(orig)
    if detail:
        message = f"{message}: {detail}"
    return message

# ----------------------------------------------------------------------------
# Misc database helpers
# ----------------------------------------------------------------------------

def generate_demo_game() -> Game | None:
    """Create a demo game for the current quarter if one does not exist."""

    current_quarter = (datetime.now(UTC).month - 1) // 3 + 1
    year = datetime.now(UTC).year
    title = f"Demo Game - Q{current_quarter} {year}"

    existing_game = Game.query.filter_by(is_demo=True, title=title).first()
    if existing_game:
        return

    # Archive previous demo games so users can view past statistics
    old_demos = Game.query.filter_by(is_demo=True, archived=False).all()
    for old in old_demos:
        submissions = (
            QuestSubmission.query
            .join(Quest, QuestSubmission.quest_id == Quest.id)
            .filter(Quest.game_id == old.id, QuestSubmission.image_url.isnot(None))
            .all()
        )
        for submission in submissions:
            delete_media_file(submission.image_url)
            submission.image_url = None

        old.is_demo = False
        old.allow_joins = False
        old.is_public = False
        old.archived = True

    if old_demos:
        db.session.commit()

    description = """
    Welcome to the newest Demo Game! Embark on a quest to create a more
    sustainable future while enjoying everyday activities, having fun, and
    fostering teamwork in the real-life battle against climate change.

    Quest Instructions:

    Concepts:

    How to Play:

    Play solo or join forces with friends in teams.
    Explore the quests and have fun completing them to earn Carbon Reduction
    Points.
    Once a quest is verified, you'll earn points displayed on the Leaderboard
    and badges of honor. Quests can be verified by uploading an image from your
    computer, taking a photo, writing a comment, or using a QR code.
    Earn achievement badges by completing a group of quests or repeating quests.
    Learn more about badge criteria by clicking on the quest name.
    """

    start_date = datetime(year, 3 * (current_quarter - 1) + 1, 1)
    end_date = (
        datetime(year + 1, 1, 1) - timedelta(seconds=1)
        if current_quarter == 4
        else datetime(year, 3 * current_quarter + 1, 1) - timedelta(seconds=1)
    )

    demo_game = Game(
        title=title,
        description=description,
        description2="Rules and guidelines for the demo game.",
        start_date=start_date,
        end_date=end_date,
        game_goal=20000,
        details="""Verifying and Earning "Carbon Reduction" Points:""",
        awards="""Stay tuned for prizes...""",
        beyond="Visit your local bike club!",
        admin_id=1,
        is_demo=True,
        twitter_username=current_app.config["TWITTER_USERNAME"],
        twitter_api_key=current_app.config["TWITTER_API_KEY"],
        twitter_api_secret=current_app.config["TWITTER_API_SECRET"],
        twitter_access_token=current_app.config["TWITTER_ACCESS_TOKEN"],
        twitter_access_token_secret=current_app.config["TWITTER_ACCESS_TOKEN_SECRET"],
        facebook_app_id=current_app.config["FACEBOOK_APP_ID"],
        facebook_app_secret=current_app.config["FACEBOOK_APP_SECRET"],
        facebook_access_token=current_app.config["FACEBOOK_ACCESS_TOKEN"],
        facebook_page_id=current_app.config["FACEBOOK_PAGE_ID"],
        instagram_access_token=current_app.config["INSTAGRAM_ACCESS_TOKEN"],
        instagram_user_id=current_app.config["INSTAGRAM_USER_ID"],
        is_public=True,
        allow_joins=True,
        leaderboard_image="leaderboard_image.png",
    )
    db.session.add(demo_game)
    admin_user = db.session.get(User, 1)
    if admin_user:
        demo_game.admins.append(admin_user)
    db.session.commit()

    import_quests_and_badges_from_csv(
        demo_game.id,
        os.path.join(current_app.static_folder, "defaultquests.csv"),
    )

    try:
        admin_id = 1
        pinned_message = ShoutBoardMessage(
            message="Get on your Bicycle this Quarter!",
            user_id=admin_id,
            game_id=demo_game.id,
            is_pinned=True,
            timestamp=datetime.now(UTC),
        )
        db.session.add(pinned_message)
        db.session.commit()
    except SQLAlchemyError as exc:  # pragma: no cover - log and rollback
        db.session.rollback()
        current_app.logger.error("Failed to pin demo message: %s", exc)

    return demo_game


def import_quests_and_badges_from_csv(game_id: int, csv_path: str) -> None:
    """Populate a game with quests and badges described in a CSV file."""

    try:
        with open(csv_path, mode="r", encoding="utf-8") as csv_file:
            data = csv.DictReader(csv_file)
            for row in data:
                badge_name = sanitize_html(row["badge_name"])
                badge_description = sanitize_html(row["badge_description"])
                if "badge_image_filename" in row and row["badge_image_filename"]:
                    badge_image_filename = row["badge_image_filename"]
                else:
                    badge_image_filename = f"{badge_name.lower().replace(' ', '_')}.png"
                badge_image_path = os.path.join(
                    current_app.static_folder,
                    "images",
                    "badge_images",
                    badge_image_filename,
                )
                if not os.path.exists(badge_image_path):
                    continue
                badge = Badge.query.filter_by(name=badge_name).first()
                if not badge:
                    badge = Badge(
                        name=badge_name,
                        description=badge_description,
                        image=badge_image_filename,
                    )
                    db.session.add(badge)
                    db.session.flush()
                quest = Quest(
                    category=(sanitize_html(row["category"]) or None),
                    title=sanitize_html(row["title"]),
                    description=sanitize_html(row["description"]),
                    tips=sanitize_html(row["tips"]),
                    points=int(row["points"].replace(",", "")),
                    badge_awarded=int(row["badge_awarded"]),
                    completion_limit=int(row["completion_limit"]),
                    frequency=sanitize_html(row["frequency"]),
                    verification_type=sanitize_html(row["verification_type"]),
                    badge_id=badge.id,
                    game_id=game_id,
                )
                db.session.add(quest)
            db.session.commit()
    except (OSError, SQLAlchemyError) as exc:  # pragma: no cover - log and rollback
        db.session.rollback()
        current_app.logger.error(
            "Failed to import quests and badges from %s: %s", csv_path, exc
        )


def log_user_ip(user: User) -> None:
    """Store the user's current IP address if it hasn't been logged before."""

    ip_address = request.remote_addr
    existing_ip = UserIP.query.filter_by(user_id=user.id, ip_address=ip_address).first()
    if not existing_ip:
        new_ip = UserIP(user_id=user.id, ip_address=ip_address)
        db.session.add(new_ip)
        db.session.commit()


def get_game_badges(game_id: int) -> list[Badge]:
    """Return all badges associated with a game."""

    game = db.session.get(Game, game_id)
    if not game:
        return []
    return Badge.query.filter_by(game_id=game_id).all()

# ----------------------------------------------------------------------------
# Re-export grouped helpers
# ----------------------------------------------------------------------------

from .file_uploads import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    ALLOWED_IMAGE_MIMETYPES,
    ALLOWED_VIDEO_MIMETYPES,
    MAX_IMAGE_BYTES,
    MAX_VIDEO_BYTES,
    MAX_JSON_BYTES,
    MAX_IMAGE_DIMENSION,
    MAX_VIDEO_WIDTH,
    MAX_VIDEO_HEIGHT,
    allowed_file,
    allowed_image_file,
    allowed_video_file,
    correct_image_orientation,
    save_image_file,
    save_leaderboard_image,
    save_game_logo,
    create_smog_effect,
    generate_smoggy_images,
    save_profile_picture,
    save_badge_image,
    save_bicycle_picture,
    save_submission_image,
    save_submission_video,
    public_media_url,
    delete_media_file,
    save_sponsor_logo,
    save_calendar_service_json,
)

from .email_utils import (
    send_email,
    send_social_media_liaison_email,
    check_and_send_liaison_emails,
)

from .quest_scoring import (
    MAX_POINTS_INT,
    update_user_score,
    can_complete_quest,
    get_last_relevant_completion_time,
    check_and_award_badges,
    check_and_revoke_badges,
    enhance_badges_with_task_info,
)

__all__ = [
    "ALLOWED_IMAGE_EXTENSIONS",
    "ALLOWED_VIDEO_EXTENSIONS",
    "ALLOWED_IMAGE_MIMETYPES",
    "ALLOWED_VIDEO_MIMETYPES",
    "MAX_IMAGE_BYTES",
    "MAX_VIDEO_BYTES",
    "MAX_JSON_BYTES",
    "MAX_IMAGE_DIMENSION",
    "MAX_VIDEO_WIDTH",
    "MAX_VIDEO_HEIGHT",
    "MAX_POINTS_INT",
    "REQUEST_TIMEOUT",
    "allowed_file",
    "allowed_image_file",
    "allowed_video_file",
    "correct_image_orientation",
    "save_image_file",
    "save_leaderboard_image",
    "save_game_logo",
    "create_smog_effect",
    "generate_smoggy_images",
    "save_profile_picture",
    "save_badge_image",
    "save_bicycle_picture",
    "save_submission_image",
    "save_submission_video",
    "public_media_url",
    "delete_media_file",
    "save_sponsor_logo",
    "save_calendar_service_json",
    "send_email",
    "send_social_media_liaison_email",
    "check_and_send_liaison_emails",
    "update_user_score",
    "can_complete_quest",
    "get_last_relevant_completion_time",
    "check_and_award_badges",
    "check_and_revoke_badges",
    "enhance_badges_with_task_info",
    "generate_demo_game",
    "import_quests_and_badges_from_csv",
    "log_user_ip",
    "get_game_badges",
    "safe_url_for",
    "sanitize_html",
    "get_int_param",
]
