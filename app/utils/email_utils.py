"""Email helper functions."""
from __future__ import annotations

from datetime import datetime, timedelta
import io
import os
import smtplib

from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app, url_for
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from app.utils import format_db_error
from textwrap import dedent
from PIL import Image

from ..models import db, Game, Quest, QuestSubmission, User
from app.constants import UTC
from app.tasks import enqueue_email


def send_email(
    to: str,
    subject: str,
    html_content: str,
    inline_images: list[tuple[str, bytes, str]] | None = None,
) -> bool:
    """Send an email using SMTP settings from the Flask app."""
    msg_root = MIMEMultipart("related")
    msg_root["Subject"] = subject
    msg_root["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
    msg_root["To"] = to

    alt_part = MIMEMultipart("alternative")
    msg_root.attach(alt_part)
    alt_part.attach(MIMEText(html_content, "html"))

    inline_images = inline_images or []
    for cid, data, subtype in inline_images:
        img = MIMEImage(data, _subtype=subtype)
        img.add_header("Content-ID", f"<{cid}>")
        img.add_header("Content-Disposition", "inline", filename=f"{cid}.{subtype}")
        msg_root.attach(img)

    config = current_app.config
    mail_server = config.get("MAIL_SERVER")
    mail_port = config.get("MAIL_PORT")
    use_tls = config.get("MAIL_USE_TLS", False)
    use_ssl = config.get("MAIL_USE_SSL", False)
    mail_username = config.get("MAIL_USERNAME")
    mail_password = config.get("MAIL_PASSWORD")

    smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    try:
        with smtp_class(mail_server, mail_port) as smtp_conn:
            smtp_conn.ehlo()
            if use_tls:
                smtp_conn.starttls()
                smtp_conn.ehlo()
            if mail_username and mail_password:
                smtp_conn.login(mail_username, mail_password)

            smtp_conn.sendmail(msg_root["From"], [to], msg_root.as_string())
        current_app.logger.info("Email sent successfully to %s.", to)
        return True
    except (smtplib.SMTPException, OSError) as exc:
        current_app.logger.error("Failed to send email: %s", exc)
        return False


def send_social_media_liaison_email(
    game_id: int,
    fallback_to_last: bool = False,
    last_limit: int = 5,
) -> bool:
    """Send a digest of recent quest submissions to a game's liaison."""
    try:
        game = db.session.get(Game, game_id)
    except SQLAlchemyError as e:
        current_app.logger.error(
            "Database error while fetching Game id=%s: %s",
            game_id,
            format_db_error(e),
        )
        return False

    if game is None:
        current_app.logger.warning("No Game found with id=%s. Aborting social media email.", game_id)
        return False

    liaison_email = game.social_media_liaison_email
    if not liaison_email:
        current_app.logger.warning(
            "Game id=%s has no social_media_liaison_email. Aborting email.", game_id
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
            .filter(Quest.game_id == game_id, QuestSubmission.timestamp > cutoff_time)
            .order_by(QuestSubmission.timestamp.asc())
            .all()
        )
    except SQLAlchemyError as e:
        current_app.logger.error(
            "Database error fetching submissions for game_id=%s: %s",
            game_id,
            format_db_error(e),
        )
        return False

    fallback_used = False
    if not submissions:
        current_app.logger.info(
            "No new submissions since %s for game_id=%s.", cutoff_time.isoformat(), game_id
        )
        if fallback_to_last:
            submissions = (
                QuestSubmission.query
                .join(Quest, Quest.id == QuestSubmission.quest_id)
                .join(User, User.id == QuestSubmission.user_id)
                .filter(Quest.game_id == game_id)
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
    html_header = dedent(
        f"""
        <h1>{header_title} for \"{game.title}\"</h1>
        <p><b>Time period:</b> {cutoff_time:%Y-%m-%d %H:%M %Z} → {now:%Y-%m-%d %H:%M %Z}</p>
        <p><b>Total {header_title.lower()}:</b> {len(submissions)}</p>
        <hr>
        """
    )
    html_parts = [html_header]
    inline_images: list[tuple[str, bytes, str]] = []

    social_submissions = [s for s in submissions if s.submitter.upload_to_socials]
    nonsocial_submissions = [s for s in submissions if not s.submitter.upload_to_socials]

    def append_submission(sub, idx):
        quest = sub.quest
        user = sub.submitter
        safe_quest_title = quest.title if quest and quest.title else "(Untitled Quest)"
        safe_username = user.username if user and user.username else "(Unknown User)"

        html_parts.append(
            dedent(
                f"""
                <div style="margin-bottom:1.5rem">
                  <h3>{idx}. Quest: {safe_quest_title}</h3>
                  <p>User: {safe_username} &nbsp;|&nbsp; Submitted: {sub.timestamp:%Y-%m-%d %H:%M %Z}</p>
                """
            )
        )

        if sub.comment:
            sanitized_comment = sub.comment.replace("\n", "<br>")
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
                            f'<img src="cid:{cid}" alt="submission image" style="max-width:300px;max-height:300px"><br>'
                        )
                except OSError as e:
                    current_app.logger.warning(
                        "Could not open or process image for submission id=%s at %s: %s. Falling back to public URL.",
                        sub.id,
                        image_path,
                        e,
                    )
                    try:
                        with current_app.test_request_context():
                            public_url = url_for("static", filename=rel_path, _external=True)
                        html_parts.append(
                            f'<img src="{public_url}" alt="submission image"><br>'
                        )
                    except RuntimeError as ue:
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
        enqueue_email(liaison_email, subject, html_body, inline_images)
        sent = True
    except Exception as e:
        current_app.logger.error(
            "Exception when sending email to '%s': %s", liaison_email, e
        )
        return False

    if sent:
        try:
            if not fallback_used:
                game.last_social_media_email_sent = now
                db.session.commit()
            current_app.logger.info(
                "Sent social media email for game_id=%s to %s.", game_id, liaison_email
            )
        except SQLAlchemyError as db_err:
            current_app.logger.error(
                "Email sent, but failed to update last_social_media_email_sent for game_id=%s: %s",
                game_id,
                format_db_error(db_err),
            )
        return True
    current_app.logger.warning(
        "send_email returned False for game_id=%s, no DB update performed.", game_id
    )
    return False


def _ensure_aware(dt):
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def check_and_send_liaison_emails() -> None:
    """Send scheduled liaison digests for all games."""
    try:
        now = datetime.now(UTC)
        interval_map = {
            "hourly": timedelta(hours=1),
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1),
            "monthly": timedelta(days=30),
        }
        games = Game.query.filter(Game.social_media_liaison_email.isnot(None)).all()
        for game in games:
            freq = (game.social_media_email_frequency or "weekly").lower()
            threshold = interval_map.get(freq, timedelta(days=1))

            started = _ensure_aware(game.start_date)
            last = _ensure_aware(game.last_social_media_email_sent) or started

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
