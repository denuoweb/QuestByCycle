from __future__ import annotations

from redis import Redis
from rq import Queue
from flask import current_app

from app.models import db, User


def init_queue(app):
    """Initialize and attach an RQ queue to the Flask app."""
    redis_url = app.config.get("REDIS_URL", "redis://localhost:6379/0")
    queue = Queue('default', connection=Redis.from_url(redis_url))
    app.task_queue = queue
    return queue


def send_email_task(to: str, subject: str, html_content: str, inline_images=None) -> None:
    """Background job to send email."""
    from app.utils.email_utils import send_email
    send_email(to, subject, html_content, inline_images)


def deliver_activity_task(activity: dict, sender_id: int) -> None:
    """Background job to deliver an ActivityPub activity."""
    from app.activitypub_utils import deliver_activity
    sender = db.session.get(User, sender_id)
    if sender is not None:
        deliver_activity(activity, sender)


def enqueue_email(to: str, subject: str, html_content: str, inline_images=None) -> None:
    """Enqueue an email sending task or run synchronously when disabled."""
    queue = getattr(current_app, "task_queue", None)
    if queue and current_app.config.get("USE_TASK_QUEUE", True):
        queue.enqueue(send_email_task, to, subject, html_content, inline_images)
    else:
        send_email_task(to, subject, html_content, inline_images)


def enqueue_deliver_activity(activity: dict, sender_id: int) -> None:
    """Enqueue an ActivityPub delivery task or run synchronously when disabled."""
    queue = getattr(current_app, "task_queue", None)
    if queue and current_app.config.get("USE_TASK_QUEUE", True):
        queue.enqueue(deliver_activity_task, activity, sender_id)
    else:
        deliver_activity_task(activity, sender_id)
