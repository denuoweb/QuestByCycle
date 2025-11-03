"""APScheduler configuration and advisory lock helpers."""

import hashlib
import struct
from typing import Callable

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING
from sqlalchemy import text

from app.models import db
from app.utils import generate_demo_game
from app.utils.calendar_utils import sync_google_calendar_events
from app.utils.email_utils import check_and_send_liaison_emails


def _advisory_lock_key(name: str) -> int:
    """Convert ``name`` into a signed 64-bit key suitable for Postgres advisory locks."""
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    return struct.unpack("!q", digest[:8])[0]


def _execute_with_advisory_lock(app, lock_name: str, target: Callable[[], None]) -> bool:
    """Run ``target`` while holding a Postgres advisory lock for ``lock_name``."""
    try:
        engine = db.get_engine(app)
    except RuntimeError:
        # Happens when no app is bound; fall back to running without locking.
        app.logger.warning(
            "Skipping advisory lock for %s because no application context is bound.",
            lock_name,
        )
        target()
        return False

    if engine.dialect.name != "postgresql":
        target()
        return True

    lock_key = _advisory_lock_key(lock_name)
    try:
        with engine.connect() as connection:
            acquired = connection.execute(
                text("SELECT pg_try_advisory_lock(:key)"),
                {"key": lock_key},
            ).scalar()

            if not acquired:
                app.logger.info(
                    "Skipped %s because another worker holds the advisory lock.",
                    lock_name,
                )
                return False

            try:
                target()
            finally:
                connection.execute(
                    text("SELECT pg_advisory_unlock(:key)"),
                    {"key": lock_key},
                )

    except Exception:  # pragma: no cover - defensive fallback for unexpected DB issues
        app.logger.exception(
            "Failed to obtain advisory lock for %s; running job without locking.",
            lock_name,
        )
        target()
        return False

    return True


def create_scheduler(app):
    """Create and start the background scheduler used for recurring jobs."""
    scheduler = BackgroundScheduler(
        jobstores={"default": MemoryJobStore()},
        executors={"default": ThreadPoolExecutor(5)},
        job_defaults={"coalesce": False, "max_instances": 1},
        timezone=app.config.get("SCHEDULER_TIMEZONE", "UTC"),
    )

    def _run_check_and_send():
        with app.app_context():
            _execute_with_advisory_lock(
                app,
                "liaison_email_job",
                check_and_send_liaison_emails,
            )

    def _run_calendar_sync():
        with app.app_context():
            _execute_with_advisory_lock(
                app,
                "calendar_sync_job",
                sync_google_calendar_events,
            )

    def _run_generate_demo():
        with app.app_context():
            _execute_with_advisory_lock(
                app,
                "generate_demo_game_job",
                generate_demo_game,
            )

    scheduler.add_job(
        func=_run_check_and_send,
        trigger="cron",
        minute="0",
        id="liaison_email_job",
        replace_existing=True,
    )
    scheduler.add_job(
        func=_run_calendar_sync,
        trigger="interval",
        minutes=15,
        id="calendar_sync_job",
        replace_existing=True,
    )
    scheduler.add_job(
        func=_run_generate_demo,
        trigger="cron",
        hour="0",
        id="generate_demo_game_job",
        replace_existing=True,
    )
    app.logger.info("Scheduled job 'liaison_email_job'")
    app.logger.info("Scheduled job 'calendar_sync_job'")
    app.logger.info("Scheduled job 'generate_demo_game_job'")

    scheduler.start()
    app.logger.info("APScheduler started")
    app.scheduler = scheduler
    return scheduler


def shutdown_scheduler(app, wait=True):
    """
    Shutdown the scheduler if it is running. Call this at process exit.
    """
    scheduler = getattr(app, "scheduler", None)
    if scheduler and scheduler.state == STATE_RUNNING:
        scheduler.shutdown(wait=wait)
        app.logger.info("APScheduler shut down")
