                                              
"""
Module: quests
This module contains all routes and helper functions for quest management,
submission handling, and related operations in the application.
"""

import base64
import csv
import os
from datetime import datetime
from io import BytesIO

import qrcode
import requests
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
    abort
)
from flask_login import current_user, login_required
from app.decorators import require_admin
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
from app.forms import PhotoForm, QuestForm
from app.social import post_to_social_media
from app.utils import REQUEST_TIMEOUT, sanitize_html, get_int_param, format_db_error
from app.utils.quest_scoring import (
    can_complete_quest,
    check_and_award_badges,
    check_and_revoke_badges,
    get_last_relevant_completion_time,
    update_user_score,
)
from app import limiter
from app.utils.rate_limit import user_or_ip
from app.utils.file_uploads import (
    save_badge_image,
    save_submission_image,
    save_submission_video,
    public_media_url,
)
from app.activitypub_utils import (
    post_activitypub_create_activity,
    post_activitypub_like_activity,
    post_activitypub_comment_activity
)
from .models import (
    db, Badge, Game, Quest, QuestSubmission,
    User, UserQuest, SubmissionLike, SubmissionReply,
    Notification, user_games
)
from app.constants import UTC

quests_bp = Blueprint("quests", __name__, template_folder="templates")


@quests_bp.route("/<int:game_id>/manage_quests", methods=["GET"])
@login_required
def manage_game_quests(game_id):
    """
    Render the manage quests page for a given game.

    Args:
        game_id (int): The ID of the game.
    """
    game = Game.query.get_or_404(game_id)

    if not current_user.is_admin_for_game(game_id):
        flash("Access denied: Only administrators can manage quests.", "danger")
        return redirect(url_for("main.index", game_id=game_id))

    form = QuestForm()
    quests = Quest.query.filter_by(game_id=game_id).all()
    response = make_response(
        render_template(
            "manage_quests.html",
            game=game,
            quests=quests,
            form=form,
            game_id=game_id,
            in_admin_dashboard=True,
        )
    )
    response.headers.update(
        {
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )
    return response


@quests_bp.route("/game/<int:game_id>/add_quest", methods=["GET", "POST"])
@login_required
def add_quest(game_id):
    """Add a new quest to the game."""

    if not current_user.is_admin_for_game(game_id):
        flash("Access denied: Only administrators can add quests.", "danger")
        return redirect(url_for("main.index", game_id=game_id))

    form = QuestForm()
    form.game_id.data = game_id

    if form.validate_on_submit():
        badge_option = form.badge_option.data
        badge_id = None
        if badge_option in ("individual", "both"):
            badge_id = (
                int(form.badge_id.data)
                if form.badge_id.data and form.badge_id.data != "0"
                else None
            )

            if badge_id:
                badge = db.session.get(Badge, badge_id)
                if not badge or badge.game_id != game_id:
                    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                        return jsonify(success=False, message="Invalid badge for this game"), 400
                    flash("Invalid badge for this game.", "error")
                    return redirect(
                        url_for(
                            "quests.manage_game_quests",
                            game_id=game_id,
                            in_admin_dashboard=True,
                        )
                    )

            if not badge_id and form.badge_name.data:
                badge_image_file = None
                if "badge_image_filename" in request.files:
                    badge_image_file = request.files["badge_image_filename"]
                    if badge_image_file and badge_image_file.filename != "":
                        badge_image_file = save_badge_image(badge_image_file)
                    else:
                        flash("No badge image selected for upload.", "error")

                new_badge = Badge(
                    name=sanitize_html(form.badge_name.data),
                    description=sanitize_html(form.badge_description.data),
                    image=badge_image_file,
                    game_id=game_id,
                )
                db.session.add(new_badge)
                db.session.flush()
                badge_id = new_badge.id

        category = (
            sanitize_html(form.category.data) if form.category.data else None
        )
        new_quest = Quest(
            title=sanitize_html(form.title.data),
            description=sanitize_html(form.description.data),
            tips=sanitize_html(form.tips.data),
            points=form.points.data,
            game_id=game_id,
            completion_limit=form.completion_limit.data,
            badge_awarded=form.badge_awarded.data,
            frequency=sanitize_html(form.frequency.data),
            enabled=form.enabled.data,
            is_sponsored=form.is_sponsored.data,
            category=category,
            verification_type=sanitize_html(form.verification_type.data),
            badge_id=badge_id,
            badge_option=badge_option,
        )
        db.session.add(new_quest)
        try:
            db.session.commit()
            if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                return jsonify(
                    success=True,
                    redirectUrl=url_for("quests.manage_game_quests", game_id=game_id)
                )
            flash("Quest added successfully!", "success")
        except Exception:                                
            db.session.rollback()
            if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                return jsonify(success=False, message="An error occurred"), 500
            flash("An error occured.", "error")

        return redirect(url_for("quests.manage_game_quests", game_id=game_id,
            in_admin_dashboard=True))

    return render_template("add_quest.html", form=form, game_id=game_id,
        in_admin_dashboard=True)


@quests_bp.route("/quest/<int:quest_id>/submit", methods=["POST"])
@login_required
def submit_quest(quest_id):
    """
    Submit a quest completion. This version now includes the hybrid behavior:
    if an image is provided and the user is set to cross-post, it will also post
    to Mastodon and generate a local ActivityPub Create activity.
    """
    current_app.logger.debug("Start quest submission for quest_id=%s", quest_id)
    quest = db.session.get(Quest, quest_id)
    if not quest:
        abort(404)
    game = Game.query.get_or_404(quest.game_id)
    now = datetime.now(UTC)

                                              
    if game.start_date > now or now > game.end_date:
        return jsonify({
            "success": False,
            "message": "This quest cannot be completed outside of the game dates"
        }), 403

    if quest.from_calendar and quest.calendar_event_start and now < quest.calendar_event_start:
        return jsonify({
            "success": False,
            "message": "Submissions open once the event begins."
        }), 403

    can_verify, next_eligible_time = can_complete_quest(current_user.id, quest_id)
    if not can_verify:
        return jsonify({
            "success": False,
            "message": f"You cannot submit this quest again until {next_eligible_time}"
        }), 403


    verification_type = quest.verification_type
    image_file = request.files.get("image")
    video_file = request.files.get("video")
    comment = sanitize_html(request.form.get("verificationComment", ""))

                                                    
    current_app.logger.debug(
        "submit_quest called: verification_type=%s, image_file=%s, video_file=%s",
        verification_type,
        getattr(image_file, "filename", None),
        getattr(video_file, "filename", None),
    )

                                          
    if verification_type == "qr_code":
        return jsonify({
            "success": True,
            "message": "QR Code verification does not require any submission"
        }), 200
    if verification_type == "photo" and (not image_file or image_file.filename == ""):
        return jsonify({
            "success": False,
            "message": "No file selected for photo verification"
        }), 400
    if verification_type == "video" and (not video_file or video_file.filename == ""):
        return jsonify({
            "success": False,
            "message": "No file selected for video verification"
        }), 400
    if verification_type == "comment" and not comment:
        return jsonify({"success": False, "message": "Comment required for verification"}), 400
    if verification_type == "photo_comment" and (not image_file or image_file.filename == ""):
        return jsonify({
            "success": False,
            "message": "Photo required for verification"
        }), 400
    if quest.verification_type == "Pause":
        return jsonify({"success": False, "message": "This quest is currently paused"}), 403

    try:
        image_url = None
        video_url = None
        if image_file and image_file.filename:
            image_url = save_submission_image(image_file)
            image_path = os.path.join(current_app.static_folder, image_url)
        elif video_file and video_file.filename:
            current_app.logger.debug(
                "Attempting to save video file '%s'", video_file.filename
            )
            try:
                video_url = save_submission_video(video_file)
                current_app.logger.debug("Video saved to %s", video_url)
            except ValueError as ve:
                current_app.logger.error(f"Error processing video file: {str(ve)}")
                return jsonify({"success": False, "message": "An error occurred while processing the video file. Please try again later."}), 400
            image_path = os.path.join(current_app.static_folder, video_url)
        else:
            image_path = None

        display_name = current_user.display_name or current_user.username
        status_text = f"{display_name} completed '{quest.title}'! #QuestByCycle"

                                                                         
        twitter_url, fb_url, instagram_url = (None, None, None)
        if image_url and current_user.upload_to_socials:
            twitter_url, fb_url, instagram_url = post_to_social_media(
                image_url, image_path, status_text, game
            )

                                                                    
        mastodon_url = None
        if image_url and current_user.upload_to_mastodon and current_user.mastodon_access_token:
            mastodon_url = post_to_mastodon_status(image_path, status_text, current_user)

        new_submission = QuestSubmission(
            quest_id=quest_id,
            user_id=current_user.id,
            image_url=(image_url if image_url else None),
            video_url=video_url,
            comment=comment,
            twitter_url=twitter_url,
            fb_url=fb_url,
            instagram_url=instagram_url,
            timestamp=datetime.now(UTC),
        )
        db.session.add(new_submission)

        user_quest = UserQuest.query.filter_by(user_id=current_user.id, quest_id=quest_id).first()
        if not user_quest:
            user_quest = UserQuest(
                user_id=current_user.id,
                quest_id=quest_id,
                completions=1,
                points_awarded=quest.points,
                completed_at=datetime.now(UTC),
            )
            db.session.add(user_quest)
        else:
            user_quest.completions += 1
            user_quest.points_awarded += quest.points
            user_quest.completed_at = datetime.now(UTC)

        db.session.commit()

        update_user_score(current_user.id)
        check_and_award_badges(current_user.id, quest_id, quest.game_id)

        db.session.add(
            Notification(
                user_id=current_user.id,
                type="quest_complete",
                payload={
                    "quest_id": quest_id,
                    "quest_title": quest.title,
                    "submission_id": new_submission.id,
                },
            )
        )
        db.session.commit()
        total_points = db.session.query(
            db.func.sum(UserQuest.points_awarded)
        ).join(Quest, UserQuest.quest_id == Quest.id
        ).filter(
            UserQuest.user_id == current_user.id,
            Quest.game_id == quest.game_id
        ).scalar() or 0
        total_completion_count = QuestSubmission.query.filter_by(quest_id=quest_id).count()

                                                         
        activity = None
        if image_url or video_url:
            activity = post_activitypub_create_activity(new_submission, current_user, quest)

        current_app.logger.debug(
            "Quest submission successful: image_url=%s, video_url=%s",
            image_url,
            video_url,
        )

        return jsonify({
            "success": True,
            "new_completion_count": user_quest.completions,
            "total_completion_count": total_completion_count,
            "total_points": total_points,
            "image_url": public_media_url(image_url),
            "video_url": public_media_url(video_url),
            "comment": comment,
            "twitter_url": twitter_url,
            "fb_url": fb_url,
            "instagram_url": instagram_url,
            "mastodon_url": mastodon_url,
            "activity": activity                                                             
        })
    except Exception as error:
        current_app.logger.error(
            "Quest submission failed: %s", format_db_error(error)
        )
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred while submitting your quest."
        }), 500


