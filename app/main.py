"""
Module main.py

This module defines the main blueprint for the Flask application.
It contains routes for the index page, profile management, image resizing,
shout board interactions, leaderboard data, and contact submissions.
"""

import io
import logging
import os
from datetime import datetime, timedelta

from flask import (Blueprint, jsonify, render_template, request, redirect,
                   url_for, flash, current_app, send_file)
from flask_login import current_user, login_required
from flask_wtf.csrf import generate_csrf
from PIL import Image, ExifTags
from pytz import utc
import bleach

from app.models import (db, Game, User, Quest, Badge, UserQuest, QuestSubmission,
                        QuestLike, ShoutBoardMessage, ShoutBoardLike, ProfileWallMessage,
                        user_games)
from app.forms import (ProfileForm, ShoutBoardForm, ContactForm, BikeForm,
                       LoginForm, RegistrationForm)
from app.utils import (save_profile_picture, save_bicycle_picture, send_email,
                       allowed_file, enhance_badges_with_task_info, get_game_badges)
from .config import load_config

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create blueprint
main_bp = Blueprint('main', __name__)

# Allowed HTML tags and attributes for sanitization
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

# Load configuration
config = load_config()


def sanitize_html(html_content):
    """
    Sanitize HTML content using bleach with a set of allowed tags and attributes.
    """
    return bleach.clean(html_content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)


def get_datetime(activity):
    """
    Retrieve a datetime from an activity object.
    Checks for either a 'timestamp' or 'completed_at' attribute.
    """
    if hasattr(activity, 'timestamp') and isinstance(activity.timestamp, datetime):
        return activity.timestamp.replace(tzinfo=None) if activity.timestamp.tzinfo is not None else activity.timestamp
    if hasattr(activity, 'completed_at') and isinstance(activity.completed_at, datetime):
        return activity.completed_at.replace(tzinfo=None)
    raise ValueError("Activity object does not contain valid timestamp information.")


def _select_game(game_id):
    """
    Determine the game to display based on the provided game_id and current_user.
    Returns a tuple (game, game_id). If no game is found, redirects to an error route.
    """
    # Set game_id from current_user if not provided
    if game_id is None and current_user.is_authenticated:
        if current_user.selected_game_id:
            game_id = current_user.selected_game_id
        else:
            joined_games = current_user.participated_games
            if joined_games:
                game_id = joined_games[0].id

    # If still None, select the latest tutorial game
    if game_id is None:
        default_tutorial_game = Game.query.filter_by(is_tutorial=True).order_by(Game.start_date.desc()).first()
        if default_tutorial_game:
            game_id = default_tutorial_game.id
        else:
            flash("No tutorial game available", "error")
            return None, None

    game = Game.query.get(game_id)
    # Ensure the user has joined the game
    if game and current_user.is_authenticated:
        if game not in current_user.participated_games:
            return redirect(url_for('main.index')), None
        if current_user.selected_game_id != game_id:
            current_user.selected_game_id = game_id
            db.session.commit()
    return game, game_id


