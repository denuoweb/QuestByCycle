from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.base import STATE_RUNNING

from app.utils.email_utils import check_and_send_liaison_emails
from app.utils.calendar_utils import sync_google_calendar_events
from app.utils import generate_demo_game

def create_scheduler(app):
    scheduler = BackgroundScheduler(
        jobstores={'default': MemoryJobStore()},
        executors={'default': ThreadPoolExecutor(5)},
        job_defaults={'coalesce': False, 'max_instances': 1},
        timezone=app.config.get('SCHEDULER_TIMEZONE', 'UTC')
    )

    def _run_check_and_send():
        with app.app_context():
            check_and_send_liaison_emails()

    def _run_calendar_sync():
        with app.app_context():
            sync_google_calendar_events()

    def _run_generate_demo():
        with app.app_context():
            generate_demo_game()

    scheduler.add_job(
        func=_run_check_and_send,
        trigger='cron',
        minute='0',
        id='liaison_email_job',
        replace_existing=True,
    )
    scheduler.add_job(
        func=_run_calendar_sync,
        trigger='interval',
        minutes=15,
        id='calendar_sync_job',
        replace_existing=True,
    )
    scheduler.add_job(
        func=_run_generate_demo,
        trigger='cron',
        hour='0',
        id='generate_demo_game_job',
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
    scheduler = getattr(app, 'scheduler', None)
    if scheduler and scheduler.state == STATE_RUNNING:
        scheduler.shutdown(wait=wait)
        app.logger.info("APScheduler shut down")
