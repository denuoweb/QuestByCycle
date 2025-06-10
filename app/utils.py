import uuid
import os
import subprocess
import shutil
import csv
import io
from html_sanitizer import Sanitizer
import smtplib
from flask import current_app, request, url_for
from .models import (
    db,
    Quest,
    Badge,
    Game,
    UserQuest,
    User,
    ShoutBoardMessage,
    QuestSubmission,
    UserIP,
)
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from app.constants import UTC, FREQUENCY_DELTA
from PIL import Image, ExifTags, UnidentifiedImageError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from textwrap import dedent


def _get_ffmpeg_bin() -> str | None:
    """Return the path to a usable ffmpeg binary or ``None`` if unavailable."""
    ffmpeg_bin = current_app.config.get("FFMPEG_PATH") or shutil.which("ffmpeg")
    if ffmpeg_bin and (
        (os.path.isabs(ffmpeg_bin) and os.path.exists(ffmpeg_bin))
        or shutil.which(ffmpeg_bin)
    ):
        return ffmpeg_bin
    return None

ALLOWED_TAGS = {
    'a', 'b', 'i', 'u', 'em', 'strong', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre', 'br', 'div', 'span', 'ul', 'ol', 'li', 'hr',
    'sub', 'sup', 's', 'strike', 'font', 'img', 'video', 'figure'
}

_ATTRS = {
    'a': {'href', 'title', 'target', 'rel', 'class', 'id'},
    'img': {'src', 'alt', 'width', 'height', 'class', 'id'},
    'video': {'src', 'width', 'height', 'controls', 'class', 'id'},
    'font': {'color', 'face', 'size', 'class', 'id'},
}
for _tag in ALLOWED_TAGS:
    _ATTRS.setdefault(_tag, set()).update({'class', 'id'})

SANITIZER = Sanitizer({
    'tags': ALLOWED_TAGS,
    'attributes': _ATTRS,
    'empty': {'br', 'hr', 'img'},
    'separate': {'a', 'p', 'li'},
    'whitespace': {'br'},
})

def sanitize_html(html_content: str) -> str:
    return SANITIZER.sanitize(html_content)


                                                
MAX_POINTS_INT = 2**63 - 1
                                                                 
ALLOWED_IMAGE_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'heif', 'heic'
}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov'}

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_VIDEO_BYTES = 10 * 1024 * 1024
                                                       
REQUEST_TIMEOUT = 5


def allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
    """Return True if ``filename`` has an allowed extension."""
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in allowed_extensions
    )


def allowed_image_file(filename: str) -> bool:
    """Return True if the filename has an allowed image extension."""
    return allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS)


def allowed_video_file(filename: str) -> bool:
    """Return True if the filename has an allowed video extension."""
    return allowed_file(filename, ALLOWED_VIDEO_EXTENSIONS)


def correct_image_orientation(img: Image.Image) -> Image.Image:
    """Return a copy of ``img`` with EXIF orientation applied if present."""
    tag = next((t for t, v in ExifTags.TAGS.items() if v == "Orientation"), None)
    if not tag:
        return img
    try:
        exif = img._getexif()
        if exif:
            orientation = exif.get(tag)
            rotation = {3: 180, 6: -90, 8: 90}.get(orientation)
            if rotation:
                img = img.rotate(rotation, expand=True)
    except Exception:
        pass
    return img


def save_image_file(
    image_file,
    subpath,
    *,
    allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
    old_filename=None,
    output_ext=None,
):
    """Save ``image_file`` under ``static/<subpath>``.

    ``subpath`` should be a path relative to the ``static`` directory.
    Optionally delete ``old_filename`` (also relative to ``static``).
    If ``output_ext`` is provided, the saved file will use that extension.
    """

    if not image_file or not getattr(image_file, "filename", None):
        raise ValueError("Invalid file object passed.")

    image_file.seek(0, os.SEEK_END)
    size = image_file.tell()
    image_file.seek(0)
    if size > MAX_IMAGE_BYTES:
        raise ValueError("Image exceeds 8 MB limit")

    ext = image_file.filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed_extensions:
        raise ValueError("File extension not allowed.")

    if output_ext:
        ext = output_ext.lstrip(".").lower()

    filename = secure_filename(f"{uuid.uuid4()}.{ext}")
    upload_dir = os.path.join(current_app.static_folder, subpath)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    image_file.save(file_path)

    # Normalize orientation for common image types
    try:
        with Image.open(file_path) as img:
            corrected = correct_image_orientation(img)
            if corrected is not img:
                corrected.save(file_path)
    except UnidentifiedImageError:
        pass

    if old_filename:
        old_path = os.path.join(current_app.static_folder, old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)

    return os.path.join(subpath, filename)