@quests_bp.route("/quest/<int:quest_id>/update", methods=["POST"])
@login_required
@require_admin
def update_quest(quest_id):
    """
    Update quest details. Only accessible to administrators.

    Args:
        quest_id (int): The ID of the quest.
    """

    quest = Quest.query.get_or_404(quest_id)
    if not current_user.is_super_admin and not current_user.is_admin_for_game(quest.game_id):
        return jsonify({"success": False, "message": "Permission denied"}), 403

    data = request.get_json()

    quest.title = sanitize_html(data.get("title", quest.title))
    quest.description = sanitize_html(data.get("description", quest.description))
    quest.tips = sanitize_html(data.get("tips", quest.tips))

    def parse_int(field_name: str, current_value: int) -> int:
        value = data.get(field_name)
        if value in (None, ""):
            return current_value
        try:
            return int(value)
        except ValueError as err:  # pragma: no cover - defensive programming
            raise ValueError(f"Invalid {field_name}") from err

    try:
        quest.points = parse_int("points", quest.points)
        quest.completion_limit = parse_int(
            "completion_limit", quest.completion_limit
        )
        quest.badge_awarded = parse_int("badge_awarded", quest.badge_awarded)
    except ValueError as error:
        return jsonify({"success": False, "message": "Invalid input for quest field(s)."}), 400

    quest.enabled = data.get("enabled", quest.enabled)
    quest.is_sponsored = data.get("is_sponsored", quest.is_sponsored)
    category_data = data.get("category")
    if category_data is not None:
        category = sanitize_html(category_data)
        quest.category = category or None
    quest.verification_type = sanitize_html(
        data.get("verification_type", quest.verification_type)
    )
    quest.frequency = sanitize_html(data.get("frequency", quest.frequency))

    quest.badge_option = data.get("badge_option", quest.badge_option)

    badge_id = data.get("badge_id")
    if badge_id is not None and quest.badge_option in ("individual", "both"):
        try:
            badge_id_int = int(badge_id)
        except ValueError:
            return jsonify({"success": False, "message": "Invalid badge ID"}), 400
        badge = db.session.get(Badge, badge_id_int)
        if not badge or badge.game_id != quest.game_id:
            return jsonify({"success": False, "message": "Invalid badge for this quest"}), 400
        quest.badge_id = badge_id_int
    elif quest.badge_option in ("none", "category"):
        quest.badge_id = None

    quest.from_calendar = data.get("from_calendar", quest.from_calendar)
    quest.calendar_event_id = sanitize_html(
        data.get("calendar_event_id", quest.calendar_event_id)
    )
    start_str = data.get("calendar_event_start")
    if start_str is not None:
        if start_str == "":
            quest.calendar_event_start = None
        else:
            try:
                start_dt = datetime.fromisoformat(start_str)
            except ValueError:
                return jsonify(
                    {"success": False, "message": "Invalid calendar event start"}
                ), 400
            if not start_dt.tzinfo:
                start_dt = start_dt.replace(tzinfo=UTC)
            quest.calendar_event_start = start_dt

    try:
        db.session.commit()
        if (
            quest.calendar_event_start
            and quest.calendar_event_start.tzinfo is None
        ):
            quest.calendar_event_start = quest.calendar_event_start.replace(tzinfo=UTC)
        return jsonify({"success": True, "message": "Quest updated successfully"})
    except Exception as error:
        db.session.rollback()
        current_app.logger.error(
            "Failed to update quest %s: %s", quest_id, format_db_error(error)
        )
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred while updating the quest.",
        }), 500


