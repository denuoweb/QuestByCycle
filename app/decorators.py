from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user


def require_admin(func):
    """Allow access only to admins or super admins.

    When a ``game_id`` argument is present, non-super admins must be an
    administrator for that specific game. This helps ensure admins cannot
    manage games they do not control.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_super_admin and not current_user.is_admin:
            flash('Access denied: You do not have the necessary permissions.', 'error')
            return redirect(url_for('main.index'))

        if not current_user.is_super_admin:
            game_id = kwargs.get('game_id') or request.view_args.get('game_id')
            if game_id and not current_user.is_admin_for_game(game_id):
                flash('Access denied: You do not have permission for this game.', 'error')
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


