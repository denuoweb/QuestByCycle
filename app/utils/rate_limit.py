"""Utility functions for rate limiting.

These helpers provide key functions used by Flask-Limiter to apply
per-user and per-email throttling while falling back to the client's
IP address.
"""

from flask import request
from flask_login import current_user
from flask_limiter.util import get_remote_address


def user_or_ip() -> str:
    """Return the current user's ID or the request IP address.

    When a user is authenticated their database ID is used to scope the
    limit; otherwise the remote IP address is used.
    """
    return str(current_user.id) if current_user.is_authenticated else get_remote_address()


def email_or_ip() -> str:
    """Use submitted email for limiting or fall back to the IP address."""
    return request.form.get("email") or get_remote_address()
