# pylint: disable=import-error
"""
Authentication module for handling login, registration, and related routes.
"""

from datetime import datetime
from urllib.parse import urlparse

from flask import (Blueprint, render_template, request, redirect, url_for, flash,
                   current_app)
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from pytz import utc
import bleach

from app.models import db, User, Game
from app.forms import (LoginForm, RegistrationForm, ForgotPasswordForm,
                       ResetPasswordForm, UpdatePasswordForm)
from app.utils import send_email, generate_tutorial_game, log_user_ip

# Initialize the blueprint.
auth_bp = Blueprint('auth', __name__)

ALLOWED_TAGS = [
    'a', 'b', 'i', 'u', 'em', 'strong', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre', 'br', 'div', 'span', 'ul', 'ol', 'li', 'hr',
    'sub', 'sup', 's', 'strike', 'font', 'img', 'video', 'figure'
]

ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id'],
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'width', 'height'],
    'video': ['src', 'width', 'height', 'controls'],
    'p': ['class'],
    'span': ['class'],
    'div': ['class'],
    'h1': ['class'],
    'h2': ['class'],
    'h3': ['class'],
    'h4': ['class'],
    'h5': ['class'],
    'h6': ['class'],
    'blockquote': ['class'],
    'code': ['class'],
    'pre': ['class'],
    'ul': ['class'],
    'ol': ['class'],
    'li': ['class'],
    'hr': ['class'],
    'sub': ['class'],
    'sup': ['class'],
    's': ['class'],
    'strike': ['class'],
    'font': ['color', 'face', 'size']
}


def sanitize_html(html_content):
    """
    Sanitize HTML content using allowed tags and attributes.
    """
    return bleach.clean(
        html_content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES
    )


def _generate_username(email):
    """
    Generate a unique username based on the provided email.
    """
    base_username = email.split('@')[0]
    username = base_username
    counter = 1
    while User.query.filter(or_(User.username == username, User.email == email)
                              ).first():
        username = f"{base_username}{counter}"
        counter += 1
    return username


def _send_verification_email(user):
    """
    Send a verification email to the user.
    """
    token = user.generate_verification_token()
    verify_url = url_for(
        'auth.verify_email', token=token, _external=True,
        quest_id=request.args.get('quest_id'),
        next=request.args.get('next')
    )
    html = render_template('verify_email.html', verify_url=verify_url)
    subject = "QuestByCycle verify email"
    send_email(user.email, subject, html)
    flash('A verification email has been sent to you. '
          'Please check your inbox.', 'info')


def _auto_verify_and_login(user):
    """
    Automatically verify the user's email and log them in.
    """
    user.email_verified = True
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        current_app.logger.error(f'Failed to auto verify user: {exc}')
        flash('Registration failed due to an unexpected error. '
              'Please try again.', 'error')
        return False
    login_user(user)
    return True


def _join_game_if_provided(user):
    """
    Join the game if a game_id is provided in the request.
    """
    game_id = request.args.get('game_id')
    if game_id:
        game = Game.query.get(game_id)
        if game and game not in user.participated_games:
            user.participated_games.append(game)
            try:
                db.session.commit()
                flash(f'You have successfully joined the game: {game.title}',
                      'success')
            except SQLAlchemyError as exc:
                db.session.rollback()
                current_app.logger.error(f'Failed to join game: {exc}')


def _ensure_tutorial_game(user):
    """
    Ensure the user is joined to a tutorial game if no games are participated.
    """
    if not user.participated_games:
        tutorial_game = Game.query.filter_by(
            is_tutorial=True
        ).order_by(Game.start_date.desc()).first()
        if tutorial_game:
            user.participated_games.append(tutorial_game)
            try:
                db.session.commit()
            except SQLAlchemyError as exc:
                db.session.rollback()
                current_app.logger.error(f'Failed to join tutorial game: {exc}')


