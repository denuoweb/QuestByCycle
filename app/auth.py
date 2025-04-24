# pylint: disable=import-error
"""
Authentication module for handling login, registration, and related routes.
"""

from datetime import datetime
from urllib.parse import urlparse, urlencode

from flask import (Blueprint, render_template, request, redirect, url_for, flash,
                   current_app, session, jsonify)
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from pytz import utc
from urllib.parse import urlparse, urljoin

import bleach
import rsa
import uuid
import requests

from app.models import db, User, Game
from app.forms import (LoginForm, RegistrationForm, ForgotPasswordForm,
                       ResetPasswordForm, UpdatePasswordForm, MastodonLoginForm)
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
    Send a verification email to the user, including context parameters
    (game_id, quest_id, next) so that they are passed along in the verification link.
    """
    # Generate the token for email verification
    token = user.generate_verification_token()

    # Try to extract game context from the query parameters;
    # if not found there, try form data.
    game_id = request.args.get('game_id') or request.form.get('game_id')
    quest_id = request.args.get('quest_id') or request.form.get('quest_id')
    next_info = request.args.get('next') or request.form.get('next')

    # Build the verification URL with the context parameters included
    verify_url = url_for(
        'auth.verify_email',
        token=token,
        _external=True,
        game_id=game_id,
        quest_id=quest_id,
        next=next_info
    )

    # Render the email content with the verification URL
    html = render_template('verify_email.html', verify_url=verify_url)
    subject = "QuestByCycle verify email"

    # Send the email
    send_email(user.email, subject, html)

    # Optionally, flash a message to inform the user that a verification email has been sent
    flash('A verification email has been sent to you. Please check your inbox.', 'info')



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
    Additionally, set the user's selected_game_id to that game.
    Checks both request.args and request.form.
    """
    # Try to get game_id from query parameters
    game_id = request.args.get('game_id')
    # If not found, try to get it from form data (this applies to POST requests)
    if not game_id:
        game_id = request.form.get('game_id')
    
    if game_id:
        try:
            # Ensure game_id is treated as an integer
            game_id = int(game_id)
        except ValueError:
            current_app.logger.error("Invalid game_id provided: %s", game_id)
            return

        game = Game.query.get(game_id)
        if game:
            # If not already joined, add the game to the user's participated games.
            if game not in user.participated_games:
                user.participated_games.append(game)
            # Set the user's selected game to this game.
            user.selected_game_id = game.id
            try:
                db.session.commit()
                current_app.logger.debug("User %s joined game %s", user.id, game.id)
            except Exception as exc:
                db.session.rollback()
                current_app.logger.error("Failed to join game: %s", exc)



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


@auth_bp.route('/login/mastodon', methods=['GET', 'POST'])
def mastodon_login():
    """
    Display and process the Mastodon login form.
    The user provides the instance domain, and the route dynamically registers
    the OAuth application with that instance.
    """
    form = MastodonLoginForm()
    if form.validate_on_submit():
        instance = form.instance.data.strip().lower()
        redirect_uri = url_for('auth.mastodon_callback', _external=True)
        state = uuid.uuid4().hex
        session['mastodon_state'] = state
        session['mastodon_instance'] = instance
        # Dynamic app registration with Mastodon
        app_registration_url = f"https://{instance}/api/v1/apps"
        data = {
            "client_name": "QuestByCycle",
            "redirect_uris": redirect_uri,
            "scopes": "read write follow",
            "website": request.host_url.rstrip('/')
        }
        try:
            response = requests.post(app_registration_url, data=data)
            response.raise_for_status()
            app_data = response.json()
        except Exception as e:
            flash(f"Error registering app with Mastodon instance: {e}", "danger")
            return redirect(url_for('auth.login'))
        session['mastodon_client_id'] = app_data.get("client_id")
        session['mastodon_client_secret'] = app_data.get("client_secret")
        auth_url = f"https://{instance}/oauth/authorize"
        params = {
            "response_type": "code",
            "client_id": session['mastodon_client_id'],
            "redirect_uri": redirect_uri,
            "scope": "read write follow",
            "state": state
        }
        auth_redirect_url = f"{auth_url}?{urlencode(params)}"
        return redirect(auth_redirect_url)
    return render_template('mastodon_login.html', form=form)