@quests_bp.route("/quest/<int:quest_id>/delete", methods=["DELETE"])
@login_required
def delete_quest(quest_id):
    """
    Delete a quest. Only administrators are allowed to perform this action.

    Args:
        quest_id (int): The ID of the quest to delete.
    """
    quest_to_delete = Quest.query.get_or_404(quest_id)
    game_id = quest_to_delete.game_id
    if not current_user.is_admin_for_game(game_id):
        return jsonify({"success": False, "message": "Permission denied"}), 403
    db.session.delete(quest_to_delete)

    try:
        db.session.commit()
        return jsonify({"success": True, "message": "Quest deleted successfully"})
    except Exception as error:
        db.session.rollback()
        current_app.logger.error(
            "Failed to delete quest %s: %s", quest_id, format_db_error(error)
        )
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred while deleting the quest.",
        }), 500


@quests_bp.route("/game/<int:game_id>/quests", methods=["GET"])
def get_quests_for_game(game_id):
    """
    Get all quests for a specific game.

    Args:
        game_id (int): The ID of the game.
    """
    quests = Quest.query.filter_by(game_id=game_id).all()
    quests_data = [
        {
            "id": quest.id,
            "title": quest.title,
            "description": quest.description,
            "tips": quest.tips,
            "points": quest.points,
            "completion_limit": quest.completion_limit,
            "enabled": quest.enabled,
            "is_sponsored": quest.is_sponsored,
            "verification_type": quest.verification_type,
            "game_id": quest.game_id,
            "badge_id": quest.badge_id,
            "badge_name": quest.badge.name if quest.badge else "None",
            "badge_description": quest.badge.description if quest.badge else "",
            "badge_awarded": quest.badge_awarded if quest.badge_id else "",
            "frequency": quest.frequency,
            "category": quest.category if quest.category else "Not Set",
            "badge_option": quest.badge_option,
            "from_calendar": quest.from_calendar,
            "calendar_event_id": quest.calendar_event_id,
            "calendar_event_start": quest.calendar_event_start.isoformat()
            if quest.calendar_event_start
            else None,
        }
        for quest in quests
    ]
    response = jsonify(quests=quests_data)
    response.headers.update(
        {
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )
    return response


@quests_bp.route("/game/<int:game_id>/import_quests", methods=["POST"])
@login_required
@limiter.limit("10/minute", key_func=user_or_ip)
@limiter.limit("50/minute")
def import_quests(game_id):
    """
    Import quests from a CSV file for a specified game.

    Args:
        game_id (int): The ID of the game.
    """
    if "quests_csv" not in request.files:
        return jsonify(success=False, message="No file part"), 400

    file = request.files["quests_csv"]
    if file.filename == "":
        return jsonify(success=False, message="No selected file"), 400

    if file:
        upload_dir = current_app.config["TASKCSV"]
        os.makedirs(upload_dir, exist_ok=True)

        filepath = os.path.join(upload_dir, secure_filename(file.filename))
        file.save(filepath)

        imported_badges = []
        with open(filepath, mode="r", encoding="utf-8") as csv_file:
            quests_data = csv.DictReader(csv_file)
            try:
                for quest_info in quests_data:
                    badge = Badge.query.filter_by(
                        name=sanitize_html(quest_info["badge_name"])
                    ).first()
                    if not badge:
                        badge = Badge(
                            name=sanitize_html(quest_info["badge_name"]),
                            description=sanitize_html(quest_info["badge_description"]),
                        )
                        db.session.add(badge)
                        db.session.flush()
                        imported_badges.append(badge.id)

                    new_quest = Quest(
                        category=(
                            sanitize_html(quest_info["category"]) or None
                        ),
                        title=sanitize_html(quest_info["title"]),
                        description=sanitize_html(quest_info["description"]),
                        tips=sanitize_html(quest_info["tips"]),
                        points=int(quest_info["points"].replace(",", "") or 0),
                        completion_limit=int(quest_info["completion_limit"] or 0),
                        frequency=sanitize_html(quest_info["frequency"]),
                        verification_type=sanitize_html(quest_info["verification_type"]),
                        badge_id=badge.id,
                        badge_awarded=int(quest_info.get("badge_awarded", 1) or 1),
                        game_id=game_id,
                    )
                    db.session.add(new_quest)
                db.session.commit()
            except (KeyError, ValueError):
                db.session.rollback()
                os.remove(filepath)
                return jsonify(success=False, message="Invalid CSV format"), 400
            os.remove(filepath)

        return jsonify(
            success=True,
            redirectUrl=url_for("quests.manage_game_quests", game_id=game_id),
        )

    return jsonify(success=False, message="Invalid file"), 400


@quests_bp.route("/quest/<int:quest_id>/submissions")
@login_required
def get_quest_submissions(quest_id):
    submissions = (
        db.session.query(QuestSubmission, Quest)
        .join(Quest, Quest.id == QuestSubmission.quest_id)
        .filter(QuestSubmission.quest_id == quest_id)
        .all()
    )

    submissions_data = []
    for sub, quest in submissions:
        user = db.session.get(User, sub.user_id)
        submissions_data.append({
            "id"                 : sub.id,
            "image_url"          : public_media_url(sub.image_url),
            "video_url"          : public_media_url(sub.video_url),
            "comment"            : sub.comment,
            "timestamp"          : sub.timestamp.strftime("%Y-%m-%d %H:%M"),
            "user_id"            : sub.user_id,
            "user_display_name"  : user.display_name or user.username,
            "user_username"      : user.username,
            "user_profile_picture": (
                url_for('static', filename=user.profile_picture)
                if user.profile_picture
                else url_for('static', filename=current_app.config['PLACEHOLDER_IMAGE'])
            ),
            "twitter_url"        : sub.twitter_url,
            "fb_url"             : sub.fb_url,
            "instagram_url"      : sub.instagram_url,
            "verification_type"  : quest.verification_type                  
        })
    return jsonify(submissions_data)


@quests_bp.route("/detail/<int:quest_id>/user_completion")
@login_required
                                                                                  
def quest_user_completion(quest_id):
    """
    Get quest details and user completion data for a specific quest.

    Args:
        quest_id (int): The ID of the quest.
    """
    quest = Quest.query.get_or_404(quest_id)
    badge = db.session.get(Badge, quest.badge_id) if quest.badge_id else None
    user_quest = UserQuest.query.filter_by(
        user_id=current_user.id, quest_id=quest_id
    ).first()
    can_verify, next_eligible_time = can_complete_quest(current_user.id, quest_id)
    last_relevant_completion_time = get_last_relevant_completion_time(
        current_user.id, quest_id
    )

    badge_info = (
        {
            "id": badge.id,
            "name": badge.name,
            "description": badge.description,
            "image": badge.image,
        }
        if badge
        else {"name": "Default", "image": None}
    )

    quest_info = {
        "id": quest.id,
        "title": quest.title,
        "description": quest.description,
        "tips": quest.tips,
        "points": quest.points,
        "completion_limit": quest.completion_limit,
        "badge_awarded": quest.badge_awarded,
        "category": quest.category,
        "frequency": quest.frequency,
        "badge_option": quest.badge_option,
        "enabled": quest.enabled,
        "is_sponsored": quest.is_sponsored,
        "verification_type": quest.verification_type,
        "badge": badge_info,
        "nextEligibleTime": (
            next_eligible_time.isoformat() if next_eligible_time else None
        ),
    }

    user_completion_data = {
        "completions": user_quest.completions if user_quest else 0,
        "lastCompletionTimestamp": (
            user_quest.completed_at.isoformat()
            if user_quest and user_quest.completed_at
            else None
        ),
    }

    response_data = {
        "quest": quest_info,
        "userCompletion": user_completion_data,
        "canVerify": can_verify,
        "nextEligibleTime": (
            next_eligible_time.isoformat() if next_eligible_time else None
        ),
        "lastRelevantCompletionTime": (
            last_relevant_completion_time.isoformat()
            if last_relevant_completion_time
            else None
        ),
    }

    return jsonify(response_data)


@quests_bp.route("/get_last_relevant_completion_time/<int:quest_id>/<int:user_id>")
@login_required
def get_last_relevant_completion_time_route(quest_id, user_id):
    """
    Get the last relevant completion time for a user on a specific quest.

    Args:
        quest_id (int): The ID of the quest.
        user_id (int): The user ID.
    """
    last_time = get_last_relevant_completion_time(user_id, quest_id)
    
    if last_time:
        return jsonify(success=True, lastRelevantCompletionTime=last_time.isoformat())
    return jsonify(success=False, message="No relevant completion found")

@quests_bp.route("/generate_qr/<int:quest_id>")
def generate_qr(quest_id):
    """
    Generate a QR code for quest submission.

    Args:
        quest_id (int): The ID of the quest.
    """
    quest = Quest.query.get_or_404(quest_id)
    url = url_for("quests.submit_photo", quest_id=quest_id, _external=True)
    qr_code = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr_code.add_data(url)
    qr_code.make(fit=True)
    img = qr_code.make_image(fill_color="white", back_color="black")
    img_buffer = BytesIO()
    img.save(img_buffer, format="PNG")
    img_data = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
    html_content = (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "    <meta charset=\"UTF-8\">\n"
        f"    <title>QR Code - {quest.title}</title>\n"
        "    <style>\n"
        "        body { text-align: center; padding: 20px; font-family: Arial, sans-serif; }\n"
        "        .qrcodeHeader img { max-width: 100%; height: auto; }\n"
        "        h1, h2 { margin: 10px 0; }\n"
        "        img { margin-top: 20px; }\n"
        "        @media print {\n"
        "            .no-print { display: none; }\n"
        "        }\n"
        "    </style>\n"
        "</head>\n"
        "<body>\n"
        f"    <div class=\"qrcodeHeader\">\n"
        f"        <img src=\"{url_for('static', filename='images/welcomeQuestByCycle.webp')}\" alt=\"Welcome\">\n"
        "    </div>\n"
        "    <h1>Congratulations!</h1>\n"
        f"    <h2>Scan to complete '{quest.title}' and gain {quest.points} points!</h2>\n"
        f"    <img src=\"data:image/png;base64,{img_data}\" alt=\"QR Code\">\n"
        "    <h2>Quest By Cycle is a free eco-adventure game where players pedal their way to sustainability, "
        "earn rewards, and transform communities—all while having fun!</h2>\n"
        "</body>\n"
        "</html>\n"
    )
    response = make_response(html_content)
    response.headers["Content-Type"] = "text/html"
    return response


def post_to_mastodon_status(image_path, status_text, user):
    """
    Post a new status on Mastodon using the user's linked account.

    This function first uploads the image to the Mastodon media endpoint,
    then posts a status (with the media attached) to the Mastodon statuses endpoint.
    """
    instance = user.mastodon_instance                          
    access_token = user.mastodon_access_token
                  
                               
    media_upload_url = f"https://{instance}/api/v1/media"
    headers = {"Authorization": f"Bearer {access_token}"}
    with open(image_path, "rb") as image_file:
        files = {"file": image_file}
        media_response = requests.post(
            media_upload_url,
            headers=headers,
            files=files,
            timeout=REQUEST_TIMEOUT,
        )
    media_response.raise_for_status()
    media_data = media_response.json()
    media_id = media_data.get("id")
    if not media_id:
        return None

                                                      
    statuses_url = f"https://{instance}/api/v1/statuses"
    payload = {"status": status_text, "media_ids[]": media_id}
    status_response = requests.post(
        statuses_url,
        headers=headers,
        data=payload,
        timeout=REQUEST_TIMEOUT,
    )
    status_response.raise_for_status()
    status_data = status_response.json()
    status_url = status_data.get("url")
    return status_url


@quests_bp.route("/submit_photo/<int:quest_id>", methods=["GET", "POST"])
@login_required
def submit_photo(quest_id):
    """
    Handle photo submissions for quest completion.
    If the user is linked to Mastodon, the submission image will be posted as a status on Mastodon.
    Additionally, a local ActivityPub Create activity is generated for the submission.
    """
    form = PhotoForm()
    quest = Quest.query.get_or_404(quest_id)
    game = Game.query.get_or_404(quest.game_id)
    # Join the quest's game automatically when a user arrives via a direct link.
    if game not in current_user.participated_games:
        db.session.execute(
            user_games.insert().values(user_id=current_user.id, game_id=game.id)
        )
        current_user.selected_game_id = game.id
        db.session.commit()

    now = datetime.now(UTC)

    start_date = game.start_date
    end_date = game.end_date
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=UTC)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=UTC)

    if not quest.enabled:
        flash("This quest is not enabled.", "error")
        return redirect(url_for("main.index"))

    if start_date > now or now > end_date:
        flash("This quest cannot be completed outside of the game dates.", "error")
        return redirect(url_for("main.index"))

    if quest.from_calendar and quest.calendar_event_start:
        event_start = quest.calendar_event_start
        if event_start.tzinfo is None:
            event_start = event_start.replace(tzinfo=UTC)
        if now < event_start:
            flash("Submissions open once the event begins.", "error")
            return redirect(url_for("main.index"))

    if request.method == "POST":
        can_verify, next_eligible_time = can_complete_quest(current_user.id, quest_id)
        if not can_verify:
            message = f"You cannot submit this quest again until {next_eligible_time}."
            return jsonify({"success": False, "message": message}), 400

        photo = request.files.get("photo")
        video = request.files.get("video")
        comment = sanitize_html(request.form.get("verificationComment", ""))

                                                                             
                                                                           
                                                                  
        if photo and not video and photo.mimetype.startswith("video/"):
            video = photo
            photo = None

        image_url = None
        video_url = None

        if photo:
            image_url = save_submission_image(photo)
            media_path = os.path.join(current_app.static_folder, image_url)
        elif video:
            try:
                video_url = save_submission_video(video)
            except ValueError as ve:
                current_app.logger.error(f"Error processing video: {ve}")
                return jsonify({"success": False, "message": "An error occurred while processing the video."}), 400
            media_path = os.path.join(current_app.static_folder, video_url)
        else:
            return jsonify({"success": False, "message": "No media detected, please try again."}), 400
        display_name = current_user.display_name or current_user.username
        status_text = f"{display_name} completed '{quest.title}'! #QuestByCycle"

                                                  
                                                
        twitter_url, fb_url, instagram_url = (None, None, None)
        if image_url and current_user.upload_to_socials:
            twitter_url, fb_url, instagram_url = post_to_social_media(
                image_url, media_path, status_text, game
            )

                                                 
        mastodon_url = None
        if image_url and current_user.upload_to_mastodon and current_user.mastodon_access_token:
            mastodon_url = post_to_mastodon_status(media_path, status_text, current_user)

        new_submission = QuestSubmission(
            quest_id=quest_id,
            user_id=current_user.id,
            image_url=image_url,
            video_url=video_url if video else None,
            comment=comment,
            twitter_url=twitter_url,
            fb_url=fb_url,
            instagram_url=instagram_url,
            timestamp=datetime.now(UTC),
        )
        db.session.add(new_submission)

        user_quest = UserQuest.query.filter_by(user_id=current_user.id, quest_id=quest_id).first()
        if not user_quest:
            user_quest = UserQuest(
                user_id=current_user.id,
                quest_id=quest_id,
                completions=1,
                points_awarded=quest.points,
            )
            db.session.add(user_quest)
        else:
            user_quest.completions += 1
            user_quest.points_awarded += quest.points
            user_quest.completed_at = datetime.now(UTC)

        db.session.commit()

        update_user_score(current_user.id)
        check_and_award_badges(current_user.id, quest_id, quest.game_id)

        activity = post_activitypub_create_activity(new_submission, current_user, quest)

        message = "Media submitted successfully!"

        return jsonify({
            "success": True,
            "message": message,
            "redirect_url": url_for("main.index", game_id=game.id, quest_id=quest_id),
            "mastodon_url": mastodon_url,
            "activity": activity
        }), 200

    return render_template("submit_photo.html", form=form, quest=quest, quest_id=quest_id)


