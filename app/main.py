"""
Module main.py

This module defines the main blueprint for the Flask application.
It contains routes for the index page, profile management, image resizing,
shout board interactions, leaderboard data, and contact submissions.
"""
import bleach
import io
import logging
import os
import json
from flask import (Blueprint, jsonify, render_template, request, redirect,
                   url_for, flash, current_app, send_file)
from flask_login import current_user, login_required
from flask_wtf.csrf import generate_csrf
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from typing import Any, List
from datetime import datetime, timedelta
from PIL import Image, ExifTags
from pytz import utc
from app.models import (db, Game, User, Quest, Badge, UserQuest, QuestSubmission,
                        QuestLike, ShoutBoardMessage, ShoutBoardLike, ProfileWallMessage,
                        user_games)
from app.forms import (ProfileForm, ShoutBoardForm, ContactForm, BikeForm,
                       LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm)
from app.utils import (save_profile_picture, save_bicycle_picture, send_email)
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
        return activity.timestamp
    if hasattr(activity, 'completed_at') and isinstance(activity.completed_at, datetime):
        return activity.completed_at
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

    # If still None, select the latest demo game
    if game_id is None:
        default_demo_game = Game.query.filter_by(is_demo=True).order_by(Game.start_date.desc()).first()
        if default_demo_game:
            game_id = default_demo_game.id
        else:
            flash("No demo game available", "error")
            return None, None

    game = Game.query.get(game_id)
    # Ensure the user has joined the game (auto-join if they requested it by URL)
    if game and current_user.is_authenticated:
        if game not in current_user.participated_games:
            # auto-register the user for the requested game
            stmt = user_games.insert().values(
                user_id=current_user.id,
                game_id=game.id
            )
            db.session.execute(stmt)
            db.session.commit()
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


def _prepare_user_data(game_id, profile):
    # 1. Bulk-load all game badges and their quests in one go
    badges = (
        Badge.query
             .options(joinedload(Badge.quests))   # eager-load the quests relationship
             .join(Quest)
             .filter(Quest.game_id == game_id, Quest.badge_id.isnot(None))
             .distinct()
             .all()
    )

    # 2. Build a map of user's completions, in one query
    completions = (
        db.session.query(
            UserQuest.quest_id,
            func.max(UserQuest.completions).label('completions')
        )
        .filter(UserQuest.user_id == profile.id)
        .group_by(UserQuest.quest_id)
        .all()
    )
    user_completions_map = {q_id: c for q_id, c in completions}

    # 3. Enhance badges in-memory
    enhanced_badges = []
    for badge in badges:
        # Only keep quests for this game
        awarding = [q for q in badge.quests if q.game_id == game_id]
        task_names            = ", ".join(q.title for q in awarding)
        task_ids              = ", ".join(str(q.id) for q in awarding)
        badge_awarded_counts  = ", ".join(str(q.badge_awarded) for q in awarding)

        # Look up the user's max completions for any of those quests
        user_counts = [user_completions_map.get(q.id, 0) for q in awarding]
        is_complete = any(c >= q.badge_awarded for q, c in zip(awarding, user_counts))
        max_completion = max(user_counts, default=0)

        enhanced_badges.append({
            'id':                    badge.id,
            'name':                  badge.name,
            'description':           badge.description,
            'image':                 badge.image,
            'category':              badge.category,
            'task_names':            task_names,
            'task_ids':              task_ids,
            'badge_awarded_counts':  badge_awarded_counts,
            'user_completions':      max_completion,
            'is_complete':           is_complete
        })

    # 4. Split earned / unearned here, once
    earned = [b for b in enhanced_badges if b['is_complete']]
    unearned = [b for b in enhanced_badges if not b['is_complete']]

    return earned, unearned


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
    forgot_form = ForgotPasswordForm()
    reset_form = ResetPasswordForm()
    start_onboarding = False

    now = datetime.now(utc)

    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id

    # Check if we should prompt custom-game join modal
    show_login       = request.args.get('show_login') == '1'
    show_join_custom = request.args.get('show_join_custom') == '1'
    explicit_game    = bool(request.args.get('game_id'))
    if current_user.is_authenticated \
        and not current_user.participated_games \
        and not explicit_game:
        show_join_custom = True

    if show_join_custom and not current_user.is_authenticated and not show_login:
        return redirect(url_for(
            'auth.login',
            next=request.full_path,
            show_join_custom=1
        ))

    # Load game context without auto-join when prompting custom-join
    if show_join_custom:
        game = None
        game_id = None
    else:
        game, game_id = _select_game(game_id)

    # Redirect to login/modal only once
    if not show_join_custom and (game is None or game_id is None) and request.args.get('show_login') != '1':
        demo = (Game.query
                    .filter_by(is_demo=True)
                    .order_by(Game.start_date.desc())
                    .first())
        return redirect(url_for('main.index', game_id=demo.id, show_login=1))

    if game is None or game_id is None:
        demo = (Game.query
                    .filter_by(is_demo=True)
                    .order_by(Game.start_date.desc())
                    .first())
        game, game_id = demo, demo.id

    # Load user-specific data
    profile = None
    user_quests = []
    total_points = None
    if current_user.is_authenticated:
        user_quests = UserQuest.query.filter_by(user_id=current_user.id).all()
        total_points = sum(ut.points_awarded for ut in user_quests if ut.quest.game_id == game_id)
        profile = User.query.get_or_404(user_id)
        if not profile.display_name:
            profile.display_name = profile.username

        # Compute the list of games the user has joined
        user_games_list = (
            db.session.query(Game, user_games.c.joined_at)
                        .join(user_games, user_games.c.game_id == Game.id)
                        .filter(user_games.c.user_id == current_user.id)
                        .all()
        )
    else:
        user_games_list = []

    # Prepare quests and activities
    quests, activities = _prepare_quests(game, user_id, user_quests, now)
    categories = sorted({quest.category for quest in quests if quest.category})

    # Custom vs closed games (exclude demos)
    all_custom = Game.query.filter(
        Game.custom_game_code.isnot(None),
        Game.is_public.is_(True),
        Game.is_demo.is_(False)
    ).all()
    open_games = [g for g in all_custom if g.start_date <= now and (not g.end_date or g.end_date >= now)]
    closed_games = [g for g in all_custom if g.end_date and g.end_date < now]

    # Ongoing demo for UI context
    demo_game = (Game.query
                    .filter(
                        Game.is_demo.is_(True),
                        Game.start_date <= now,
                        (Game.end_date == None) | (Game.end_date >= now)
                    )
                    .order_by(Game.start_date.desc())
                    .first())

    # Participation flags
    has_joined = (current_user.is_authenticated and game in current_user.participated_games)
    explicit_game = bool(request.args.get('game_id'))
    suppress_custom = request.args.get('show_join_custom') == '0'
    show_join_modal = (
        not has_joined and
        not explicit_game and
        not suppress_custom and
        not show_join_custom
    )

    # Prepare badge lists
    if current_user.is_authenticated:
        earned_badges, unearned_badges = _prepare_user_data(game_id, profile)
    else:
        earned_badges, unearned_badges = [], []

    # Render
    return render_template(
        'index.html',
        form=ShoutBoardForm(),
        badges=earned_badges,
        earned_badges=earned_badges,
        unearned_badges=unearned_badges,
        games=user_games_list,
        game=game,
        user_games=user_games_list,
        activities=activities,
        quests=quests,
        categories=categories,
        show_join_modal=show_join_modal,
        show_join_custom=show_join_custom,
        game_participation={game.id: (game in current_user.participated_games if current_user.is_authenticated else [])},
        selected_quest=Quest.query.get(quest_id) if quest_id else None,
        has_joined=has_joined,
        profile=profile,
        user_quests=user_quests,
        total_points=total_points,
        completions=UserQuest.query.filter(UserQuest.completions > 0).order_by(UserQuest.completed_at.desc()).all(),
        open_games=open_games,
        closed_games=closed_games,
        demo_game=demo_game,
        now=now,
        selected_game_id=game_id or 0,
        selected_quest_id=quest_id,
        next=request.args.get('next'),
        selected_game=game,
        quest_id=quest_id,
        start_onboarding=start_onboarding,
        login_form=login_form,
        register_form=register_form,
        forgot_form=forgot_form,
        reset_form=reset_form
    )


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
        return


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

        # --- notify your followers ---
        from app.models import Notification
        follower_ids = [rel.follower_id for rel in current_user.followers]
        for fid in follower_ids:
            notif = Notification(
                user_id=fid,
                type='shout',
                payload={'shout_id': shout_message.id, 'from_user': current_user.id}
            )
            db.session.add(notif)
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
            'upload_to_mastodon': user.upload_to_mastodon,
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

    # Add a flag for whether the current_user follows this profile
    response_data['current_user_following'] = (
        current_user.is_authenticated and
        User.query.get(user_id) in current_user.following
    )

    return jsonify(response_data)