@auth_bp.route('/mastodon/callback')
def mastodon_callback():
    """
    Handle the OAuth callback from Mastodon.
    This route verifies the state, exchanges the code for an access token,
    and retrieves the Mastodon account details.
    """
    code = request.args.get('code')
    state = request.args.get('state')
    if not state or state != session.get('mastodon_state'):
        flash("State mismatch. Authentication failed.", "danger")
        return redirect(url_for('auth.login'))
    instance = session.get('mastodon_instance')
    client_id = session.get('mastodon_client_id')
    client_secret = session.get('mastodon_client_secret')
    redirect_uri = url_for('auth.mastodon_callback', _external=True)
    token_url = f"https://{instance}/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "scope": "read write follow"
    }
    try:
        token_response = requests.post(token_url, data=data)
        token_response.raise_for_status()
        token_data = token_response.json()
    except Exception as e:
        flash(f"Error obtaining access token: {e}", "danger")
        return redirect(url_for('auth.login'))
    access_token = token_data.get("access_token")
    if not access_token:
        flash("Access token not found in response.", "danger")
        return redirect(url_for('auth.login'))
    # Get Mastodon account details.
    verify_url = f"https://{instance}/api/v1/accounts/verify_credentials"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        verify_response = requests.get(verify_url, headers=headers)
        verify_response.raise_for_status()
        mastodon_user = verify_response.json()
    except Exception as e:
        flash(f"Error verifying Mastodon credentials: {e}", "danger")
        return redirect(url_for('auth.login'))
    mastodon_id = str(mastodon_user.get("id"))
    mastodon_username = mastodon_user.get("username")
    display_name = mastodon_user.get("display_name") or mastodon_username
    mastodon_actor_url = mastodon_user.get("url")
    # Look up an existing user by Mastodon ID and instance.
    user = User.query.filter_by(mastodon_id=mastodon_id, mastodon_instance=instance).first()
    if user:
        user.mastodon_access_token = access_token
        user.activitypub_id = mastodon_actor_url  # <-- Use Mastodon actor URL
        db.session.commit()
        login_user(user)
        flash("Logged in via Mastodon. Your federated identity is managed by your Mastodon account.", "success")
    else:
        # If a logged-in user wishes to link their Mastodon account:
        if current_user.is_authenticated:
            current_user.mastodon_id = mastodon_id
            current_user.mastodon_username = mastodon_username
            current_user.mastodon_instance = instance
            current_user.mastodon_access_token = access_token
            current_user.activitypub_id = mastodon_actor_url  # <-- Use Mastodon actor URL
            db.session.commit()
            flash("Mastodon account linked successfully. You will federate via your Mastodon account.", "success")
        else:
            # Otherwise, create a new user using Mastodon data.
            username = mastodon_username
            new_user = User(
                username=username,
                email=f"{username}@{instance}",  # Placeholder email
                license_agreed=True,
                email_verified=True,
                display_name=display_name,
                mastodon_id=mastodon_id,
                mastodon_username=mastodon_username,
                mastodon_instance=instance,
                mastodon_access_token=access_token,
                activitypub_id=mastodon_actor_url  # <-- Use Mastodon actor URL
            )
            new_user.set_password(uuid.uuid4().hex)  # Random password for OAuth-only accounts
            db.session.add(new_user)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f"Error creating user account: {e}", "danger")
                return redirect(url_for('auth.login'))
            login_user(new_user)
            flash("Account created and logged in via Mastodon. You will federate using your Mastodon identity.", "success")
    
    # Ensure a current tutorial game exists
    generate_tutorial_game()
    
    return redirect(url_for('main.index'))


