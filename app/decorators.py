from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def require_admin(func):
    """Allow access only to admins or super admins."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_super_admin and not current_user.is_admin:
            flash('Access denied: You do not have the necessary permissions.', 'error')
            return redirect(url_for('main.index'))
        return func(*args, **kwargs)

    return wrapper


def require_super_admin(func):
    """Allow access only to super admins."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_super_admin:
            flash('Access denied: You do not have the necessary permissions.', 'error')
            return redirect(url_for('main.index'))
        return func(*args, **kwargs)

    return wrapper