def save_leaderboard_image(image_file):
    try:
        return save_image_file(image_file, os.path.join('images', 'leaderboard'))
    except Exception as e:                                             
        raise ValueError(f"Failed to save image: {str(e)}") from e

def create_smog_effect(image, smog_level):
    smog_overlay = Image.new('RGBA', image.size, (169, 169, 169, int(255 * smog_level)))
    smog_image = Image.alpha_composite(image.convert('RGBA'), smog_overlay)
    return smog_image

def generate_smoggy_images(image_path, game_id):
    try:
        original_image = Image.open(image_path)

        for i in range(10):
            smog_level = i / 9.0
            smoggy_image = create_smog_effect(original_image, smog_level)
            dest = os.path.join(
                current_app.root_path,
                f"static/images/leaderboard/smoggy_skyline_{game_id}_{i}.png",
            )
            smoggy_image.save(dest)
    except Exception as e:
        raise ValueError(f"Failed to generate smoggy images: {str(e)}")

def update_user_score(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return False

                                                        
        total_points = sum(
            quest.points_awarded
            for quest in user.user_quests
            if quest.points_awarded is not None
        )

                                                                            
        user.score = min(total_points, MAX_POINTS_INT)

                                        
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()                                     
        return False


def save_profile_picture(profile_picture_file, old_filename=None):
    uploads = current_app.config['main']['UPLOAD_FOLDER']
    return save_image_file(profile_picture_file, uploads, old_filename=old_filename)


def save_badge_image(image_file):
    try:
        return os.path.basename(
            save_image_file(
                image_file,
                os.path.join('images', 'badge_images'),
                output_ext='png',
            )
        )
    except Exception as e:
        raise ValueError(f"Failed to save image: {str(e)}") from e


def save_bicycle_picture(bicycle_picture_file, old_filename=None):
    subdir = os.path.join(
        current_app.config['main']['UPLOAD_FOLDER'], 'bicycle_pictures'
    )
    return save_image_file(
        bicycle_picture_file,
        subdir,
        old_filename=old_filename,
    )


def save_submission_image(submission_image_file):
    try:
        return save_image_file(
            submission_image_file, os.path.join('images', 'verifications')
        )
    except Exception as e:
        current_app.logger.error(f"Failed to save image: {e}")
        raise


def save_submission_video(submission_video_file):
    """Save an uploaded video for quest verification.

    The uploaded file is converted to H.264 MP4 with basic compression using
    ``ffmpeg``. Videos over ``MAX_VIDEO_BYTES`` are rejected before conversion
    and again after compression to ensure storage limits are respected.
    """
    try:
                                          
        submission_video_file.seek(0, os.SEEK_END)
        size = submission_video_file.tell()
        submission_video_file.seek(0)
        current_app.logger.debug(
            "Uploaded video size: %s bytes for file '%s'",
            size,
            submission_video_file.filename,
        )
        if size > MAX_VIDEO_BYTES:
            raise ValueError("Video exceeds 10 MB limit")

                                                
        ext = submission_video_file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            raise ValueError("File extension not allowed.")
        tmp_dir = os.path.join(current_app.static_folder, 'videos', 'tmp')
        os.makedirs(tmp_dir, exist_ok=True)
        orig_name = secure_filename(f"{uuid.uuid4()}_orig.{ext}")
        orig_path = os.path.join(tmp_dir, orig_name)
        current_app.logger.debug("Saving original upload to %s", orig_path)
        submission_video_file.save(orig_path)

                                           
        uploads_dir = os.path.join(
            current_app.static_folder, "videos", "verifications"
        )
        os.makedirs(uploads_dir, exist_ok=True)

        ffmpeg_bin = _get_ffmpeg_bin()

        if not ffmpeg_bin:
            current_app.logger.warning(
                "ffmpeg not found, saving video without conversion"
            )
            final_name = secure_filename(f"{uuid.uuid4()}.{ext}")
            final_path = os.path.join(uploads_dir, final_name)
            shutil.move(orig_path, final_path)
        else:
            final_name = secure_filename(f"{uuid.uuid4()}.mp4")
            final_path = os.path.join(uploads_dir, final_name)
            ffmpeg_cmd = [
                ffmpeg_bin,
                "-i",
                orig_path,
                "-vf",
                "scale='min(1280,iw)':-2",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "28",
                "-c:a",
                "aac",
                "-movflags",
                "faststart",
                "-y",
                final_path,
            ]
            current_app.logger.debug(
                "Running ffmpeg command: %s", " ".join(ffmpeg_cmd)
            )
            try:
                subprocess.run(
                    ffmpeg_cmd,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except subprocess.CalledProcessError as e:
                stderr_output = e.stderr.decode(errors="ignore") if e.stderr else ""
                current_app.logger.error("ffmpeg failed: %s", stderr_output)
                os.remove(orig_path)
                current_app.logger.debug("Removed temporary upload %s", orig_path)
                raise ValueError("Invalid or corrupted video file") from e

            os.remove(orig_path)
            current_app.logger.debug("Removed temporary upload %s", orig_path)

            final_size = os.path.getsize(final_path)
            current_app.logger.debug("Compressed video size: %s bytes", final_size)
            if final_size > MAX_VIDEO_BYTES:
                os.remove(final_path)
                current_app.logger.debug(
                    "Compressed video exceeded max size and was deleted"
                )
                raise ValueError("Video exceeds 10 MB limit after compression")

        return os.path.join('videos', 'verifications', final_name)
    except Exception as e:
        current_app.logger.error(f"Failed to save video: {e}")
        raise




def public_media_url(path: str | None) -> str | None:
    "Return a publicly accessible URL for a stored media path."
    if not path:
        return None
    if path.startswith(("http://", "https://", "/static/")):
        return path
    filename = path.lstrip("/")
    filename = filename.removeprefix("static/")
    return url_for("static", filename=filename)

def save_sponsor_logo(image_file, old_filename=None):
    if not image_file or not image_file.filename:
        raise ValueError("Invalid file type or no file provided.")

    try:
        return save_image_file(
            image_file,
            os.path.join('images', 'sponsors'),
            old_filename=old_filename,
        )
    except Exception as e:
        raise ValueError(f"Failed to save image: {str(e)}") from e


def can_complete_quest(user_id, quest_id):
    now = datetime.now(UTC)
    quest = Quest.query.get(quest_id)
    
    if not quest:
        return False, None                        
    
                                                                   
    period_start = now - FREQUENCY_DELTA.get(quest.frequency, timedelta(days=1))
                                             
    completions_within_period = QuestSubmission.query.filter(
        QuestSubmission.user_id == user_id,
        QuestSubmission.quest_id == quest_id,
        QuestSubmission.timestamp >= period_start
    ).count()

                                                  
    can_verify = completions_within_period < quest.completion_limit
    next_eligible_time = None
    if not can_verify:
        first_completion_in_period = QuestSubmission.query.filter(
            QuestSubmission.user_id == user_id,
            QuestSubmission.quest_id == quest_id,
            QuestSubmission.timestamp >= period_start
        ).order_by(QuestSubmission.timestamp.asc()).first()

        if first_completion_in_period:
                                                                                          
            next_eligible_time = (
                first_completion_in_period.timestamp
                + FREQUENCY_DELTA.get(quest.frequency, timedelta(days=1))
            )

    return can_verify, next_eligible_time


def getLastRelevantCompletionTime(user_id, quest_id):
    now = datetime.now(UTC)
    quest = Quest.query.get(quest_id)
    
    if not quest:
        return None                        

                                                                
    period_start = now - FREQUENCY_DELTA.get(quest.frequency, timedelta(0))


                                                               
    last_relevant_completion = QuestSubmission.query.filter(
        QuestSubmission.user_id == user_id,
        QuestSubmission.quest_id == quest_id,
        QuestSubmission.timestamp >= period_start
    ).order_by(QuestSubmission.timestamp.desc()).first()

    return last_relevant_completion.timestamp if last_relevant_completion else None

def check_and_award_badges(user_id, quest_id, game_id):
    """
    Award badges for a quest:
      - For quest-specific badges: Award if the user’s completions for the quest 
        reach or exceed quest.badge_awarded.
      - For category badges: Award if the user has at least one completion on 
        every quest in that category for the specified game.
    All awards and associated shoutboard messages are tied to the given game_id.
    """
    user = User.query.get(user_id)
    quest = Quest.query.get(quest_id)
    user_quest = UserQuest.query.filter_by(user_id=user_id, quest_id=quest_id).first()
    if not user_quest:
        return

                                           
    if quest.badge and user_quest.completions >= quest.badge_awarded:
                                                                                
        existing_award = ShoutBoardMessage.query.filter_by(
            user_id=user_id,
            game_id=game_id
        ).filter(ShoutBoardMessage.message.contains(f"data-badge-id='{quest.badge.id}'")).first()
        if not existing_award:
                                             
            user.badges.append(quest.badge)
            msg = (
                " earned the badge"
                "<a class='quest-title' href='javascript:void(0);' "
                "onclick='openBadgeModal(this)' "
                f"data-badge-id='{quest.badge.id}' "
                f"data-badge-name='{quest.badge.name}' "
                f"data-badge-description='{quest.badge.description}' "
                f"data-badge-image='{quest.badge.image}' "
                f"data-task-name='{quest.title}' "
                f"data-badge-awarded-count='{quest.badge_awarded}' "
                f"data-task-id='{quest.id}' "
                f"data-user-completions='{user_quest.completions}'>"
                f"{quest.badge.name}</a>for completing quest "
                "<a class='quest-title' href='javascript:void(0);' "
                f"onclick='openQuestDetailModal({quest.id})'>"
                f"{quest.title}</a>"
            )
            sbm = ShoutBoardMessage(message=msg, user_id=user_id, game_id=game_id)
            db.session.add(sbm)
            db.session.commit()

                                           
    if quest.category and game_id:
                                                                
        category_quests = Quest.query.filter_by(
            category=quest.category,
            game_id=game_id,
        ).all()
        if not category_quests:
            return
                                                                               
        completed_quests = [
            ut.quest
            for ut in user.user_quests
            if (
                ut.quest.category == quest.category
                and ut.quest.game_id == game_id
                and ut.completions >= 1
            )
        ]
                                                                             
        if len(completed_quests) == len(category_quests):
                                                    
            category_badges = Badge.query.filter_by(category=quest.category).all()
            for badge in category_badges:
                                                                                           
                existing_award = ShoutBoardMessage.query.filter_by(
                    user_id=user_id,
                    game_id=game_id
                ).filter(ShoutBoardMessage.message.contains(f"data-badge-id='{badge.id}'")).first()
                if not existing_award:
                    url = url_for(
                        'static',
                        filename=f'images/badge_images/{badge.image}'
                    )
                    user.badges.append(badge)
                    msg = (
                        " earned the badge "
                        "<a class='quest-title' href='javascript:void(0);' "
                        "onclick='openBadgeModal(this)' "
                        f"data-badge-id='{badge.id}' "
                        f"data-badge-name='{badge.name}' "
                        f"data-badge-description='{badge.description}' "
                        f"data-badge-image='{url}' "
                        f"data-task-name='{quest.title}' "
                        "data-badge-awarded-count='1' "
                        f"data-task-id='{quest.id}' "
                        f"data-user-completed='{len(completed_quests)}' "
                        f"data-total-tasks='{len(category_quests)}'>"
                        f"{badge.name}</a> for completing all quests in category "
                        f"'{quest.category}'"
                    )
                    sbm = ShoutBoardMessage(
                        message=msg,
                        user_id=user_id,
                        game_id=game_id,
                    )
                    db.session.add(sbm)
                    db.session.commit()


def check_and_revoke_badges(user_id, game_id=None):
    """
    Revoke badges awarded to the user if the tasks in the specified game no
    longer meet the required conditions.
      - Quest-specific badges are revoked if the user’s completions for any
        awarding quest fall below ``quest.badge_awarded``.
      - Category badges are revoked if the user has not completed at least one
        of every quest in that badge’s category for the specified game.
    When revoking a badge, its associated shoutboard award message is deleted.
    """
    user = User.query.get(user_id)
    if not user:
        return

    badges_to_remove = []
    for badge in user.badges:
        if badge.category:
                                                                                       
            current_category_quests = Quest.query.filter_by(
                category=badge.category,
                game_id=game_id,
            ).all()
            completed_quests = {
                ut.quest
                for ut in user.user_quests
                if (
                    ut.quest.category == badge.category
                    and ut.quest.game_id == game_id
                    and ut.completions >= 1
                )
            }
            if set(current_category_quests) != set(completed_quests):
                badges_to_remove.append(badge)
        else:
                                                                                                                
            all_met = True
            for quest in badge.quests:
                user_quest = UserQuest.query.filter_by(
                    user_id=user_id,
                    quest_id=quest.id,
                ).first()
                if not user_quest or user_quest.completions < quest.badge_awarded:
                    all_met = False
                    break
            if not all_met:
                badges_to_remove.append(badge)

    for badge in badges_to_remove:
        user.badges.remove(badge)
                                                                               
        messages = ShoutBoardMessage.query.filter_by(
            user_id=user_id,
            game_id=game_id,
        ).all()
        for message in messages:
            if f"data-badge-id='{badge.id}'" in message.message:
                db.session.delete(message)
        db.session.commit()


def enhance_badges_with_task_info(badges, game_id=None, user_id=None):
    """
    Enhance each badge with aggregated task information from its awarding quests.
    If a game_id is provided, only quests in that game are considered.
    If user_id is provided, the function computes the maximum completions among
    those quests and a flag indicating if any quest’s threshold is met.
    Returns a list of dictionaries with:
      - id, name, description, image, category,
      - task_names: comma‑separated quest titles,
      - task_ids: comma‑separated quest IDs,
      - badge_awarded_counts: comma‑separated thresholds,
      - user_completions: maximum completions among awarding quests,
      - is_complete: True if any quest’s threshold is met.
    """
    enhanced_badges = []
    for badge in badges:
        if game_id:
            awarding_quests = [
                quest
                for quest in badge.quests
                if quest.game_id == game_id
            ]
        else:
            awarding_quests = badge.quests

        if awarding_quests:
            task_names = ", ".join(quest.title for quest in awarding_quests)
            task_ids = ", ".join(str(quest.id) for quest in awarding_quests)
            badge_awarded_counts = ", ".join(
                str(quest.badge_awarded) for quest in awarding_quests
            )
        else:
            task_names = ""
            task_ids = ""
            badge_awarded_counts = "1"

        user_completions_total = 0
        is_complete = False
        if awarding_quests and user_id:
            completions_list = []
            for quest in awarding_quests:
                user_quest = UserQuest.query.filter_by(
                    user_id=user_id,
                    quest_id=quest.id,
                ).first()
                completions = user_quest.completions if user_quest else 0
                completions_list.append(completions)
                if completions >= quest.badge_awarded:
                    is_complete = True
            user_completions_total = max(completions_list) if completions_list else 0

        enhanced_badges.append({
            'id': badge.id,
            'name': badge.name,
            'description': badge.description,
            'image': badge.image,
            'category': badge.category,
            'task_names': task_names,
            'task_ids': task_ids,
            'badge_awarded_counts': badge_awarded_counts,
            'user_completions': user_completions_total,
            'is_complete': is_complete
        })
    return enhanced_badges


def send_email(to: str,
               subject: str,
               html_content: str,
               inline_images: list[tuple[str, bytes, str]] | None = None) -> bool:
    """
    Send an e-mail (via the Postfix SMTP settings in Flask config).

    Parameters
    ----------
    to : str
        Recipient address.
    subject : str
        Mail subject line.
    html_content : str
        Fully-rendered HTML body *that already contains* <img src="cid:XXX"> tags.
    inline_images : list[tuple[cid, data, mime_subtype]]
        Optional list where each element is:
            cid           the Content-ID without angle brackets
            data          raw image bytes
            mime_subtype  e.g. 'jpeg', 'png', …

    Returns
    -------
    bool
        True if the message was sent without raising; False otherwise.
    """
                                                                       
    msg_root        = MIMEMultipart('related')
    msg_root['Subject'] = subject
    msg_root['From']    = current_app.config['MAIL_DEFAULT_SENDER']
    msg_root['To']      = to

                                                               
    alt_part = MIMEMultipart('alternative')
    msg_root.attach(alt_part)
    alt_part.attach(MIMEText(html_content, 'html'))

                                        
    inline_images = inline_images or []
    for cid, data, subtype in inline_images:
        img = MIMEImage(data, _subtype=subtype)
        img.add_header('Content-ID', f'<{cid}>')
        img.add_header('Content-Disposition', 'inline', filename=f'{cid}.{subtype}')
        msg_root.attach(img)

                                                                               
    try:
        mail_server   = current_app.config.get('MAIL_SERVER')
        mail_port     = current_app.config.get('MAIL_PORT')
        use_tls       = current_app.config.get('MAIL_USE_TLS', False)
        use_ssl       = current_app.config.get('MAIL_USE_SSL', False)
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')

        smtp_conn = (
            smtplib.SMTP_SSL(mail_server, mail_port)
            if use_ssl else
            smtplib.SMTP(mail_server, mail_port)
        )
        smtp_conn.ehlo()
        if use_tls:
            smtp_conn.starttls()
            smtp_conn.ehlo()
        if mail_username and mail_password:
            smtp_conn.login(mail_username, mail_password)

        smtp_conn.sendmail(msg_root['From'], [to], msg_root.as_string())
        smtp_conn.quit()
        current_app.logger.info('Email sent successfully to %s.', to)
        return True

    except Exception as exc:                                        
        current_app.logger.error('Failed to send email: %s', exc)
        return False


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
        Submit Verification: After uploading your verification photo and adding a
        comment, click the "Submit Verification" button. You should receive a
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
        awards="""
        Stay tuned for prizes...
        """,
        beyond="Visit your local bike club!",
        admin_id=1,                                           
        is_demo=True,
        twitter_username=current_app.config['TWITTER_USERNAME'],
        twitter_api_key=current_app.config['TWITTER_API_KEY'],
        twitter_api_secret=current_app.config['TWITTER_API_SECRET'],
        twitter_access_token=current_app.config['TWITTER_ACCESS_TOKEN'],
        twitter_access_token_secret=current_app.config['TWITTER_ACCESS_TOKEN_SECRET'],
        facebook_app_id=current_app.config['FACEBOOK_APP_ID'],
        facebook_app_secret=current_app.config['FACEBOOK_APP_SECRET'],
        facebook_access_token=current_app.config['FACEBOOK_ACCESS_TOKEN'],
        facebook_page_id=current_app.config['FACEBOOK_PAGE_ID'],
        instagram_access_token=current_app.config['INSTAGRAM_ACCESS_TOKEN'],
        instagram_user_id=current_app.config['INSTAGRAM_USER_ID'],
        is_public=True,
        allow_joins=True,
        leaderboard_image="leaderboard_image.png"                                                     
    )
    db.session.add(demo_game)
    admin_user = User.query.get(1)
    if admin_user:
        demo_game.admins.append(admin_user)
    db.session.commit()

                                                
    import_quests_and_badges_from_csv(
        demo_game.id,
        os.path.join(current_app.static_folder, 'defaultquests.csv'),
    )

                                   
    try:
        admin_id = 1                                           
        pinned_message = ShoutBoardMessage(
            message="Get on your Bicycle this Quarter!",
            user_id=admin_id,
            game_id=demo_game.id,
            is_pinned=True,
            timestamp=datetime.now(UTC)
        )
        db.session.add(pinned_message)
        db.session.commit()
    except Exception:
        db.session.rollback()

    return demo_game


def import_quests_and_badges_from_csv(game_id, csv_path):
    try:
        with open(csv_path, mode='r', encoding='utf-8') as csv_file:
            data = csv.DictReader(csv_file)
            for row in data:
                badge_name = sanitize_html(row['badge_name'])
                badge_description = sanitize_html(row['badge_description'])
                
                                                                        
                if 'badge_image_filename' in row and row['badge_image_filename']:
                    badge_image_filename = row['badge_image_filename']
                else:
                    badge_image_filename = (
                        f"{badge_name.lower().replace(' ', '_')}.png"
                    )
                
                badge_image_path = os.path.join(
                    current_app.static_folder,
                    'images',
                    'badge_images',
                    badge_image_filename,
                )

                if not os.path.exists(badge_image_path):
                    continue

                badge = Badge.query.filter_by(name=badge_name).first()
                if not badge:
                    badge = Badge(
                        name=badge_name,
                        description=badge_description,
                        image=badge_image_filename                                         
                    )
                    db.session.add(badge)
                    db.session.flush()
                quest = Quest(
                    category=sanitize_html(row['category']),
                    title=sanitize_html(row['title']),
                    description=sanitize_html(row['description']),
                    tips=sanitize_html(row['tips']),
                    points=int(row['points'].replace(',', '')),
                    badge_awarded=int(row['badge_awarded']),
                    completion_limit=int(row['completion_limit']),
                    frequency=sanitize_html(row['frequency']),
                    verification_type=sanitize_html(row['verification_type']),
                    badge_id=badge.id,
                    game_id=game_id
                )
                db.session.add(quest)
            db.session.commit()
    except Exception:
        db.session.rollback()


def log_user_ip(user):
                                                              
    ip_address = request.remote_addr
    existing_ip = UserIP.query.filter_by(user_id=user.id, ip_address=ip_address).first()

    if not existing_ip:
                                                    
        new_ip = UserIP(user_id=user.id, ip_address=ip_address)
        db.session.add(new_ip)
        db.session.commit()


def get_game_badges(game_id):
    game = Game.query.get(game_id)
    if not game:
        return []

    badges = (
        Badge.query.join(Quest)
        .filter(Quest.game_id == game_id, Quest.badge_id.isnot(None))
        .distinct()
        .all()
    )
    return badges


def send_social_media_liaison_email(
    game_id: int,
    fallback_to_last: bool = False,
    last_limit: int = 5,
) -> bool:
    """
    Sends an email to the social media liaison for the specified game,
    reporting all ``QuestSubmissions`` that have occurred since the last email
    (or the game ``start_date``).
    
    Returns True if an email was sent, False otherwise.
    """
                                                                                           
    try:
                                                              
                                                          
        game = Game.query.get(game_id)
    except Exception as e:
        current_app.logger.error(
            f"Database error while fetching Game id={game_id}: {e}"
        )
        return False

    if game is None:
        current_app.logger.warning(
            f"No Game found with id={game_id}. Aborting social media email."
        )
        return False

                                                    
    liaison_email = game.social_media_liaison_email
    if not liaison_email:
        current_app.logger.warning(
            f"Game id={game_id} has no social_media_liaison_email. Aborting email."
        )
        return False

                                                                         
    cutoff_time = game.last_social_media_email_sent or game.start_date
                                                                                
    if cutoff_time.tzinfo is None or cutoff_time.tzinfo.utcoffset(cutoff_time) is None:
        cutoff_time = cutoff_time.replace(tzinfo=UTC)

                                                          
    try:
        submissions = (
            QuestSubmission.query
            .join(Quest, Quest.id == QuestSubmission.quest_id)
            .join(User, User.id == QuestSubmission.user_id)
            .filter(
                Quest.game_id == game_id,
                QuestSubmission.timestamp > cutoff_time,
            )
            .order_by(QuestSubmission.timestamp.asc())                                      
            .all()
        )
    except Exception as e:
        current_app.logger.error(
            f"Database error fetching submissions for game_id={game_id}: {e}"
        )
        return False

    fallback_used = False

    if not submissions:
        current_app.logger.info(
            f"No new submissions since {cutoff_time.isoformat()} for game_id={game_id}."
        )
        if fallback_to_last:
            submissions = (
                QuestSubmission.query
                .join(Quest, Quest.id == QuestSubmission.quest_id)
                .join(User, User.id == QuestSubmission.user_id)
                .filter(
                    Quest.game_id == game_id,
                )
                .order_by(QuestSubmission.timestamp.desc())
                .limit(last_limit)
                .all()
            )
            submissions.reverse()                     
            if submissions:
                fallback_used = True
                current_app.logger.info(
                    "Using last %s submissions for game_id=%s due to empty new list.",
                    len(submissions),
                    game_id,
                )

    if not submissions:
        return False

                                          
                                                 
    now = datetime.now(UTC)
    header_title = "Recent submissions" if fallback_used else "New submissions"
    html_header = dedent(f"""\
        <h1>{header_title} for "{sanitize_html(game.title)}"</h1>
        <p><b>Time period:</b> {cutoff_time:%Y-%m-%d %H:%M %Z} →
        {now:%Y-%m-%d %H:%M %Z}</p>
        <p><b>Total {header_title.lower()}:</b> {len(submissions)}</p>
        <hr>
    """)
    html_parts = [html_header]
    inline_images: list[tuple[str, bytes, str]] = []

    social_submissions = [
        s for s in submissions if s.submitter.upload_to_socials
    ]
    nonsocial_submissions = [
        s for s in submissions if not s.submitter.upload_to_socials
    ]

    def append_submission(sub, idx):
                                                          
        quest = sub.quest
        user = sub.submitter

        safe_quest_title = (
            sanitize_html(quest.title)
            if quest and quest.title
            else "(Untitled Quest)"
        )
        safe_username = (
            sanitize_html(user.username)
            if user and user.username
            else "(Unknown User)"
        )

                                                 
        html_parts.append(dedent(f"""\
            <div style="margin-bottom:1.5rem">
              <h3>{idx}. Quest: {safe_quest_title}</h3>
              <p>User: {safe_username} &nbsp;|&nbsp; Submitted:
              {sub.timestamp:%Y-%m-%d %H:%M %Z}</p>
        """))

                                        
        if sub.comment:
            sanitized_comment = sanitize_html(sub.comment).replace("\n", "<br>")
            html_parts.append(f"<p><i>{sanitized_comment}</i></p>")

                                      
        if sub.image_url:
                                                                                   
            rel_path = sub.image_url.strip("/\\")
            if ".." in rel_path:
                current_app.logger.warning(
                    "Skipping image for submission id=%s due to suspicious path '%s'",
                    sub.id,
                    sub.image_url,
                )
            else:
                image_path = os.path.join(current_app.static_folder, rel_path)
                try:
                    with Image.open(image_path) as img:
                                                                     
                        max_size = (600, 600)
                        img.thumbnail(max_size, Image.Resampling.LANCZOS)

                        with io.BytesIO() as buffer:
                            img.convert("RGB").save(buffer, format="JPEG", quality=70)
                            img_bytes = buffer.getvalue()

                        cid = f"submission_{sub.id}"
                        inline_images.append((cid, img_bytes, "jpeg"))
                                                           
                        html_parts.append(
                            f'<img src="cid:{cid}" alt="submission image" '
                            f'style="max-width:300px;max-height:300px"><br>'
                        )
                except OSError as e:
                    current_app.logger.warning(
                        "Could not open or process image for submission id=%s "
                        "at %s: %s. Falling back to public URL.",
                        sub.id,
                        image_path,
                        e,
                    )
                                                      
                    try:
                                                               
                        with current_app.test_request_context():
                            public_url = url_for(
                                "static",
                                filename=rel_path,
                                _external=True,
                            )
                        html_parts.append(
                            f'<img src="{public_url}" alt="submission image"><br>'
                        )
                    except Exception as ue:
                        current_app.logger.error(
                            "Failed to generate public URL for image '%s': %s",
                            rel_path,
                            ue,
                        )

                                           
        html_parts.append("</div>")

    if social_submissions:
        html_parts.append("<h2>Submissions opted for social sharing</h2>")
        for idx, sub in enumerate(social_submissions, start=1):
            append_submission(sub, idx)

    if nonsocial_submissions:
        html_parts.append("<hr>")
        html_parts.append("<h2>Submissions not opted for social sharing</h2>")
        for idx, sub in enumerate(nonsocial_submissions, start=1):
            append_submission(sub, idx)

                                              
    html_body = "<html><body>\n" + "\n".join(html_parts) + "\n</body></html>"

                             
    subject = f"New submissions for \"{game.title}\" – {now:%Y-%m-%d %H:%M %Z}"

                                  
    try:
        sent = send_email(
            to=liaison_email,
            subject=subject,
            html_content=html_body,
            inline_images=inline_images,
        )
    except Exception as e:
        current_app.logger.error(
            "Exception when sending email to '%s': %s",
            liaison_email,
            e,
        )
        return False

                                                                   
    if sent:
        try:
            if not fallback_used:
                game.last_social_media_email_sent = now
                db.session.commit()
                current_app.logger.info(
                    "Sent social media email for game_id=%s to %s. "
                    "Updated last_social_media_email_sent to %s.",
                    game_id,
                    liaison_email,
                    now.isoformat(),
                )
            else:
                current_app.logger.info(
                    "Sent fallback liaison email for game_id=%s without "
                    "updating last_social_media_email_sent",
                    game_id,
                )
        except Exception as db_err:
            current_app.logger.error(
                "Email sent, but failed to update last_social_media_email_sent "
                "for game_id=%s: %s",
                game_id,
                db_err,
            )
                                                             
        return True
    else:
        current_app.logger.warning(
            "send_email returned False for game_id=%s, no DB update performed.",
            game_id,
        )
        return False

def _ensure_aware(dt):
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def check_and_send_liaison_emails():
    """
    For every game with a liaison email, send on its schedule:
      'minute', 'daily', 'weekly', or 'monthly'.
    """
    try:
        now = datetime.now(UTC)

                                            
        interval_map = {
            'hourly':  timedelta(hours=1),
            'daily':   timedelta(days=1),
            'weekly':  timedelta(weeks=1),
            'monthly': timedelta(days=30),
        }

        games = Game.query.filter(Game.social_media_liaison_email.isnot(None)).all()

        for game in games:
            freq = (game.social_media_email_frequency or 'weekly').lower()
            threshold = interval_map.get(freq, timedelta(days=1))

                                               
            started = _ensure_aware(game.start_date)
            last    = _ensure_aware(game.last_social_media_email_sent) or started

                                                                                 
            if not game.last_social_media_email_sent:
                if now - started >= threshold:
                    send_social_media_liaison_email(game.id)
                continue

                              
            if now - last >= threshold:
                send_social_media_liaison_email(game.id)

    except OperationalError as exc:
        current_app.logger.exception("DB error in liaison email job: %s", exc)
        db.session.rollback()                      
    except SQLAlchemyError:
        db.session.rollback()
        raise                                                          
    finally:
                                        
        db.session.remove()                                         