def _prepare_quests(game, user_id, user_quests, now):
    """
    Prepare quest-related data for display.
    Modifies each quest by setting completion counts, eligibility, and timestamps.
    Returns a list of quests and sorted activities.
    """
    quests = Quest.query.filter_by(game_id=game.id, enabled=True).all() if game else []
    period_start_map = {
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1),
        'monthly': timedelta(days=30)
    }
    completed_quests = UserQuest.query.filter(UserQuest.completions > 0).order_by(UserQuest.completed_at.desc()).all()

    for quest in quests:
        quest.total_completions = QuestSubmission.query.filter_by(quest_id=quest.id).count()
        quest.personal_completions = QuestSubmission.query.filter_by(
            quest_id=quest.id, user_id=user_id).count() if user_id else 0
        quest.completions_within_period = 0
        quest.can_verify = False
        quest.last_completion = None
        quest.first_completion_in_period = None
        quest.next_eligible_time = None
        quest.completion_timestamps = []

        if user_id:
            period_start = now - period_start_map.get(quest.frequency, timedelta(days=1))
            submissions = QuestSubmission.query.filter(
                QuestSubmission.user_id == user_id,
                QuestSubmission.quest_id == quest.id,
                QuestSubmission.timestamp >= period_start
            ).all()

            if submissions:
                quest.completions_within_period = len(submissions)
                quest.first_completion_in_period = min(submissions, key=lambda x: x.timestamp).timestamp
                quest.completion_timestamps = [sub.timestamp for sub in submissions]

            relevant_user_quests = [ut for ut in user_quests if ut.quest_id == quest.id]
            quest.last_completion = max((ut.completed_at for ut in relevant_user_quests), default=None)

            if quest.personal_completions < quest.completion_limit:
                quest.can_verify = True
            else:
                last_submission = max(submissions, key=lambda x: x.timestamp, default=None)
                if last_submission:
                    increment_map = {
                        'daily': timedelta(days=1),
                        'weekly': timedelta(weeks=1),
                        'monthly': timedelta(days=30)
                    }
                    quest.next_eligible_time = last_submission.timestamp + increment_map.get(quest.frequency, timedelta(days=1))

    # Combine pinned messages and completed quests into activities
    pinned_messages = ShoutBoardMessage.query.filter_by(is_pinned=True, game_id=game.id).order_by(
        ShoutBoardMessage.timestamp.desc()).all()
    unpinned_messages = ShoutBoardMessage.query.filter_by(is_pinned=False, game_id=game.id).order_by(
        ShoutBoardMessage.timestamp.desc()).all()
    activities = pinned_messages + (unpinned_messages + [ut for ut in completed_quests if ut.quest.game_id == game.id])
    activities.sort(key=get_datetime, reverse=True)

    quests.sort(key=lambda x: (-x.is_sponsored, -x.personal_completions, -x.total_completions))
    return quests, activities


def _prepare_user_data(game_id, profile, user_quests):
    """
    Prepare badge information and user game list.
    Returns a tuple (all_badges, earned_badges, user_games_list).
    """
    if game_id:
        all_badges = get_game_badges(game_id)
    else:
        all_badges = Badge.query.all()

    earned_badges_set = set(profile.badges)
    all_badges = enhance_badges_with_task_info(all_badges, game_id, current_user.id)
    earned_badges = enhance_badges_with_task_info(list(earned_badges_set), game_id)

    user_games_list = db.session.query(Game, user_games.c.joined_at).join(
        user_games, user_games.c.game_id == Game.id).filter(user_games.c.user_id == current_user.id).all()
    return all_badges, earned_badges, user_games_list


def _prepare_carousel_images(game_id):
    """
    Prepare carousel image data for the given game.
    Returns a list of dictionaries with image data.
    """
    carousel_images = []
    if current_user.is_authenticated and game_id:
        quest_submissions = QuestSubmission.query.join(Quest).filter(Quest.game_id == game_id).all()
        for submission in quest_submissions:
            if submission.image_url:
                # Normalize image path
                image_url = submission.image_url.lstrip('/').replace('static/', '')
                if not image_url.startswith('images/'):
                    image_url = f'images/{image_url}'
                carousel_images.append({
                    'small': image_url,
                    'medium': image_url,
                    'large': image_url,
                    'quest_title': submission.quest.title,
                    'comment': submission.comment
                })
    return carousel_images


@main_bp.route('/', defaults={'game_id': None, 'quest_id': None, 'user_id': None})
@main_bp.route('/<int:game_id>', defaults={'quest_id': None, 'user_id': None})
@main_bp.route('/<int:game_id>/<int:quest_id>', defaults={'user_id': None})
@main_bp.route('/<int:game_id>/<int:quest_id>/<int:user_id>')
def index(game_id, quest_id, user_id):
    """
    Render the main index page with game, quest, activity, badge, and profile data.
    """
    login_form = LoginForm()
    register_form = RegistrationForm()
    start_onboarding = False
    now = datetime.now(utc)

    # Determine user_id based on authentication
    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id

    game, game_id = _select_game(game_id)
    if game is None or game_id is None:
        # Redirect if game selection failed
        return redirect(url_for('some_error_route'))

    # Load user-specific data if authenticated
    profile = None
    user_quests = []
    total_points = None
    all_badges = []
    earned_badges = []
    if current_user.is_authenticated:
        user_quests = UserQuest.query.filter_by(user_id=current_user.id).all()
        total_points = sum(ut.points_awarded for ut in user_quests if ut.quest.game_id == game_id)
        profile = User.query.get_or_404(user_id)
        if not profile.display_name:
            profile.display_name = profile.username
        all_badges, earned_badges, user_games_list = _prepare_user_data(game_id, profile, user_quests)
    else:
        user_games_list = []

    quests, activities = _prepare_quests(game, user_id, user_quests, now)
    carousel_images = _prepare_carousel_images(game_id)
    categories = sorted({quest.category for quest in quests if quest.category})

    return render_template('index.html',
                           form=ShoutBoardForm(),
                           badges=earned_badges,
                           all_badges=all_badges,
                           games=user_games_list,
                           game=game,
                           user_games=user_games_list,
                           activities=activities,
                           quests=quests,
                           categories=categories,
                           game_participation={game.id: (game in (current_user.participated_games if current_user.is_authenticated else []))},
                           selected_quest=Quest.query.get(quest_id) if quest_id else None,
                           has_joined=(game in (current_user.participated_games if current_user.is_authenticated else [])) if game else False,
                           profile=profile,
                           user_quests=user_quests,
                           carousel_images=carousel_images,
                           total_points=total_points,
                           completions=UserQuest.query.filter(UserQuest.completions > 0).order_by(UserQuest.completed_at.desc()).all(),
                           custom_games=Game.query.filter(Game.custom_game_code.isnot(None), Game.is_public.is_(True)).all(),
                           selected_game_id=game_id or 0,
                           selected_game=game,
                           quest_id=quest_id,
                           start_onboarding=start_onboarding,
                           login_form=login_form,
                           register_form=register_form)