def _coerce_to_list(raw: Any) -> List[str]:
    """
    Turn anything—string, list, tuple, JSON literal—into a Python list of strings.
    """
    # Already good
    if isinstance(raw, (list, tuple)):
        return list(raw)

    # A JSON‐encoded list
    if isinstance(raw, str):
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, list):
                return loaded
        except json.JSONDecodeError:
            pass

        # Fallback: maybe comma-separated?
        return [item.strip() for item in raw.split(',') if item.strip()]

    # Nothing else
    return []


@main_bp.route('/profile/<int:user_id>/edit', methods=['POST'])
@login_required
def edit_profile(user_id):
    """
    Edit a user's profile details including profile picture and personal info.
    """
    if user_id != current_user.id:
        logger.warning('Unauthorized access attempt by user %s', current_user.id)
        return jsonify({'error': 'Unauthorized access'}), 403

    form = ProfileForm()
    user = User.query.get_or_404(user_id)

    if not form.validate_on_submit():
        # Collect WTForms errors and return them
        errors = {f: e for f, e in form.errors.items()}
        logger.debug('Form validation failed: %s', errors)
        return jsonify({'error': 'Invalid form submission', 'details': errors}), 400

    try:
        # — profile picture logic unchanged —
        pic = request.files.get('profile_picture')
        if pic and pic.filename:
            user.profile_picture = save_profile_picture(pic, user.profile_picture)
            logger.debug('Updated profile picture: %s', user.profile_picture)

        user.display_name = form.display_name.data
        user.age_group = form.age_group.data
        user.interests = form.interests.data or []
        user.riding_preferences = _coerce_to_list(form.riding_preferences.data)
        user.ride_description = form.ride_description.data
        user.upload_to_socials = form.upload_to_socials.data
        user.upload_to_mastodon = form.upload_to_mastodon.data
        user.show_carbon_game = form.show_carbon_game.data

        db.session.commit()
        logger.debug('Profile updated successfully in the database.')
        return jsonify({'success': True}), 200

    except Exception as exc:
        db.session.rollback()
        logger.error('Exception occurred: %s', exc)
        return


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
            return

    logger.debug('Bike form validation failed.')
    for field, errors in bike_form.errors.items():
        for error in errors:
            logger.debug('Error in the %s field - %s', field, error)
    return


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
        recipient = "jaron.rosenau+QbCFeedback@gmail.com"

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
                return
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
        return