def allowed_file(filename):
    """
    Check if the filename has an allowed extension.

    Args:
        filename (str): The file name.
    """
    allowed_extensions = {"png", "jpg", "jpeg", "gif", "mp4", "webm", "mov"}
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


@quests_bp.errorhandler(RequestEntityTooLarge)
def handle_large_file_error(_error):
    """
    Handle errors when the uploaded file is too large.

    Args:
        _error (Exception): The exception raised.
    """
    return "File too large", 413


@quests_bp.route("/quest/my_submissions", methods=["GET"])
@login_required
def get_user_submissions():
    """Retrieve submissions for the logged in user."""

    submissions = QuestSubmission.query.filter_by(user_id=current_user.id).all()
    submissions_data = [
        {
            "id": submission.id,
            "image_url": public_media_url(submission.image_url),
            "video_url": public_media_url(submission.video_url),
            "comment": submission.comment,
            "user_id": submission.user_id,
            "quest_id": submission.quest_id,
            "twitter_url": submission.twitter_url,
            "timestamp": submission.timestamp.isoformat(),
        }
        for submission in submissions
    ]
    return jsonify(submissions_data)


@quests_bp.route("/quest/delete_submission/<int:submission_id>", methods=["DELETE"])
@login_required
def delete_submission(submission_id):
    """
    Delete a submission by ID. Only the submission owner or an administrator can delete.

    Args:
        submission_id (int): The ID of the submission.
    """
    submission = QuestSubmission.query.get_or_404(submission_id)

    if not current_user.is_admin and submission.user_id != current_user.id:
        return jsonify({"success": False, "message": "Permission denied"}), 403

    user_quest = UserQuest.query.filter_by(
        user_id=submission.user_id, quest_id=submission.quest_id
    ).first()

    if user_quest:
        quest = db.session.get(Quest, submission.quest_id)
        user_quest.completions = max(user_quest.completions - 1, 0)
        if user_quest.completions == 0:
            user_quest.points_awarded = 0
        else:
            user_quest.points_awarded = max(user_quest.points_awarded - quest.points, 0)

        check_and_revoke_badges(submission.user_id, game_id=quest.game_id)
        db.session.commit()

                                                               
    SubmissionLike.query.filter_by(submission_id=submission.id).delete()
    SubmissionReply.query.filter_by(submission_id=submission.id).delete()

    db.session.delete(submission)
    db.session.commit()
    return jsonify({"success": True})