@auth_bp.route('/login', methods=['GET', 'POST'])
# pylint: disable=too-many-branches, too-many-return-statements, broad-except
def login():
    """
    Handle user login requests.
    """
    login_form = LoginForm()
    if not login_form.validate_on_submit():
        return render_template(
            'login.html',
            login_form=login_form,
            game_id=request.args.get('game_id'),
            quest_id=request.args.get('quest_id')
        )
    email = sanitize_html(login_form.email.data or "").lower()
    password = login_form.password.data
    error_response = None

    if not email or not password:
        flash('Please enter both email and password.')
        error_response = redirect(
            url_for('auth.login',
                    game_id=request.args.get('game_id'),
                    quest_id=request.args.get('quest_id'))
        )
    else:
        user = User.query.filter_by(email=email).first()
        if user is None:
            flash('Invalid email or password.')
            error_response = redirect(
                url_for('auth.login',
                        game_id=request.args.get('game_id'),
                        quest_id=request.args.get('quest_id'))
            )
        elif (current_app.config.get('MAIL_USERNAME') and
              not user.email_verified):
            flash('Please verify your email before logging in.', 'warning')
            error_response = render_template(
                'login.html',
                login_form=login_form,
                show_resend=True,
                email=email,
                game_id=request.args.get('game_id'),
                quest_id=request.args.get('quest_id')
            )
        elif not user.check_password(password):
            flash('Invalid email or password.')
            error_response = redirect(
                url_for('auth.login',
                        game_id=request.args.get('game_id'),
                        quest_id=request.args.get('quest_id'))
            )

    if error_response is not None:
        return error_response

    try:
        login_user(user, remember=login_form.remember_me.data)
        log_user_ip(user)
        generate_tutorial_game()
        _join_game_if_provided(user)
        if not user.participated_games:
            tutorial_game = Game.query.filter_by(is_tutorial=True).first()
            if tutorial_game:
                user.participated_games.append(tutorial_game)
                db.session.commit()
        quest_id = request.args.get('quest_id')
        next_page = request.args.get('next')
        if next_page:
            parsed_url = urlparse(next_page)
            if not parsed_url.netloc and not parsed_url.scheme:
                return redirect(next_page)
        if user.is_admin:
            return redirect(url_for('admin.admin_dashboard'))
        if quest_id:
            return redirect(url_for('quests.submit_photo', quest_id=quest_id))
        return redirect(url_for('main.index'))
    except Exception as exc:  # pylint: disable=broad-except
        current_app.logger.error(f'Login error: {exc}')
        flash('An unexpected error occurred during login. '
              'Please try again later.', 'error')
        return redirect(
            url_for('auth.login',
                    game_id=request.args.get('game_id'),
                    quest_id=request.args.get('quest_id'))
        )


@auth_bp.route('/resend_verification_email', methods=['POST'])
def resend_verification_email():
    """
    Resend the email verification to the user.
    """
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    if user and not user.email_verified:
        token = user.generate_verification_token()
        verify_url = url_for('auth.verify_email', token=token, _external=True)
        html = render_template('verify_email.html', verify_url=verify_url)
        subject = "Please verify your email"
        send_email(user.email, subject, html)
        flash('A new verification email has been sent. Please check your inbox.',
              'info')
    else:
        flash('Email not found or already verified.', 'warning')
    return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
