"""Helpers for sending email notifications."""

from __future__ import annotations

from datetime import datetime, timedelta
import smtplib
from textwrap import dedent

from flask import current_app
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from app.constants import UTC
from app.models import db, Game, QuestSubmission, Quest, User
from . import sanitize_html


def send_email(
    to: str,
    subject: str,
    html_content: str,
    inline_images: list[tuple[str, bytes, str]] | None = None,
) -> bool:
    """Send an email using the application's SMTP configuration."""

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

    try:
        mail_server = current_app.config.get("MAIL_SERVER")
        mail_port = current_app.config.get("MAIL_PORT")
        use_tls = current_app.config.get("MAIL_USE_TLS", False)
        use_ssl = current_app.config.get("MAIL_USE_SSL", False)
        mail_username = current_app.config.get("MAIL_USERNAME")
        mail_password = current_app.config.get("MAIL_PASSWORD")

        smtp_conn = smtplib.SMTP_SSL(mail_server, mail_port) if use_ssl else smtplib.SMTP(mail_server, mail_port)
        smtp_conn.ehlo()
        if use_tls:
            smtp_conn.starttls()
            smtp_conn.ehlo()
        if mail_username and mail_password:
            smtp_conn.login(mail_username, mail_password)

        smtp_conn.sendmail(msg_root["From"], [to], msg_root.as_string())
        smtp_conn.quit()
        current_app.logger.info("Email sent successfully to %s.", to)
        return True

    except Exception as exc:  # pragma: no cover - network dependent
        current_app.logger.error("Failed to send email: %s", exc)
        return False


def send_social_media_liaison_email(
    game_id: int,
    fallback_to_last: bool = False,
    last_limit: int = 5,
) -> bool:
    """Send a summary of recent quest submissions to the game's liaison."""

    try:
        game = db.session.get(Game, game_id)
    except Exception as e:  # pragma: no cover - DB errors are logged
        current_app.logger.error("Database error while fetching Game id=%s: %s", game_id, e)
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
    except Exception as e:  # pragma: no cover - DB errors are logged
        current_app.logger.error("Database error fetching submissions for game_id=%s: %s", game_id, e)
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
        <h1>{header_title} for "{sanitize_html(game.title)}"</h1>
        <p><b>Time period:</b> {cutoff_time:%Y-%m-%d %H:%M %Z} → {now:%Y-%m-%d %H:%M %Z}</p>
        <p><b>Total {header_title.lower()}:</b> {len(submissions)}</p>
        <hr>
        """
    )
    html_parts = [html_header]
    inline_images: list[tuple[str, bytes, str]] = []

    social_submissions = [s for s in submissions if s.submitter.upload_to_socials]
    nonsocial_submissions = [s for s in submissions if not s.submitter.upload_to_socials]

    def append_submission(sub, idx: int) -> None:
        quest = sub.quest
        user = sub.submitter
        safe_quest_title = sanitize_html(quest.title) if quest and quest.title else "(Untitled Quest)"
        safe_username = sanitize_html(user.username) if user and user.username else "(Unknown User)"

        html_parts.append(f"<div><b>{idx}.</b> {safe_username} – {safe_quest_title}<br>")
        if sub.image_url:
            try:
                with open(os.path.join(current_app.static_folder, sub.image_url), "rb") as img_fp:
                    data = img_fp.read()
                    cid = f"img{idx}"
                    inline_images.append((cid, data, "png"))
                    html_parts.append(f'<img src="cid:{cid}" alt="submission image"><br>')
            except Exception as ue:  # pragma: no cover - disk errors
                current_app.logger.error("Failed to inline image '%s': %s", sub.image_url, ue)

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
    except Exception as e:  # pragma: no cover - network errors
        current_app.logger.error("Exception when sending email to '%s': %s", liaison_email, e)
        return False

    if sent:
        try:
            if not fallback_used:
                game.last_social_media_email_sent = now
                db.session.commit()
                current_app.logger.info(
                    "Sent social media email for game_id=%s to %s. Updated last_social_media_email_sent to %s.",
                    game_id,
                    liaison_email,
                    now.isoformat(),
                )
            else:
                current_app.logger.info(
                    "Sent fallback liaison email for game_id=%s without updating last_social_media_email_sent",
                    game_id,
                )
        except Exception as db_err:  # pragma: no cover - DB errors are logged
            current_app.logger.error(
                "Email sent, but failed to update last_social_media_email_sent for game_id=%s: %s",
                game_id,
                db_err,
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
    """Send liaison emails for all games according to their schedule."""

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

    except OperationalError as exc:  # pragma: no cover - DB errors
        current_app.logger.exception("DB error in liaison email job: %s", exc)
        db.session.rollback()
    except SQLAlchemyError:  # pragma: no cover - DB errors
        db.session.rollback()
        raise
    finally:
        db.session.remove()