@quests_bp.route("/quest/all_submissions", methods=["GET"])
def get_all_submissions():
    """Return paginated submissions for a game.

    Query Parameters:
        game_id (int): The ID of the game.
        offset  (int): Starting index for pagination (default 0).
        limit   (int): Number of submissions to return (default 10).
    """

    game_id = get_int_param("game_id", min_value=1)
    offset = get_int_param("offset", default=0, min_value=0)
    limit = get_int_param("limit", default=10, min_value=1)

    if game_id is None:
        return

    limit = max(1, min(limit, 100))

    query = (
        QuestSubmission.query
        .join(Quest, QuestSubmission.quest_id == Quest.id)
        .join(User, QuestSubmission.user_id == User.id)
        .filter(Quest.game_id == game_id)
        .order_by(QuestSubmission.timestamp.desc())
    )

    submissions = query.offset(offset).limit(limit + 1).all()

    has_more = len(submissions) > limit
    submissions = submissions[:limit]

    if not submissions:
        return jsonify({"submissions": [], "has_more": False, "is_admin": current_user.is_admin})

    submissions_data = [
        {
            "id": submission.id,
            "quest_id": submission.quest_id,
            "user_id": submission.user_id,
            "user_display_name": submission.user.display_name or submission.user.username,
            "user_username": submission.user.username,
            "user_profile_picture": (
                url_for('static', filename=submission.user.profile_picture)
                if submission.user.profile_picture
                else url_for('static', filename=current_app.config['PLACEHOLDER_IMAGE'])
            ),
            "image_url": public_media_url(submission.image_url),
            "video_url": public_media_url(submission.video_url),
            "comment": submission.comment,
            "timestamp": submission.timestamp.strftime("%Y-%m-%d %H:%M"),
            "twitter_url": submission.twitter_url,
            "fb_url": submission.fb_url,
            "instagram_url": submission.instagram_url,
        }
        for submission in submissions
    ]

    return jsonify(
        {
            "submissions": submissions_data,
            "is_admin": current_user.is_admin,
            "has_more": has_more,
        }
    )


