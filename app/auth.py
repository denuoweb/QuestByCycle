from cryptography.fernet import Fernet
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Game
from app.forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm, UpdatePasswordForm
from app.utils import send_email, generate_tutorial_game, log_user_ip
from sqlalchemy import or_
from pytz import utc
from datetime import datetime
from urllib.parse import urlparse

import bleach

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
    return bleach.clean(html_content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Always create the login form instance
    login_form = LoginForm()

    try:
        if login_form.validate_on_submit():
            # Normalize email to lowercase after sanitizing it.
            email = sanitize_html(login_form.email.data or "").lower()
            password = login_form.password.data
            if not email or not password:
                flash('Please enter both email and password.')
                return redirect(url_for('auth.login', game_id=request.args.get('game_id'), quest_id=request.args.get('quest_id')))

            user = User.query.filter_by(email=email).first()

            if user is None:
                flash('Invalid email or password.')
                return redirect(url_for('auth.login', game_id=request.args.get('game_id'), quest_id=request.args.get('quest_id')))

            # Check if email verification is required and if the user's email is verified
            if current_app.config.get('MAIL_USERNAME') and not user.email_verified:
                flash('Please verify your email before logging in.', 'warning')
                return render_template('login.html', login_form=login_form, show_resend=True, email=email, 
                                       game_id=request.args.get('game_id'), quest_id=request.args.get('quest_id'))

            if user and user.check_password(password):
                login_user(user, remember=login_form.remember_me.data)
                log_user_ip(current_user)
                generate_tutorial_game()

                # Automatically join the game if a game_id is provided
                game_id = request.args.get('game_id')
                if game_id:
                    game = Game.query.get(game_id)
                    if game and game not in user.participated_games:
                        user.participated_games.append(game)
                        db.session.commit()
                        flash(f'You have successfully joined the game: {game.title}', 'success')

                # Check if the user has zero participated games and add to tutorial game if true
                if len(user.participated_games) == 0:
                    tutorial_game = Game.query.filter_by(is_tutorial=True).first()
                    if tutorial_game:
                        user.participated_games.append(tutorial_game)
                        db.session.commit()

                quest_id = request.args.get('quest_id')
                next_page = request.args.get('next')

                # Ensure next_page is a relative URL
                if next_page:
                    parsed_url = urlparse(next_page)
                    if not parsed_url.netloc and not parsed_url.scheme:
                        return redirect(next_page)

                if user.is_admin:
                    return redirect(url_for('admin.admin_dashboard'))
                elif quest_id:
                    return redirect(url_for('quests.submit_photo', quest_id=quest_id))
                else:
                    return redirect(url_for('main.index'))
            else:
                flash('Invalid email or password.')

    except Exception as e:
        current_app.logger.error(f'Login error: {e}')
        flash('An unexpected error occurred during login. Please try again later.', 'error')
        return redirect(url_for('auth.login', game_id=request.args.get('game_id'), quest_id=request.args.get('quest_id')))
    
    # Always pass the login_form, even if the user is not authenticated or if validation failed.
    return render_template('login.html', login_form=login_form, game_id=request.args.get('game_id'), quest_id=request.args.get('quest_id'))


@auth_bp.route('/resend_verification_email', methods=['POST'])
def resend_verification_email():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    if user and not user.email_verified:
        token = user.generate_verification_token()
        verify_url = url_for('auth.verify_email', token=token, _external=True)
        html = render_template('verify_email.html', verify_url=verify_url)
        subject = "Please verify your email"
        send_email(user.email, subject, html)
        flash('A new verification email has been sent. Please check your inbox.', 'info')
    else:
        flash('Email not found or already verified.', 'warning')
    return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegistrationForm()
    try:
        if register_form.validate_on_submit():
            if not register_form.accept_license.data:
                flash('You must agree to the terms of service, license agreement, and privacy policy.', 'warning')
                return render_template('register.html', form=register_form, game_id=request.args.get('game_id'), quest_id=request.args.get('quest_id'), next=request.args.get('next'))

            email = sanitize_html(register_form.email.data or "").lower()
            base_username = email.split('@')[0]
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Email already registered. Please use a different email.', 'warning')
                return redirect(url_for('auth.register', game_id=request.args.get('game_id'), quest_id=request.args.get('quest_id'), next=request.args.get('next')))

            counter = 1
            username = base_username
            while User.query.filter(or_(User.username == username, User.email == email)).first():
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                username=sanitize_html(username),
                email=email,
                license_agreed=register_form.accept_license.data,
                email_verified=False,  # Initially set to False
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

                # Check if email verification is required
                if current_app.config.get('MAIL_USERNAME'):
                    token = user.generate_verification_token()
                    verify_url = url_for('auth.verify_email', token=token, _external=True, quest_id=request.args.get('quest_id'), next=request.args.get('next'))
                    html = render_template('verify_email.html', verify_url=verify_url)
                    subject = "QuestByCycle verify email"
                    send_email(user.email, subject, html)
                    flash('A verification email has been sent to you. Please check your inbox.', 'info')
                else:
                    user.email_verified = True  # Automatically verify email
                    db.session.commit()
                    login_user(user)  # Log in the user automatically if email verification is bypassed

                    # Automatically join the game if a game_id is provided
                    game_id = request.args.get('game_id')
                    if game_id:
                        game = Game.query.get(game_id)
                        if game and game not in user.participated_games:
                            user.participated_games.append(game)
                            db.session.commit()
                            flash(f'You have successfully joined the game: {game.title}', 'success')

                    # Ensure the tutorial game exists
                    generate_tutorial_game()

                    # Check if the user has zero participated games and add to tutorial game if true
                    if len(user.participated_games) == 0:
                        tutorial_game = Game.query.filter_by(is_tutorial=True).order_by(Game.start_date.desc()).first()
                        if tutorial_game:
                            user.participated_games.append(tutorial_game)
                            db.session.commit()

                next_page = request.args.get('next')
                quest_id = request.args.get('quest_id')

                # Ensure next_page is a relative URL
                if next_page:
                    parsed_url = urlparse(next_page)
                    if not parsed_url.netloc and not parsed_url.scheme:
                        return redirect(next_page)

                if quest_id:
                    return redirect(url_for('quests.submit_photo', quest_id=quest_id))
                else:
                    return redirect(url_for('main.index'))

            except Exception as e:
                db.session.rollback()
                flash('Registration failed due to an unexpected error. Please try again.', 'error')
                current_app.logger.error(f'Failed to register user or send verification email: {e}')
                return render_template('register.html', title='Register', form=register_form, game_id=request.args.get('game_id'), quest_id=request.args.get('quest_id'), next=request.args.get('next'))

    except Exception as e:
        current_app.logger.error(f'Registration error: {e}')
        flash('An unexpected error occurred during registration. Please try again later.', 'error')
        return redirect(url_for('auth.register', game_id=request.args.get('game_id'), quest_id=request.args.get('quest_id'), next=request.args.get('next')))

    return render_template('register.html', title='Register', form=register_form, register_form=register_form, game_id=request.args.get('game_id'), quest_id=request.args.get('quest_id'), next=request.args.get('next'))


@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
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
            flash('A password reset email has been sent. Please check your inbox.', 'info')
        else:
            flash('No account found with that email.', 'warning')
        return redirect(url_for('auth.login'))
    return render_template('forgot_password.html', form=form)


@auth_bp.route('/update_password', methods=['GET', 'POST'])
@login_required
def update_password():
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
    user = User.verify_verification_token(token)
    if not user:
        flash('The verification link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))
    
    if user.email_verified:
        flash('Your email has already been verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))
    
    user.email_verified = True
    db.session.commit()
    login_user(user)  # Log in the user

    # Ensure the tutorial game exists
    generate_tutorial_game()

    # Check if the user has zero participated games and add to tutorial game if true
    if len(user.participated_games) == 0:
        tutorial_game = Game.query.filter_by(is_tutorial=True).first()
        if tutorial_game:
            user.participated_games.append(tutorial_game)
            db.session.commit()

    # Automatically join the game if a game_id is provided
    game_id = request.args.get('game_id')
    if game_id:
        game = Game.query.get(game_id)
        if game and game not in user.participated_games:
            user.participated_games.append(game)
            db.session.commit()
            flash(f'You have successfully joined the game: {game.title}', 'success')

    # Redirect to the correct page based on the quest_id or next parameter
    quest_id = request.args.get('quest_id')
    next_page = request.args.get('next')

    if quest_id:
        return redirect(url_for('quests.submit_photo', quest_id=quest_id))
    elif next_page:
        # Ensure next_page is a relative URL
        parsed_url = urlparse(next_page)
        if not parsed_url.netloc and not parsed_url.scheme:
            return redirect(next_page)

    flash('Your email has been verified and you have been logged in.', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')


@auth_bp.route('/terms_of_service')
def terms_of_service():
    return render_template('terms_of_service.html')


@auth_bp.route('/license_agreement')
def license_agreement():
    return render_template('license_agreement.html')


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_token(token)
    if not user:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset. Please log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', form=form)


@auth_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user = current_user  # Get the logged-in user directly

    try:
        db.session.delete(user)
        db.session.commit()
        flash('Your account has been deleted.', 'success')
        logout_user()  # Log the user out after deletion
        return redirect(url_for('main.index'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user: {e}")
        flash('An error occurred while deleting your account.', 'error')
        return redirect(url_for('main.index'))