def is_safe_url(target):
    """
    Ensure the target URL is safe for redirection by checking that it is relative
    or belongs to the same server.
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https')) and (ref_url.netloc == test_url.netloc)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login requests using a login modal.
    Supports both normal and AJAX (XHR) submissions:
      - On GET: redirect to index with show_login=1 to open the modal.
      - On normal POST: flash messages and redirect as before.
      - On AJAX POST: return JSON { success, error, show_forgot, forgot_url, redirect }.
    """
    print("DEBUG: Entered login function.")
    game_id   = request.args.get('game_id')
    quest_id  = request.args.get('quest_id')
    next_page = request.args.get('next')
    print(f"DEBUG: Query parameters - game_id: {game_id}, quest_id: {quest_id}, next: {next_page}")

    # If the user is already authenticated, go straight to the next page or index.
    if current_user.is_authenticated:
        if next_page and is_safe_url(next_page):
            return redirect(next_page)
        return redirect(url_for('main.index'))

    # For GET requests, trigger the modal via redirect.
    if request.method == 'GET':
        return redirect(
            url_for('main.index',
                    show_login=1,
                    game_id=game_id,
                    quest_id=quest_id,
                    next=next_page)
        )

    # At this point, we're handling a POST.
    login_form = LoginForm()
    is_ajax    = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # If WTForms validation fails, respond accordingly.
    if not login_form.validate_on_submit():
        msg = 'Please enter both email and password.'
        if is_ajax:
            return jsonify({
                'success': False,
                'error': msg,
                'show_forgot': False
            }), 400
        flash(msg)
        return redirect(
            url_for('main.index',
                    show_login=1,
                    game_id=game_id,
                    quest_id=quest_id,
                    next=next_page)
        )

    # Extract and sanitize credentials.
    email    = sanitize_html(login_form.email.data or "").lower()
    password = login_form.password.data or ""

    # Validate presence of both fields.
    if not email or not password:
        msg = 'Please enter both email and password.'
        if is_ajax:
            return jsonify({
                'success': False,
                'error': msg,
                'show_forgot': False
            }), 400
        flash(msg)
        return redirect(
            url_for('main.index',
                    show_login=1,
                    game_id=game_id,
                    quest_id=quest_id,
                    next=next_page)
        )

    # Look up the user.
    user = User.query.filter_by(email=email).first()
    if user is None:
        msg = 'Invalid email or password.'
        payload = {
            'success': False,
            'error': msg,
            'show_forgot': True,
            'forgot_url': url_for('auth.forgot_password')
        }
        if is_ajax:
            return jsonify(payload), 401
        flash(msg)
        return redirect(
            url_for('main.index',
                    show_login=1,
                    game_id=game_id,
                    quest_id=quest_id,
                    next=next_page)
        )

    # Email verification check.
    if current_app.config.get('MAIL_SERVER') and not user.email_verified:
        msg = 'Please verify your email before logging in.'
        if is_ajax:
            return jsonify({
                'success': False,
                'error': msg,
                'show_forgot': False
            }), 403
        flash(msg, 'warning')
        return redirect(
            url_for('main.index',
                    show_login=1,
                    game_id=game_id,
                    quest_id=quest_id,
                    next=next_page)
        )

    # Password check.
    if not user.check_password(password):
        msg = 'Invalid email or password.'
        payload = {
            'success': False,
            'error': msg,
            'show_forgot': True,
            'forgot_url': url_for('auth.forgot_password')
        }
        if is_ajax:
            return jsonify(payload), 401
        flash(msg)
        return redirect(
            url_for('main.index',
                    show_login=1,
                    game_id=game_id,
                    quest_id=quest_id,
                    next=next_page)
        )

    # Everything checks out: log the user in.
    try:
        login_user(user, remember=login_form.remember_me.data)
        log_user_ip(user)
        generate_tutorial_game()
        _join_game_if_provided(user)

        # Determine post-login redirect.
        if next_page and is_safe_url(next_page):
            redirect_to = next_page
        elif user.is_admin:
            redirect_to = url_for('admin.admin_dashboard')
        elif quest_id:
            redirect_to = url_for('quests.submit_photo', quest_id=quest_id)
        else:
            redirect_to = url_for('main.index')

        # Return JSON on AJAX, normal redirect otherwise.
        if is_ajax:
            return jsonify({
                'success': True,
                'redirect': redirect_to
            }), 200

        return redirect(redirect_to)

    except Exception as exc:
        current_app.logger.error(f'Login error: {exc}')
        msg = 'An unexpected error occurred. Please try again later.'
        if is_ajax:
            return jsonify({
                'success': False,
                'error': msg,
                'show_forgot': False
            }), 500
        flash(msg, 'error')
        return redirect(
            url_for('main.index',
                    show_login=1,
                    game_id=game_id,
                    quest_id=quest_id,
                    next=next_page)
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
    
    If a game_id is provided in the request, the new user will be joined to that game
    as their current selected game. Otherwise, the user is joined to the default tutorial game.
    """
    register_form = RegistrationForm()
    # On GET or if the form is not validated, render the registration template with the context.
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
        flash('Email already registered. Please use a different email.', 'warning')
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
        flash('Registration failed due to an unexpected error. Please try again.', 'error')
        current_app.logger.error(f'Failed to register user: {exc}')
        return render_template(
            'register.html',
            title='Register',
            form=register_form,
            game_id=request.args.get('game_id'),
            quest_id=request.args.get('quest_id'),
            next=request.args.get('next')
        )
    # Create a local ActivityPub actor (for users without Mastodon)
    create_activitypub_actor(user)
    
    # Determine if a game_id was provided during registration.
    # Try to get it from query parameters first, and then from form data.
    game_id = request.args.get('game_id') or request.form.get('game_id')
    
    if current_app.config['MAIL_SERVER']:
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
        # If a game id was provided, join that game.
        if game_id:
            _join_game_if_provided(user)
        else:
            # If no game id was provided, join the default tutorial game.
            generate_tutorial_game()
            _ensure_tutorial_game(user)
    
    # Process redirection after registration.
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
    - On normal GET: redirect to index with show_login=1 (if you like), but we won't need it.
    - On normal POST: flash + redirect to login page.
    - On AJAX POST: return JSON { success, message | error }.
    """
    form    = ForgotPasswordForm()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data.strip().lower()
            user  = User.query.filter_by(email=email).first()

            if user:
                token     = user.generate_reset_token()
                html      = render_template('reset_password_email.html', token=token)
                send_email(user.email, "Password Reset Requested", html)
                success_msg = 'A password reset email has been sent. Please check your inbox.'

                if is_ajax:
                    return jsonify({
                        'success': True,
                        'message': success_msg
                    }), 200

                flash(success_msg, 'info')
            else:
                error_msg = 'No account found with that email.'
                if is_ajax:
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 404

                flash(error_msg, 'warning')

            # on normal POST, go back to login so they can try again or see the flash
            return redirect(url_for('auth.login'))

        # form validation failed (e.g. empty or invalid email)
        field_errors = form.email.errors
        error_msg    = field_errors[0] if field_errors else 'Invalid email.'
        if is_ajax:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

        # re-render the old page if you still support it; or redirect
        flash(error_msg, 'danger')
        return redirect(url_for('auth.login'))

    # If someone GETs /forgot_password, just redirect to index so modal can open if desired.
    return redirect(url_for('main.index', show_login=0))


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
    
    This route checks for context parameters in the verification URL:
      - If a game_id is provided (either directly or inferred from the 'next' parameter),
        the user will be joined to that game and that game becomes the user's selected game.
      - Otherwise, if no game_id is provided and the user has not joined any game,
        the user is added to the default tutorial game.
    """
    user = User.verify_verification_token(token)
    if not user:
        flash('The verification link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))
    if user.email_verified:
        flash('Your email has already been verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))
    
    # Mark the email as verified.
    user.email_verified = True
    db.session.commit()
    
    # Log the user in.
    login_user(user)
    
    # At this point, try to extract game context.
    # First, try to get game_id from the query or form data.
    game_id = request.args.get('game_id') or request.form.get('game_id')
    
    # If no game_id is provided but a "next" parameter is available, try to extract the game id from its path.
    next_page = request.args.get('next') or request.form.get('next')
    if not game_id and next_page:
        parsed_next = urlparse(next_page)
        # Assuming the next URL is in the format https://questbycycle.org/17 (i.e. game id in the path)
        potential_id = parsed_next.path.strip('/')
        if potential_id.isdigit():
            game_id = potential_id

    # If we have a game id, attempt to join the user to that game.
    if game_id:
        try:
            game_id_int = int(game_id)
        except ValueError:
            current_app.logger.error("Invalid game_id provided in verification: %s", game_id)
            game_id_int = None

        if game_id_int:
            game = Game.query.get(game_id_int)
            if game and game not in user.participated_games:
                user.participated_games.append(game)
                user.selected_game_id = game.id
                try:
                    db.session.commit()
                except Exception as exc:
                    db.session.rollback()
                    current_app.logger.error("Failed to join game during verification: %s", exc)
                else:
                    flash(f'You have successfully joined the game: {game.title}', 'success')
    else:
        # If no game context is provided and the user hasn't joined any game,
        # join them to the default tutorial game.
        if not user.participated_games:
            tutorial_game = Game.query.filter_by(is_tutorial=True).first()
            if tutorial_game:
                user.participated_games.append(tutorial_game)
                user.selected_game_id = tutorial_game.id
                try:
                    db.session.commit()
                except Exception as exc:
                    db.session.rollback()
                    current_app.logger.error("Failed to join tutorial game during verification: %s", exc)
    
    # Handle quest and next parameters for further redirection.
    quest_id = request.args.get('quest_id')
    if quest_id:
        return redirect(url_for('quests.submit_photo', quest_id=quest_id))
    if next_page:
        parsed_url = urlparse(next_page)
        if not parsed_url.netloc and not parsed_url.scheme:
            return redirect(next_page)
    
    flash('Your email has been verified and you have been logged in.', 'success')
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
    Handle password reset using a modal.
    - GET: redirect to index with show_reset=1&token so the modal opens.
    - POST: validate form, set new password, log the user in, return JSON with redirect.
    """
    form    = ResetPasswordForm()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # Always funnel GETs back to index so your JS can pop open the modal
    if request.method == 'GET':
        return redirect(url_for('main.index', show_reset=1, token=token))

    # On POST, check form validation
    if not form.validate_on_submit():
        error = form.password.errors[0] if form.password.errors else 'Invalid input.'
        if is_ajax:
            return jsonify({'success': False, 'error': error}), 400
        flash(error, 'danger')
        return redirect(url_for('main.index', show_reset=1, token=token))

    # Verify token => find user
    user = User.verify_reset_token(token)
    if not user:
        msg = 'The reset link is invalid or has expired.'
        if is_ajax:
            return jsonify({'success': False, 'error': msg}), 400
        flash(msg, 'danger')
        return redirect(url_for('main.index'))

    # Set new password and commit
    user.set_password(form.password.data)
    db.session.commit()

    # *** NEW: automatically log them in ***
    login_user(user)

    # Prepare success response
    success_msg = 'Your password has been reset and you are now logged in.'
    if is_ajax:
        return jsonify({
            'success': True,
            'message': success_msg,
            'redirect': url_for('main.index')
        }), 200

    # Fallback for non-AJAX: flash + redirect to index
    flash(success_msg, 'success')
    return redirect(url_for('main.index'))



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


def generate_activitypub_keys():
    """
    Generate a new RSA key pair for ActivityPub signing.
    Returns a tuple (public_key_pem, private_key_pem).
    """
    (pubkey, privkey) = rsa.newkeys(2048)
    public_pem = pubkey.save_pkcs1().decode('utf-8')
    private_pem = privkey.save_pkcs1().decode('utf-8')
    return public_pem, private_pem


def create_activitypub_actor(user):
    """
    Create a local ActivityPub actor for a user if they do not already have one.
    For local registrations only: this will generate a key pair and a local actor URL.
    (For Mastodon-linked accounts, activitypub_id is set to the Mastodon account URL.)
    """
    if not user.activitypub_id:
        public_key, private_key = generate_activitypub_keys()
        # Construct the actor URL using QuestByCycle’s domain and the user's username.
        actor_url = url_for('profile.view_user', username=user.username, _external=True)
        user.activitypub_id = actor_url
        user.public_key = public_key
        user.private_key = private_key
        db.session.commit()


@auth_bp.route('/check_email', methods=['GET'])
def check_email():
    """
    AJAX endpoint: given ?email=<address>, return JSON { exists: true|false }.
    """
    email = (request.args.get('email') or '').strip().lower()
    # Query for existence of a user with that email
    exists = User.query.filter_by(email=email).first() is not None
    return jsonify({ 'exists': exists })