@quests_bp.route("/quest/<int:quest_id>")
@login_required
def quest_details(quest_id):
    """
    Get details of a specific quest.

    Args:
        quest_id (int): The ID of the quest.
    """
    if not current_user.is_authenticated:
        return

    quest = Quest.query.get_or_404(quest_id)
    quest_data = {
        "id": quest.id,
        "title": quest.title,
        "description": quest.description,
        "due_date": quest.due_date.isoformat(),
        "status": quest.status,
    }
    return jsonify({"quest": quest_data})


@quests_bp.route("/game/<int:game_id>/delete_all", methods=["DELETE"])
@login_required
def delete_all_quests(game_id):
    """
    Delete all quests associated with a game. Only the game administrator is allowed.

    Args:
        game_id (int): The ID of the game.
    """
    Game.query.get_or_404(game_id)

    if not current_user.is_admin_for_game(game_id):
        return (
            jsonify(
                {
                    "success": False,
                    "message": "You do not have permission to delete quests for this game.",
                }
            ),
            403,
        )

    try:
        Quest.query.filter_by(game_id=game_id).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({"success": True, "message": "All quests deleted successfully."}), 200
    except Exception:
        db.session.rollback()
        return


@quests_bp.route("/game/<int:game_id>/clear_calendar", methods=["DELETE"])
@login_required
def clear_calendar_quests(game_id):
    """Remove all upcoming calendar quests for a game."""
    Game.query.get_or_404(game_id)

    if not current_user.is_admin_for_game(game_id):
        return (
            jsonify({"success": False, "message": "You do not have permission to clear quests for this game."}),
            403,
        )

    now = datetime.now(UTC)
    upcoming = Quest.query.filter(
        Quest.game_id == game_id,
        Quest.from_calendar.is_(True),
        (Quest.calendar_event_start.is_(None) | (Quest.calendar_event_start >= now)),
    ).all()

    for q in upcoming:
        db.session.delete(q)

    try:
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as exc:
        current_app.logger.error(
            "Failed to clear calendar quests for game %s: %s",
            game_id,
            format_db_error(exc),
        )
        db.session.rollback()
        return jsonify({"success": False, "message": "Failed to clear quests."}), 500