@main_bp.route('/mark-onboarding-complete', methods=['POST'])
@login_required
def mark_onboarding_complete():
    """
    Mark the onboarding process as complete for the current user.
    """
    try:
        current_user.onboarded = True
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as exc:
        logger.error(f"Error marking onboarding complete: {exc}")
        return jsonify({'success': False, 'error': str(exc)}), 500


@main_bp.route('/shout-board/<int:game_id>', methods=['POST'])
@login_required
def shout_board(game_id):
    """
    Process a new shout board message submission.
    """
    form = ShoutBoardForm()
    if not form.game_id.data:
        form.game_id.data = game_id

    if form.validate_on_submit():
        is_pinned = 'is_pinned' in request.form
        message_content = sanitize_html(form.message.data)
        shout_message = ShoutBoardMessage(
            message=message_content,
            user_id=current_user.id,
            game_id=game_id,
            is_pinned=is_pinned
        )
        db.session.add(shout_message)
        db.session.commit()
        flash('Your message has been posted!', 'success')
        return redirect(url_for('main.index', game_id=game_id))
    logger.debug("Form Errors: %s", form.errors)
    flash('There was an error with your submission.', 'error')
    return redirect(url_for('main.index', game_id=game_id))


@main_bp.route('/like-message/<int:message_id>', methods=['POST'])
@login_required
def like_message(message_id):
    """
    Process a like action on a shout board message.
    """
    message = ShoutBoardMessage.query.get_or_404(message_id)
    already_liked = ShoutBoardLike.query.filter_by(user_id=current_user.id, message_id=message.id).first() is not None

    if not already_liked:
        new_like = ShoutBoardLike(user_id=current_user.id, message_id=message.id)
        db.session.add(new_like)
        db.session.commit()
        success = True
    else:
        success = False

    new_like_count = ShoutBoardLike.query.filter_by(message_id=message_id).count()
    return jsonify(success=success, new_like_count=new_like_count, already_liked=already_liked)


@main_bp.route('/leaderboard_partial')
@login_required
def leaderboard_partial():
    """
    Provide leaderboard data for a specific game.
    """
    selected_game_id = request.args.get('game_id', type=int)
    if selected_game_id:
        game = Game.query.get(selected_game_id)
        if not game:
            return jsonify({'error': 'Game not found'}), 404

        top_users_query = db.session.query(
            User.id,
            User.username,
            User.display_name,
            db.func.sum(UserQuest.points_awarded).label('total_points')
        ).join(UserQuest, UserQuest.user_id == User.id
        ).join(Quest, Quest.id == UserQuest.quest_id
        ).filter(Quest.game_id == selected_game_id
        ).group_by(User.id, User.username, User.display_name
        ).order_by(db.func.sum(UserQuest.points_awarded).desc()
        ).all()

        top_users = [{
            'user_id': uid,
            'username': username,
            'display_name': display_name,
            'total_points': total_points
        } for uid, username, display_name, total_points in top_users_query]

        total_game_points = db.session.query(
            db.func.sum(UserQuest.points_awarded)
        ).join(Quest, UserQuest.quest_id == Quest.id
        ).filter(Quest.game_id == selected_game_id
        ).scalar() or 0

        return jsonify({
            'top_users': top_users,
            'total_game_points': total_game_points,
            'game_goal': game.game_goal if game.game_goal else None
        })


