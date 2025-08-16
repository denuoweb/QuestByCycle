"""Gunicorn configuration and hooks for QuestByCycle."""

import os
from importlib import import_module


bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
threads = int(os.getenv("GUNICORN_THREADS", "4"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
accesslog = "-"
errorlog = "-"
wsgi_app = os.getenv("WSGI_APP", "wsgi:app")

_scheduler_app = None


def when_ready(server):
    """Start the APScheduler in the master process."""
    if os.getenv("ENABLE_SCHEDULER", "1") != "1":
        server.log.info("Scheduler disabled by env")
        return

    module_name, app_name = wsgi_app.split(":", 1)
    module = import_module(module_name)
    app = getattr(module, app_name)

    from app.scheduler import create_scheduler

    server.log.info("Launching scheduler")
    create_scheduler(app)

    global _scheduler_app
    _scheduler_app = app


def on_exit(server):
    """Shutdown the scheduler on graceful exit."""
    global _scheduler_app
    if _scheduler_app:
        from app.scheduler import shutdown_scheduler

        server.log.info("Shutting down scheduler")
        shutdown_scheduler(_scheduler_app, wait=False)