@quests_bp.route("/game/<int:game_id>/get_title", methods=["GET"])
@login_required
def get_game_title(game_id):
    """
    Retrieve the title of a game. Only accessible by the game administrator.

    Args:
        game_id (int): The ID of the game.
    """
    game = Game.query.get_or_404(game_id)

    if not current_user.is_admin_for_game(game_id):
        return jsonify(
            {"success": False, "message": "You do not have permission to view this game."}
        ), 403

    return jsonify({"title": game.title})


@quests_bp.route('/submissions/<int:submission_id>')
@login_required
def get_submission(submission_id):
    sub = db.session.get(QuestSubmission, submission_id)
    if not sub:
        abort(404)
    user = db.session.get(User, sub.user_id)

                                                                     
    if user.profile_picture:
        pic_url = url_for('static', filename=user.profile_picture)
    else:
        pic_url = url_for('static', filename=current_app.config['PLACEHOLDER_IMAGE'])

    display_name = user.display_name or user.username

    liked = bool(SubmissionLike.query.filter_by(
            submission_id=submission_id,
            user_id=current_user.id
        ).first())
    like_count = sub.likes.count()
    
    return jsonify({
        'id': submission_id,
        'url':                  public_media_url(sub.image_url or sub.video_url),
        'image_url':            public_media_url(sub.image_url),
        'video_url':            public_media_url(sub.video_url),
        'comment':              sub.comment,
        'user_id':              sub.user_id,
        'user_profile_picture': pic_url,
        'user_display_name':    display_name,
        'user_username':        user.username,
        'twitter_url':          sub.twitter_url,
        'fb_url':               sub.fb_url,
        'instagram_url':        sub.instagram_url,
        'like_count':           like_count,
        'liked_by_current_user': liked
    })