@login_required
def logout():
    """
    Log out the current user.
    """
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
# pylint: disable=too-many-branches, too-many-return-statements, broad-except
def register():
    """
    Handle user registration.
    """
    register_form = RegistrationForm()
    if not register_form.validate_on_submit():
        return render_template(
            'register.html',
            title='Register',
            form=register_form,
            game_id=request.args.get('game_id'),
            quest_id=request.args.get('quest_id'),
            next=request.args.get('next')
        )
    if not register_form.accept_license.data:
        flash('You must agree to the terms of service, license agreement, '
              'and privacy policy.', 'warning')
        return render_template(
            'register.html',
            title='Register',
            form=register_form,
            game_id=request.args.get('game_id'),
            quest_id=request.args.get('quest_id'),
            next=request.args.get('next')
        )
    email = sanitize_html(register_form.email.data or "").lower()
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('Email already registered. Please use a different email.',
              'warning')
        return redirect(
            url_for('auth.register',
                    game_id=request.args.get('game_id'),
                    quest_id=request.args.get('quest_id'),
                    next=request.args.get('next'))
        )
    username = _generate_username(email)
    user = User(
        username=sanitize_html(username),
        email=email,
        license_agreed=register_form.accept_license.data,
        email_verified=False,
        is_admin=False,
        created_at=datetime.now(utc),
        score=0,
        display_name=None,
        profile_picture=None,
        age_group=None,
        interests=None
    )
    user.set_password(register_form.password.data)
    db.session.add(user)
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        flash('Registration failed due to an unexpected error. '
              'Please try again.', 'error')
        current_app.logger.error(f'Failed to register user: {exc}')
        return render_template(
            'register.html',
            title='Register',
            form=register_form,
            game_id=request.args.get('game_id'),
            quest_id=request.args.get('quest_id'),
            next=request.args.get('next')
        )
    if current_app.config.get('MAIL_USERNAME'):
        _send_verification_email(user)
    else:
        if not _auto_verify_and_login(user):
            return render_template(
                'register.html',
                title='Register',
                form=register_form,
                game_id=request.args.get('game_id'),
                quest_id=request.args.get('quest_id'),
                next=request.args.get('next')
            )
        _join_game_if_provided(user)
        generate_tutorial_game()
        _ensure_tutorial_game(user)
    next_page = request.args.get('next')
    quest_id = request.args.get('quest_id')
    if next_page:
        parsed_url = urlparse(next_page)
        if not parsed_url.netloc and not parsed_url.scheme:
            return redirect(next_page)
    if quest_id:
        return redirect(url_for('quests.submit_photo', quest_id=quest_id))
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """
    Handle password reset requests.
    """
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            token = user.generate_reset_token()
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            html = render_template('reset_password_email.html', reset_url=reset_url)
            subject = "Password Reset Requested"
            send_email(user.email, subject, html)
            flash('A password reset email has been sent. Please check your inbox.',
                  'info')
        else:
            flash('No account found with that email.', 'warning')
        return redirect(url_for('auth.login'))
    return render_template('forgot_password.html', form=form)


@auth_bp.route('/update_password', methods=['GET', 'POST'])
@login_required
def update_password():
    """
    Handle password update requests.
    """
    form = UpdatePasswordForm()
    if form.validate_on_submit():
        user = current_user
        if user.check_password(form.current_password.data):
            user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated.', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Current password is incorrect.', 'danger')
    return render_template('update_password.html', form=form)


@auth_bp.route('/verify_email/<token>')
def verify_email(token):
    """
    Verify the user's email using the provided token.
    """
    user = User.verify_verification_token(token)
    if not user:
        flash('The verification link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))
    if user.email_verified:
        flash('Your email has already been verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))
    user.email_verified = True
    db.session.commit()
    login_user(user)
    generate_tutorial_game()
    if not user.participated_games:
        tutorial_game = Game.query.filter_by(is_tutorial=True).first()
        if tutorial_game:
            user.participated_games.append(tutorial_game)
            db.session.commit()
    game_id = request.args.get('game_id')
    if game_id:
        game = Game.query.get(game_id)
        if game and game not in user.participated_games:
            user.participated_games.append(game)
            db.session.commit()
            flash(f'You have successfully joined the game: {game.title}',
                  'success')
    quest_id = request.args.get('quest_id')
    next_page = request.args.get('next')
    if quest_id:
        return redirect(url_for('quests.submit_photo', quest_id=quest_id))
    if next_page:
        parsed_url = urlparse(next_page)
        if not parsed_url.netloc and not parsed_url.scheme:
            return redirect(next_page)
    flash('Your email has been verified and you have been logged in.',
          'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/privacy_policy')
def privacy_policy():
    """
    Render the privacy policy page.
    """
    return render_template('privacy_policy.html')


@auth_bp.route('/terms_of_service')
def terms_of_service():
    """
    Render the terms of service page.
    """
    return render_template('terms_of_service.html')


@auth_bp.route('/license_agreement')
def license_agreement():
    """
    Render the license agreement page.
    """
    return render_template('license_agreement.html')


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Handle password reset using the provided token.
    """
    user = User.verify_reset_token(token)
    if not user:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset. Please log in with your new password.',
              'success')
        return redirect(url_for('auth.login'))
    return render_template('reset_password.html', form=form)


@auth_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """
    Delete the current user's account.
    """
    user = current_user
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Your account has been deleted.', 'success')
        logout_user()
        return redirect(url_for('main.index'))
    except Exception as exc:  # pylint: disable=broad-except
        db.session.rollback()
        current_app.logger.error(f"Error deleting user: {exc}")
        flash('An error occurred while deleting your account.', 'error')
        return redirect(url_for('main.index'))