@main_bp.route('/profile/<int:user_id>')
@login_required
def user_profile(user_id):
    """
    Return JSON data for a user's profile including quests, badges,
    participated games, quest submissions, and profile messages.
    """
    user = User.query.get_or_404(user_id)
    user_quests = UserQuest.query.filter(UserQuest.user_id == user.id, UserQuest.completions > 0).all()
    badges = user.badges
    participated_games = user.participated_games
    quest_submissions = user.quest_submissions
    profile_messages = ProfileWallMessage.query.filter_by(user_id=user_id).order_by(
        ProfileWallMessage.timestamp.desc()).all()

    riding_preferences_choices = [
        ('new_novice', 'New and novice rider'),
        ('elementary_school', 'In elementary school or younger'),
        ('middle_school', 'In Middle school'),
        ('high_school', 'In High school'),
        ('college', 'College student'),
        ('families', 'Families who ride with their children'),
        ('grandparents', 'Grandparents who ride with their grandchildren'),
        ('seasoned', 'Seasoned riders who ride all over town for their transportation'),
        ('adaptive', 'Adaptive bike users'),
        ('occasional', 'Occasional rider'),
        ('ebike', 'E-bike rider'),
        ('long_distance', 'Long distance rider'),
        ('no_car', 'Don’t own a car'),
        ('commute', 'Commute by bike'),
        ('seasonal', 'Seasonal riders: I don’t like riding in inclement weather'),
        ('environmentally_conscious', 'Environmentally Conscious Riders'),
        ('social', 'Social Riders'),
        ('fitness_focused', 'Fitness-Focused Riders'),
        ('tech_savvy', 'Tech-Savvy Riders'),
        ('local_history', 'Local History or Culture Enthusiasts'),
        ('advocacy_minded', 'Advocacy-Minded Riders'),
        ('bike_collectors', 'Bike Collectors or Bike Equipment Geek'),
        ('freakbike', 'Freakbike rider/maker')
    ]

    response_data = {
        'current_user_id': current_user.id,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'profile_picture': user.profile_picture,
            'display_name': user.display_name,
            'interests': user.interests,
            'age_group': user.age_group,
            'riding_preferences': user.riding_preferences or [],
            'ride_description': user.ride_description,
            'bike_picture': user.bike_picture,
            'bike_description': user.bike_description,
            'upload_to_socials': user.upload_to_socials,
            'show_carbon_game': user.show_carbon_game,
            'badges': [{'id': badge.id, 'name': badge.name, 'description': badge.description,
                        'category': badge.category, 'image': badge.image} for badge in badges]
        },
        'user_quests': [
            {'id': quest.id, 'completions': quest.completions} for quest in user_quests
        ],
        'profile_messages': [
            {
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%B %d, %Y %H:%M'),
                'author_id': message.author_id,
                'author': {
                    'username': message.author.username,
                    'display_name': message.author.display_name
                },
                'parent_id': message.parent_id
            } for message in profile_messages
        ],
        'participated_games': [
            {'id': game.id, 'title': game.title, 'description': game.description,
             'start_date': game.start_date.strftime('%B %d, %Y'),
             'end_date': game.end_date.strftime('%B %d, %Y')}
            for game in participated_games
        ],
        'quest_submissions': [
            {'id': submission.id,
             'quest': {'title': submission.quest.title},
             'comment': submission.comment,
             'timestamp': submission.timestamp.strftime('%B %d, %Y %H:%M'),
             'image_url': submission.image_url,
             'twitter_url': submission.twitter_url,
             'fb_url': submission.fb_url,
             'instagram_url': submission.instagram_url}
            for submission in quest_submissions
        ],
        'riding_preferences_choices': riding_preferences_choices
    }
    return jsonify(response_data)