@quests_bp.route('/submission/<int:submission_id>/comment', methods=['PUT'])
@login_required
def update_submission_comment(submission_id):
    """
    Allow the original submitter to edit their comment.
    """
    sub = QuestSubmission.query.get_or_404(submission_id)

                             
    if sub.user_id != current_user.id:
        abort(403, description="Permission denied: cannot edit another user's comment.")

    data = request.get_json() or {}
    new_comment = sanitize_html(data.get('comment', ''))
    sub.comment = new_comment

    MAX_LEN = 1000
    if len(sub.comment) > MAX_LEN:
        sub.comment = sub.comment[:MAX_LEN]

    db.session.commit()
    return jsonify(success=True, comment=sub.comment)


@quests_bp.route('/submission/<int:submission_id>/like', methods=['POST','DELETE'])
@login_required
def submission_like(submission_id):
    sub = QuestSubmission.query.get_or_404(submission_id)
    existing = SubmissionLike.query.filter_by(
        submission_id=submission_id,
        user_id=current_user.id
    ).first()

    if request.method == 'POST':
        if not existing:
            like = SubmissionLike(
                submission_id=submission_id,
                user_id=current_user.id
            )
            db.session.add(like)
            db.session.commit()

            post_activitypub_like_activity(sub, current_user)

                                                                   
            if sub.user_id != current_user.id:
                db.session.add(Notification(
                    user_id   = sub.user_id,
                    type      = 'submission_like',
                    payload   = {
                        'submission_id': submission_id,
                        'liker_id'     : current_user.id,
                        'liker_name'   : current_user.display_name or current_user.username
                    }
                ))
                db.session.commit()
        liked = True
    else:
        if existing:
            db.session.delete(existing)
            db.session.commit()
        liked = False

    count = sub.likes.count()
    return jsonify(success=True, liked=liked, like_count=count)


@quests_bp.route('/submission/<int:submission_id>/replies', methods=['GET', 'POST'])
@login_required
def submission_replies(submission_id):
    """
    GET: return up to 2 replies for a submission.
    POST: create a new reply (up to 2 per submission), fire ActivityPub Create.
    """
    sub = QuestSubmission.query.get_or_404(submission_id)

    if request.method == 'GET':
        reps = (SubmissionReply.query
                .filter_by(submission_id=submission_id)
                .order_by(SubmissionReply.timestamp.desc())
                .limit(10)
                .all())
        data = [{
            'id'           : r.id,
            'content'      : r.content,
            'timestamp'    : r.timestamp.isoformat(),
            'user_id'      : r.user_id,
            'user_display' : (r.user.display_name or r.user.username)
        } for r in reps]
        return jsonify(success=True, replies=data)

    if request.method == 'POST':
        if sub.user_id == current_user.id:
            return jsonify(
                success=False,
                message="You cannot comment on your own submission"
            ), 403

        payload = request.get_json() or {}
        content = payload.get('content','').strip()
        if not content:
            return jsonify(success=False, message="Empty reply"), 400

                                
        existing_count = SubmissionReply.query.filter_by(
            submission_id=submission_id
        ).count()
        if existing_count >= 10:
            return jsonify(success=False,
                           message="Reply limit of 10 reached"), 403

        reply = SubmissionReply(
            submission_id=submission_id,
            user_id=current_user.id,
            content=content
        )
        db.session.add(reply)
        db.session.commit()

    if sub.user_id != current_user.id:
        db.session.add(Notification(
            user_id   = sub.user_id,
            type      = 'submission_reply',
            payload   = {
                'submission_id': submission_id,
                'reply_id'     : reply.id,
                'actor_id'     : current_user.id,
                'actor_name'   : current_user.display_name or current_user.username,
                'content'      : reply.content
            }
        ))
        db.session.commit()

                              
    post_activitypub_comment_activity(reply, current_user)

    return jsonify(
      success=True,
      reply={
        'id'           : reply.id,
        'content'      : reply.content,
        'timestamp'    : reply.timestamp.isoformat(),
        'user_id'      : reply.user_id,
        'user_display' : (current_user.display_name or current_user.username)
      }
    )


@quests_bp.route('/submission/<int:submission_id>/photo', methods=['PUT'])
@login_required
@limiter.limit("10/minute", key_func=user_or_ip)
@limiter.limit("50/minute")
def update_submission_photo(submission_id):
    sub = QuestSubmission.query.get_or_404(submission_id)
                            
    if sub.user_id != current_user.id:
        abort(403)

                                
    photo = request.files.get('photo')
    video = request.files.get('video')
    if photo and photo.filename:
        new_path = save_submission_image(photo)
        sub.image_url = new_path
    elif video and video.filename:
        try:
            new_path = save_submission_video(video)
        except ValueError as ve:
            current_app.logger.error("Error saving submission video: %s", str(ve))
            return jsonify(success=False, message="An error occurred while processing the video."), 400
        sub.video_url = new_path
    else:
        return jsonify(success=False, message='No file uploaded'), 400

    db.session.commit()
    return jsonify(
        success=True,
        image_url=public_media_url(sub.image_url),
        video_url=public_media_url(sub.video_url)
    )
