                              
"""
Authentication module for handling login, registration, and related routes.
"""

import uuid
import requests
from datetime import datetime
from urllib.parse import urlparse, urlencode

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    session,
    jsonify,
)
from app.utils import safe_url_for
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from app.constants import UTC
from urllib.parse import urljoin
from app.models import db
from app.models.user import User
from app.models.game import Game
from app.forms import (LoginForm, RegistrationForm, ForgotPasswordForm,
                       ResetPasswordForm, UpdatePasswordForm, MastodonLoginForm)
from app.utils.email_utils import send_email
from app.utils import log_user_ip, REQUEST_TIMEOUT, sanitize_html
from app.tasks import enqueue_email
from app.activitypub_utils import create_activitypub_actor

auth_bp = Blueprint('auth', __name__)


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
    Compose and send the “verify your e-mail” message,
    forwarding any game_id or custom_game_code through the token link.
    """
    token = user.generate_verification_token()
    raw_gid = (request.values.get('game_id') or '').strip()
    raw_code = (request.values.get('custom_game_code') or '').strip()
    raw_next = (request.values.get('next') or '').strip()

    params = {'token': token}

    if raw_gid:
        params['game_id'] = raw_gid
    elif raw_code:
        params['custom_game_code'] = raw_code
    else:
                                                                  
        params['show_join_custom'] = 1

    if raw_next:
        params['next'] = raw_next

    verify_url = safe_url_for('auth.verify_email', _external=True, **params)
    html = render_template('verify_email.html', verify_url=verify_url)
    subject = "QuestByCycle – verify your email"
    enqueue_email(user.email, subject, html)


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
                                              
    game_id = request.args.get('game_id')
                                                                                
    if not game_id:
        game_id = request.form.get('game_id')
    
    if game_id is not None:
        try:
                                                     
            game_id = int(game_id)
        except ValueError:
            current_app.logger.error("Invalid game_id provided: %s", game_id)
            return

        game = Game.query.get(game_id)
        if game:
                                                                                   
            if game not in user.participated_games:
                user.participated_games.append(game)
                                                        
            user.selected_game_id = game.id
            try:
                db.session.commit()
                current_app.logger.debug("User %s joined game %s", user.id, game.id)
            except Exception:
                db.session.rollback()


def _ensure_demo_game(user):
    """
    Ensure the user is joined to a demo game if no games are participated.
    """
    if not user.participated_games:
        demo_game = (
            Game.query
            .filter_by(is_demo=True, archived=False)
            .order_by(Game.start_date.desc())
            .first()
        )
        if demo_game:
            user.participated_games.append(demo_game)
            try:
                db.session.commit()
            except SQLAlchemyError as exc:
                db.session.rollback()
                current_app.logger.error(f'Failed to join demo game: {exc}')


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
        redirect_uri = safe_url_for('auth.mastodon_callback', _external=True)
        state = uuid.uuid4().hex
        session['mastodon_state'] = state
        session['mastodon_instance'] = instance
                                                
        app_registration_url = f"https://{instance}/api/v1/apps"
        data = {
            "client_name": "QuestByCycle",
            "redirect_uris": redirect_uri,
            "scopes": "read write follow",
            "website": request.host_url.rstrip('/')
        }
        try:
            response = requests.post(
                app_registration_url,
                data=data,
                timeout=REQUEST_TIMEOUT,
            )
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
    redirect_uri = safe_url_for('auth.mastodon_callback', _external=True)
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
        token_response = requests.post(
            token_url,
            data=data,
            timeout=REQUEST_TIMEOUT,
        )
        token_response.raise_for_status()
        token_data = token_response.json()
    except Exception as e:
        flash(f"Error obtaining access token: {e}", "danger")
        return redirect(url_for('auth.login'))
    access_token = token_data.get("access_token")
    if not access_token:
        flash("Access token not found in response.", "danger")
        return redirect(url_for('auth.login'))
                                   
    verify_url = f"https://{instance}/api/v1/accounts/verify_credentials"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        verify_response = requests.get(
            verify_url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        verify_response.raise_for_status()
        mastodon_user = verify_response.json()
    except Exception as e:
        flash(f"Error verifying Mastodon credentials: {e}", "danger")
        return redirect(url_for('auth.login'))
    mastodon_id = str(mastodon_user.get("id"))
    mastodon_username = mastodon_user.get("username")
    display_name = mastodon_user.get("display_name") or mastodon_username
    mastodon_actor_url = mastodon_user.get("url")
                                                           
    user = User.query.filter_by(mastodon_id=mastodon_id, mastodon_instance=instance).first()
    if user:
        user.mastodon_access_token = access_token
        user.activitypub_id = mastodon_actor_url                              
        db.session.commit()
        login_user(user)
        flash("Logged in via Mastodon. Your federated identity is managed by your Mastodon account.", "success")
    else:
                                                                    
        if current_user.is_authenticated:
            current_user.mastodon_id = mastodon_id
            current_user.mastodon_username = mastodon_username
            current_user.mastodon_instance = instance
            current_user.mastodon_access_token = access_token
            current_user.activitypub_id = mastodon_actor_url                              
            db.session.commit()
            flash("Mastodon account linked successfully. You will federate via your Mastodon account.", "success")
        else:
                                                               
            username = mastodon_username
            new_user = User(
                username=username,
                email=f"{username}@{instance}",                     
                license_agreed=True,
                email_verified=True,
                display_name=display_name,
                mastodon_id=mastodon_id,
                mastodon_username=mastodon_username,
                mastodon_instance=instance,
                mastodon_access_token=access_token,
                activitypub_id=mastodon_actor_url                              
            )
            new_user.set_password(uuid.uuid4().hex)                                           
            db.session.add(new_user)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                flash(f"Error creating user account: {e}", "danger")
                return redirect(url_for('auth.login'))
            login_user(new_user)
            flash("Account created and logged in via Mastodon. You will federate using your Mastodon identity.", "success")
    
    return redirect(url_for('main.index'))


def _is_safe_url(target):
    """
    Ensure that the URL is local to our server.
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https') and
            ref_url.netloc == test_url.netloc)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.  Carries forward game_id, custom_game_code,
    and show_join_custom so that after login we land in the right context.

    Supports both full-page POST (flash+redirect) and
    AJAX POST (JSON response) for use in a modal.
    """
    game_id    = request.values.get('game_id') or None
    quest_id   = request.values.get('quest_id') or None
    show_join  = request.values.get('show_join_custom')
    next_page  = request.values.get('next')

                                           
    if current_user.is_authenticated:
        if next_page and _is_safe_url(next_page):
            target = next_page
        else:
            target = url_for('main.index', show_login=0, next=next_page)
        return redirect(target)

                                                          
    if request.method == 'GET':
        if show_join == '1':
            show_login_flag = 1
        else:
            show_login_flag = 0 if next_page else 1

        return redirect(
            safe_url_for(
                'main.index',
                show_login=show_login_flag,
                show_join_custom=show_join,
                game_id=game_id,
                quest_id=quest_id,
                next=next_page,
            )
        )

                           
    form    = LoginForm()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'


    if not form.validate_on_submit():
        msg = 'Please correct the errors in the login form.'
        if is_ajax:
            return jsonify({
                'success': False,
                'error': msg,
                                                                        
                'show_forgot': False
            }), 400
        flash(msg, 'warning')
        return redirect(
            url_for('main.index',
                    show_login=1,
                    game_id=game_id,
                    quest_id=quest_id,
                    show_join_custom=show_join,
                    next=next_page)
        )

                     
    user = User.query.filter_by(email=form.email.data.lower()).first()
    if not user or not user.check_password(form.password.data):
                         
        msg = 'Invalid email or password.'
        if is_ajax:
            return jsonify({
                'success': False,
                'error': msg,
                                                                         
                'show_forgot': True
            }), 401
        flash(msg, 'danger')
        return redirect(
            url_for('main.index',
                    show_login=1,
                    game_id=game_id,
                    quest_id=quest_id,
                    show_join_custom=show_join,
                    next=next_page)
        )

                                                      
    if current_app.config.get('MAIL_SERVER') and not user.email_verified:
        _send_verification_email(user)
        warning = 'Please verify your email. A new link has been sent.'
        if is_ajax:
            return jsonify({
                'success': False,
                'error': warning,
                'show_forgot': False
            }), 409
        flash(warning, 'warning')
        return redirect(
            url_for('main.index',
                    show_login=1,
                    game_id=game_id,
                    quest_id=quest_id,
                    show_join_custom=show_join,
                    next=next_page)
        )

                 
    login_user(user, remember=form.remember_me.data)
    log_user_ip(user)
    if game_id:
        _join_game_if_provided(user)

                            
    target = next_page if next_page and _is_safe_url(next_page) else url_for('main.index',
                                                                            game_id=game_id,
                                                                            show_join_custom=0)

    if is_ajax:
        return jsonify({
            'success': True,
            'redirect': target
        }), 200

    return redirect(target)


@auth_bp.route('/resend_verification_email', methods=['POST'])
def resend_verification_email():
    """
    Resend the email verification to the user.
    """
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    if user and not user.email_verified:
        token = user.generate_verification_token()
        verify_url = safe_url_for('auth.verify_email', token=token, _external=True)
        html = render_template('verify_email.html', verify_url=verify_url)
        subject = "Please verify your email"
        enqueue_email(user.email, subject, html)
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
def register():
    form = RegistrationForm()

                                    
    game_id = (request.args.get('game_id') or request.form.get('game_id') or None)
    custom_game_code = request.args.get('custom_game_code') or request.form.get('custom_game_code')
    quest_id = (request.args.get('quest_id') or request.form.get('quest_id') or None)
    next_page = request.args.get('next') or request.form.get('next')

                               
    if request.method == 'GET':
                                                             
        if not game_id and next_page:
            parsed = urlparse(next_page)
            if parsed.netloc in (urlparse(request.host_url).netloc, '')\
               and parsed.path.lstrip('/').isdigit():
                game_id = parsed.path.lstrip('/')
                                                           
                custom_game_code = ''

        return redirect(
            safe_url_for(
                'main.index',
                show_register=1,
                game_id=game_id,
                custom_game_code=custom_game_code,
                quest_id=quest_id,
                next=next_page,
                _external=True,
            )
        )

                                                     
    if not form.validate_on_submit():
        flash('Please correct the errors in the registration form.', 'warning')
        return redirect(
            safe_url_for(
                'main.index',
                show_register=1,
                game_id=game_id,
                custom_game_code=custom_game_code,
                quest_id=quest_id,
                next=next_page,
                _external=True,
            )
        )

    if not form.accept_license.data:
        flash('You must agree to the terms of service, license agreement, and privacy policy.', 'warning')
        return redirect(
            safe_url_for(
                'main.index',
                show_register=1,
                game_id=game_id,
                custom_game_code=custom_game_code,
                quest_id=quest_id,
                next=next_page,
                _external=True,
            )
        )

                 
    email = sanitize_html(form.email.data or "").lower()
    if User.query.filter_by(email=email).first():
        flash('Email already registered. Please use a different email.', 'warning')
        return redirect(url_for('auth.register',
                                game_id=game_id,
                                quest_id=quest_id,
                                next=next_page))

    username = _generate_username(email)
    user = User(username=username,
                email=email,
                license_agreed=True,
                email_verified=False,
                is_admin=False,
                created_at=datetime.now(UTC),
                score=0)
    user.set_password(form.password.data)
    db.session.add(user)
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        current_app.logger.error(f'Failed to register user: {exc}')
        flash('Registration failed due to an unexpected error. Please try again.', 'error')
        return redirect(
            safe_url_for(
                'main.index',
                show_register=1,
                game_id=game_id,
                custom_game_code=custom_game_code,
                quest_id=quest_id,
                next=next_page,
                _external=True,
            )
        )

                                     
    create_activitypub_actor(user)

    mail_server = current_app.config.get("MAIL_SERVER")
    if mail_server:
        _send_verification_email(user)
        flash(
            "Registration successful! Please verify your email before logging in.",
            "info",
        )
    else:
        _auto_verify_and_login(user)
                                                                   
                                              
                             
                                                             
                                               
                                                                
                                       

                                              
    if game_id:
        _join_game_if_provided(user)

                                            
    if next_page and _is_safe_url(next_page):
        return redirect(next_page)

    if quest_id:
        return redirect(
            safe_url_for(
                'quests.submit_photo',
                quest_id=quest_id,
                _external=True,
            )
        )

    if game_id:
        return redirect(
            safe_url_for(
                'main.index',
                show_join_custom=0,
                game_id=game_id,
                quest_id=quest_id,
                next=next_page,
                _external=True,
            )
        )

                                                
    return redirect(
        safe_url_for(
            'main.index',
            show_join_custom=1,
            _external=True,
        )
    )



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
                enqueue_email(user.email, "Password Reset Requested", html)
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

                                                                                     
            return redirect(url_for('auth.login'))

                                                              
        field_errors = form.email.errors
        error_msg    = field_errors[0] if field_errors else 'Invalid email.'
        if is_ajax:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

                                                                     
        flash(error_msg, 'danger')
        return redirect(url_for('auth.login'))

                                                                                            
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
    Handle the click on the e-mail verification link.
    Auto-join any game_id or custom_game_code, otherwise pop the picker.
    """
    user = User.verify_verification_token(token)
    if not user:
        flash('Invalid or expired link.', 'danger')
        return redirect(url_for('main.index'))

    user.email_verified = True
    db.session.commit()
    login_user(user)

    code = request.args.get('custom_game_code')
    gid = request.args.get('game_id')
    params = {}

    if code:
        params['custom_game_code'] = code
    elif gid and gid.isdigit():
        params['game_id'] = gid
    else:
                                               
        params['show_join_custom'] = 1

    return redirect(url_for('main.index', **params))


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

                                                                        
    if request.method == 'GET':
        return redirect(url_for('main.index', show_reset=1, token=token))

                                    
    if not form.validate_on_submit():
        error = form.password.errors[0] if form.password.errors else 'Invalid input.'
        if is_ajax:
            return jsonify({'success': False, 'error': error}), 400
        flash(error, 'danger')
        return redirect(url_for('main.index', show_reset=1, token=token))

                               
    user = User.verify_reset_token(token)
    if not user:
        msg = 'The reset link is invalid or has expired.'
        if is_ajax:
            return jsonify({'success': False, 'error': msg}), 400
        flash(msg, 'danger')
        return redirect(url_for('main.index'))

                                 
    user.set_password(form.password.data)
    db.session.commit()

                                            
    login_user(user)

                              
    success_msg = 'Your password has been reset and you are now logged in.'
    if is_ajax:
        return jsonify({
            'success': True,
            'message': success_msg,
            'redirect': url_for('main.index')
        }), 200

                                                      
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
        user.delete_user()
        flash('Your account has been deleted.', 'success')
        logout_user()
        return redirect(url_for('main.index'))
    except Exception as exc:                                
        db.session.rollback()
        current_app.logger.error(f"Error deleting user: {exc}")
        flash('An error occurred while deleting your account.', 'error')
        return redirect(url_for('main.index'))


@auth_bp.route('/check_email', methods=['GET'])
def check_email():
    """
    AJAX endpoint: given ?email=<address>, return JSON { exists: true|false }.
    """
    email = (request.args.get('email') or '').strip().lower()
                                                   
    exists = User.query.filter_by(email=email).first() is not None
    return jsonify({ 'exists': exists })