@main_bp.route('/profile/<int:user_id>/edit', methods=['POST'])
@login_required
def edit_profile(user_id):
    """
    Edit a user's profile details including profile picture and personal info.
    """
    if user_id != current_user.id:
        logger.warning('Unauthorized access attempt by user %s', current_user.id)
        return jsonify({'error': 'Unauthorized access'}), 403

    profile_form = ProfileForm()
    user = User.query.get_or_404(user_id)

    if profile_form.validate_on_submit():
        try:
            profile_picture = request.files.get('profile_picture')
            if profile_picture and hasattr(profile_picture, 'filename'):
                user.profile_picture = save_profile_picture(profile_picture, user.profile_picture)
                logger.debug('Updated profile picture: %s', user.profile_picture)

            user.display_name = profile_form.display_name.data
            user.age_group = profile_form.age_group.data
            user.interests = profile_form.interests.data
            user.riding_preferences = request.form.getlist('riding_preferences')
            user.ride_description = profile_form.ride_description.data
            user.upload_to_socials = profile_form.upload_to_socials.data
            user.show_carbon_game = profile_form.show_carbon_game.data

            db.session.commit()
            logger.debug('Profile updated successfully in the database.')
            return jsonify({'success': True})
        except Exception as exc:
            db.session.rollback()
            logger.error('Exception occurred: %s', exc)
            return jsonify({'error': f'Failed to update profile: {str(exc)}'}), 500

    for field, errors in profile_form.errors.items():
        for error in errors:
            logger.debug('Error in the %s field - %s', field, error)
    return jsonify({'error': 'Invalid form submission'}), 400


@main_bp.route('/profile/<int:user_id>/edit-bike', methods=['POST'])
@login_required
def edit_bike(user_id):
    """
    Edit a user's bike information including bike picture and description.
    """
    if user_id != current_user.id:
        logger.warning('Unauthorized access attempt by user %s', current_user.id)
        return jsonify({'error': 'Unauthorized access'}), 403

    bike_form = BikeForm()
    user = User.query.get_or_404(user_id)

    if bike_form.validate_on_submit():
        try:
            bike_picture = request.files.get('bike_picture')
            if bike_picture and bike_picture.filename:
                user.bike_picture = save_bicycle_picture(bike_picture, user.bike_picture)
                logger.debug('Updated bike picture: %s', user.bike_picture)

            user.bike_description = bike_form.bike_description.data
            db.session.commit()
            logger.debug('Bike updated successfully in the database.')
            return jsonify({'success': True})
        except Exception as exc:
            db.session.rollback()
            logger.error('Exception occurred: %s', exc)
            return jsonify({'error': f'Failed to update bike: {str(exc)}'}), 500

    logger.debug('Bike form validation failed.')
    for field, errors in bike_form.errors.items():
        for error in errors:
            logger.debug('Error in the %s field - %s', field, error)
    return jsonify({'error': 'Invalid form submission'}), 400


@main_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """
    Update a user's profile and bike details.
    """
    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file:
            old_filename = current_user.profile_picture
            current_user.profile_picture = save_profile_picture(file, old_filename)

    current_user.display_name = sanitize_html(request.form.get('display_name', current_user.display_name))
    current_user.age_group = sanitize_html(request.form.get('age_group', current_user.age_group))
    current_user.interests = sanitize_html(request.form.get('interests', current_user.interests))
    current_user.riding_preferences = request.form.getlist('riding_preferences')
    current_user.ride_description = sanitize_html(request.form.get('ride_description', current_user.ride_description))
    current_user.bike_description = sanitize_html(request.form.get('bike_description', current_user.bike_description))
    current_user.upload_to_socials = 'upload_to_socials' in request.form
    current_user.show_carbon_game = 'show_carbon_game' in request.form

    if 'bike_picture' in request.files:
        bike_picture_file = request.files['bike_picture']
        if bike_picture_file and allowed_file(bike_picture_file.filename):
            bike_filename = save_profile_picture(bike_picture_file)
            current_user.bike_picture = bike_filename

    db.session.commit()
    return jsonify(success=True)


@main_bp.route('/like_quest/<int:quest_id>', methods=['POST'])
@login_required
def like_quest(quest_id):
    """
    Process a like action on a quest.
    """
    quest = Quest.query.get_or_404(quest_id)
    already_liked = QuestLike.query.filter_by(user_id=current_user.id, quest_id=quest.id).first() is not None

    if not already_liked:
        new_like = QuestLike(user_id=current_user.id, quest_id=quest.id)
        db.session.add(new_like)
        db.session.commit()
        success = True
    else:
        success = False

    new_like_count = QuestLike.query.filter_by(quest_id=quest.id).count()
    return jsonify(success=success, new_like_count=new_like_count, already_liked=already_liked)


