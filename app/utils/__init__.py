"""Utility package exposing helper functions used across the app."""

from __future__ import annotations

import csv
import os
from datetime import datetime, timedelta

from flask import current_app, request
from html_sanitizer import Sanitizer

from app.constants import UTC
from app.models import db, Badge, Game, Quest, QuestSubmission, UserIP

from .file_uploads import *  # noqa: F401,F403
from .email_utils import *  # noqa: F401,F403
from .quest_scoring import *  # noqa: F401,F403


ALLOWED_TAGS = {
    "a",
    "b",
    "i",
    "u",
    "em",
    "strong",
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "code",
    "pre",
    "br",
    "div",
    "span",
    "ul",
    "ol",
    "li",
    "hr",
    "sub",
    "sup",
    "s",
    "strike",
    "font",
    "img",
    "video",
    "figure",
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


def sanitize_html(html_content: str) -> str:
    """Return sanitized HTML content."""

    return SANITIZER.sanitize(html_content)


REQUEST_TIMEOUT = 5


def generate_demo_game():
    current_quarter = (datetime.now(UTC).month - 1) // 3 + 1
    year = datetime.now(UTC).year
    title = f"Demo Game - Q{current_quarter} {year}"

    existing_game = Game.query.filter_by(is_demo=True, title=title).first()
    if existing_game:
        return

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
    if current_quarter == 4:
        end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        end_date = datetime(year, 3 * current_quarter + 1, 1) - timedelta(seconds=1)

    demo_game = Game(
        title=title,
        description=description,
        description2="Rules and guidelines for the demo game.",
        start_date=start_date,
        end_date=end_date,
        game_goal=20000,
        details="""
        Verifying and Earning "Carbon Reduction" Points:

        Sign In and Access Quests: Log into the game, navigate to the homepage,
        and scroll down on the main game page to see the quest list.
        Complete a Quest: Choose by clicking on a quest from the list, and after
        completion, click "Verify Quest". You will need to upload a picture as
        proof of your achievement and/or you can add a comment about your
        experience.
        Submit Verification: After uploading your verification photo and adding
        a comment, click the "Submit Verification" button. You should receive a
        confirmation message indicating your quest completion has been updated.
        Your image will appear at the bottom of the page and it will be
        automatically uploaded to Quest by Cycle’s social Media accounts.
        Social Media Interaction: The uploaded photo will be shared on
        QuestByCycle’s Twitter, Facebook, and Instagram pages. You can view and
        expand thumbnail images of completed quests by others, read comments, and
        visit their profiles by clicking on the images. Use the social media
        buttons to comment and engage with the community.
        Explore the Leaderboard: Check the dynamic leaderboard to see the
        progress of players and teams. The community-wide impact is displayed via
        a "thermometer" showing collective carbon reduction efforts. Clicking on
        a player's name reveals their completed quests and badges.

        Earning Badges:

        Quest Categories: Each quest belongs to a category. Completing all quests
        in a category earns you a badge. The more quests you complete, the higher
        your chances of earning badges.
        Quest Limits: The quest detail popup provides completion limits. If you
        reach the limit set for a quest, you will earn a badge.

        Social Media Interaction:

        Quest Entries: Engage with the community by commenting and sharing your
        achievements on social media platforms directly through the game. Click
        on the thumbnail images at the bottom of a Quest to view user's
        submissions. At the bottom, there will be buttons to take you to
        Facebook, X, and Instagram where you can comment on various quests that
        have been posted and communicate with other players. Through friendly
        competition, let's strive to reduce carbon emissions and make a positive
        impact on the atmosphere.
        """,
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
    except Exception:
        db.session.rollback()

    return demo_game


def import_quests_and_badges_from_csv(game_id: int, csv_path: str) -> None:
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
                    category=sanitize_html(row["category"]),
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
    except Exception:
        db.session.rollback()


def log_user_ip(user) -> None:
    ip_address = request.remote_addr
    existing_ip = UserIP.query.filter_by(user_id=user.id, ip_address=ip_address).first()

    if not existing_ip:
        new_ip = UserIP(user_id=user.id, ip_address=ip_address)
        db.session.add(new_ip)
        db.session.commit()