@main_bp.route('/pin_message/<int:game_id>/<int:message_id>', methods=['POST'])
@login_required
def pin_message(game_id, message_id):
    """
    Toggle the pin status of a shout board message.
    """
    message = ShoutBoardMessage.query.get_or_404(message_id)
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('main.index'))
    message.is_pinned = not message.is_pinned
    db.session.commit()
    flash('Message pin status updated.', 'success')
    return redirect(url_for('main.index', game_id=game_id))


@main_bp.route('/contact', methods=['POST'])
@login_required
def contact():
    """
    Process a contact form submission.
    """
    form = ContactForm()
    if form.validate_on_submit():
        message = sanitize_html(form.message.data)
        subject = "New Contact Form Submission"
        recipient = current_app.config['MAIL_DEFAULT_SENDER']

        user_info = None
        if current_user.is_authenticated:
            user_info = {
                "username": current_user.username,
                "email": current_user.email,
                "is_admin": current_user.is_admin,
                "created_at": current_user.created_at,
                "license_agreed": current_user.license_agreed,
                "display_name": current_user.display_name,
                "age_group": current_user.age_group,
                "interests": current_user.interests,
                "email_verified": current_user.email_verified,
            }

        html = render_template('contact_email.html', message=message, user_info=user_info)
        try:
            send_email(recipient, subject, html)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=True)
            flash('Your message has been sent successfully.', 'success')
        except Exception as exc:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=False, message="Failed to send your message"), 500
            flash('Failed to send your message. Please try again later.', 'error')
            current_app.logger.error('Failed to send contact form message: %s', exc)
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message="Validation failed"), 400
        flash('Validation failed. Please ensure all fields are filled correctly.', 'warning')
    return redirect(url_for('main.index'))


@main_bp.route('/refresh-csrf', methods=['GET'])
def refresh_csrf():
    """
    Refresh and return a new CSRF token.
    """
    new_csrf_token = generate_csrf()
    response = jsonify({'csrf_token': new_csrf_token})
    response.set_cookie(
        'csrf_token',
        new_csrf_token,
        secure=True,
        httponly=True,
        samesite='Strict'
    )
    return response


@main_bp.route('/resize_image')
def resize_image():
    """
    Resize an image to a given width while maintaining aspect ratio.
    The image is served in WEBP format.
    """
    image_path = request.args.get('path')
    width = request.args.get('width', type=int)

    if not image_path or not width:
        return jsonify({'error': "Invalid request: Missing 'path' or 'width'"}), 400

    try:
        full_image_path = os.path.abspath(os.path.join(current_app.static_folder, image_path))
        if not full_image_path.startswith(os.path.abspath(current_app.static_folder)):
            current_app.logger.error("Attempted path traversal detected: %s", image_path)
            return jsonify({'error': 'Invalid file path'}), 400

        if not os.path.exists(full_image_path):
            current_app.logger.error("File not found: %s", full_image_path)
            return jsonify({'error': 'File not found'}), 404

        with Image.open(full_image_path) as img:
            # Correct image orientation using EXIF data
            orientation_tag = None
            for tag, value in ExifTags.TAGS.items():
                if value == 'Orientation':
                    orientation_tag = tag
                    break

            try:
                exif = img._getexif()
                if exif is not None and orientation_tag in exif:
                    orientation_value = exif.get(orientation_tag)
                    if orientation_value == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation_value == 6:
                        img = img.rotate(-90, expand=True)
                    elif orientation_value == 8:
                        img = img.rotate(90, expand=True)
            except (AttributeError, KeyError, IndexError):
                pass

            ratio = width / float(img.width)
            height = int(img.height * ratio)
            img_resized = img.resize((width, height), Image.Resampling.LANCZOS)
            img_io = io.BytesIO()

            if img_resized.mode in ('RGBA', 'LA') or (img_resized.mode == 'P' and 'transparency' in img_resized.info):
                img_resized = img_resized.convert('RGBA')
                img_resized.save(img_io, 'WEBP')
            else:
                img_resized = img_resized.convert('RGB')
                img_resized.save(img_io, 'WEBP')

            img_io.seek(0)
            return send_file(img_io, mimetype='image/webp')

    except Exception as exc:
        current_app.logger.error("Exception occurred during image processing: %s", exc)
        return jsonify({'error': 'Internal server error'}), 500
