"""
Module main.py

This module defines the main blueprint for the Flask application.
It contains routes for the index page, profile management, image resizing,
shout board interactions, leaderboard data, and contact submissions.
"""
import io
import logging
import os
import json
from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_file,
    send_from_directory,
)
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required
from app.decorators import require_admin
from flask_wtf.csrf import generate_csrf
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from typing import Any, List
from datetime import datetime, timedelta
from PIL import Image, UnidentifiedImageError
from app.constants import UTC, FREQUENCY_DELTA
from urllib.parse import urlparse, parse_qs
from zoneinfo import ZoneInfo

from app.models import db, user_games
from app.models.game import Game, ShoutBoardMessage
from app.models.user import User, UserQuest, ProfileWallMessage
from app.models.quest import Quest, QuestSubmission
from app.models.badge import Badge
from app.forms import (
    ProfileForm,
    ShoutBoardForm,
    ContactForm,
    BikeForm,
    LoginForm,
    RegistrationForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    MastodonLoginForm,
)
from app.utils.file_uploads import (
    save_profile_picture,
    save_bicycle_picture,
    correct_image_orientation,
)
from app.utils import sanitize_html, get_int_param
from app.utils.calendar_utils import _parse_calendar_tz
from .config import load_config, AppConfig
from app.tasks import enqueue_email


logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

                    
config: AppConfig = load_config()


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
                                                   
    if game_id is None and current_user.is_authenticated:
        if current_user.selected_game_id:
            game_id = current_user.selected_game_id
        else:
            joined_games = current_user.participated_games
            if joined_games:
                game_id = joined_games[0].id

                                                
    if game_id is None:
        default_demo_game = Game.query.filter_by(is_demo=True).order_by(Game.start_date.desc()).first()
        if default_demo_game:
            game_id = default_demo_game.id
        else:
            flash("No demo game available", "error")
            return None, None

    game = Game.query.get(game_id)
                                                                                 
    if game and current_user.is_authenticated:
        if game not in current_user.participated_games:
                                                           
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
            period_start = now - FREQUENCY_DELTA.get(quest.frequency, timedelta(days=1))
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
                start = quest.calendar_event_start
                if start and not start.tzinfo:
                    start = start.replace(tzinfo=UTC)
                if quest.from_calendar and start and now < start:
                    quest.next_eligible_time = start
                    quest.can_verify = False
                else:
                    quest.can_verify = True
            else:
                last_submission = max(submissions, key=lambda x: x.timestamp, default=None)
                if last_submission:
                    quest.next_eligible_time = last_submission.timestamp + FREQUENCY_DELTA.get(quest.frequency, timedelta(days=1))

                                                                  
    pinned_messages = ShoutBoardMessage.query.filter_by(is_pinned=True, game_id=game.id).order_by(
        ShoutBoardMessage.timestamp.desc()).all()
    unpinned_messages = ShoutBoardMessage.query.filter_by(is_pinned=False, game_id=game.id).order_by(
        ShoutBoardMessage.timestamp.desc()).all()
    activities = pinned_messages + (unpinned_messages + [ut for ut in completed_quests if ut.quest.game_id == game.id])
    activities.sort(key=get_datetime, reverse=True)

                                                                     
    quests = [
        q for q in quests
        if q.from_calendar
        or not (
            (
                q.badge_id is None
                or (q.badge is not None and not q.badge.image)
            )
            and q.total_completions == 0
        )
    ]

    quests.sort(key=lambda x: (-x.is_sponsored, -x.personal_completions, -x.total_completions))
    return quests, activities
  

def _prepare_user_data(game_id, profile):
                                                             
    badges = (
        Badge.query
             .options(joinedload(Badge.quests))                                       
             .join(Quest)
             .filter(
                 Quest.game_id == game_id,
                 Quest.badge_id.isnot(None),
                 Badge.image.isnot(None)
             )
             .distinct()
             .all()
    )

                                                        
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

                                 
    enhanced_badges = []
    for badge in badges:
                                        
        awarding = [q for q in badge.quests if q.game_id == game_id]
        task_names            = ", ".join(q.title for q in awarding)
        task_ids              = ", ".join(str(q.id) for q in awarding)
        badge_awarded_counts  = ", ".join(str(q.badge_awarded) for q in awarding)

                                                                    
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

                                           
    earned = [b for b in enhanced_badges if b['is_complete']]
    unearned = [b for b in enhanced_badges if not b['is_complete']]

    return earned, unearned


def _sort_calendar_quests(quests, now):
    """Return calendar quests sorted with upcoming first and past events last."""
    def aware(dt):
        if dt is None:
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

    upcoming = [q for q in quests if not q.calendar_event_start or aware(q.calendar_event_start) >= now]
    past = [q for q in quests if q.calendar_event_start and aware(q.calendar_event_start) < now]
    sentinel = datetime.max.replace(tzinfo=UTC)
    upcoming.sort(key=lambda q: aware(q.calendar_event_start) or sentinel)
    past.sort(key=lambda q: aware(q.calendar_event_start) or sentinel)
    return upcoming + past


def _calendar_display_date(dt, tz):
    """Return event date converted to the calendar timezone if provided."""
    if dt is None:
        return None
    aware = dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    if tz:
        aware = aware.astimezone(tz)
    return aware.date()


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
    mastodon_form = MastodonLoginForm()

    now = datetime.now(UTC)

    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id

                                                                       
                                                                             
    query_game_id = get_int_param('game_id')
    if query_game_id is not None:
        game_id = query_game_id

                                                      
    show_login       = request.args.get('show_login') == '1'
    show_join_custom = request.args.get('show_join_custom') == '1'
    explicit_game    = bool(request.args.get('game_id'))
    if current_user.is_authenticated\
        and not current_user.participated_games\
        and not explicit_game:
        show_join_custom = True

    if show_join_custom and not current_user.is_authenticated and not show_login:
        return redirect(url_for(
            'auth.login',
            next=request.full_path,
            show_join_custom=1
        ))

                                                                    
    if show_join_custom:
        game = None
        game_id = None
    else:
        game, game_id = _select_game(game_id)

    calendar_tz = None
    if game and game.calendar_url:
        tz_name = _parse_calendar_tz(game.calendar_url)
        if tz_name:
            try:
                calendar_tz = ZoneInfo(tz_name)
            except Exception:
                calendar_tz = None

                                       
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

                             
    profile = None
    user_quests = []
    total_points = None
    if current_user.is_authenticated:
        user_quests = UserQuest.query.filter_by(user_id=current_user.id).all()
        total_points = sum(ut.points_awarded for ut in user_quests if ut.quest.game_id == game_id)
        profile = User.query.get_or_404(user_id)
        if not profile.display_name:
            profile.display_name = profile.username

                                                       
        user_games_list = (
            db.session.query(Game, user_games.c.joined_at)
                        .join(user_games, user_games.c.game_id == Game.id)
                        .filter(user_games.c.user_id == current_user.id)
                        .all()
        )
    else:
        user_games_list = []

                                   
    quests, activities = _prepare_quests(game, user_id, user_quests, now)
    calendar_quests = [q for q in quests if getattr(q, 'from_calendar', False)]
    calendar_quests = _sort_calendar_quests(calendar_quests, now)
    def _is_past_event(q):
        if not q.calendar_event_start:
            return False
        aware = q.calendar_event_start if q.calendar_event_start.tzinfo else q.calendar_event_start.replace(tzinfo=UTC)
        return aware < now

    upcoming_calendar_quests = [q for q in calendar_quests if not _is_past_event(q)]
    past_calendar_quests = [q for q in calendar_quests if _is_past_event(q)]

    for q in upcoming_calendar_quests + past_calendar_quests:
        q.display_date = _calendar_display_date(q.calendar_event_start, calendar_tz)

    quests = [q for q in quests if not getattr(q, 'from_calendar', False)]
    categories = sorted({quest.category for quest in quests if quest.category})

                                            
    open_games = Game.query.filter(
        Game.custom_game_code.isnot(None),
        Game.is_public.is_(True),
        Game.is_demo.is_(False),
        Game.start_date <= now,
        (Game.end_date.is_(None) | (Game.end_date >= now))
    ).all()

    closed_games = Game.query.filter(
        Game.custom_game_code.isnot(None),
        Game.is_public.is_(True),
        Game.is_demo.is_(False),
        Game.end_date < now
    ).all()

                                 
    demo_game = (Game.query
                    .filter(
                        Game.is_demo.is_(True),
                        Game.start_date <= now,
                        (Game.end_date.is_(None) | (Game.end_date >= now))
                    )
                    .order_by(Game.start_date.desc())
                    .first())

                         
    has_joined = (current_user.is_authenticated and game in current_user.participated_games)
    explicit_game = bool(request.args.get('game_id'))
    suppress_custom = request.args.get('show_join_custom') == '0'
    show_join_modal = (
        not has_joined and
        not explicit_game and
        not suppress_custom and
        not show_join_custom
    )

                         
    if current_user.is_authenticated:
        earned_badges, unearned_badges = _prepare_user_data(game_id, profile)
    else:
        earned_badges, unearned_badges = [], []

            
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
        upcoming_calendar_quests=upcoming_calendar_quests,
        past_calendar_quests=past_calendar_quests,
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
        login_form=login_form,
        register_form=register_form,
        forgot_form=forgot_form,
        reset_form=reset_form,
        mastodon_form=mastodon_form,
        calendar_tz=calendar_tz
    )




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

                                       
        from app.models.user import Notification
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


@main_bp.route('/shout-board-messages/<int:game_id>')
@login_required
def shout_board_messages(game_id):
    """
    Return JSON: { pinned: [...], messages: [...], has_next: bool }.
    """
    page     = get_int_param('page', default=1)
    per_page = get_int_param('per_page', default=20)

                                    
    pinned = []
    if page == 1:
        pinned_q = (ShoutBoardMessage.query
                    .filter_by(game_id=game_id, is_pinned=True)
                    .order_by(ShoutBoardMessage.timestamp.desc())
                    .all())
        pinned = [{
            'id': m.id,
            'message': m.message,
            'timestamp': m.timestamp.isoformat(),
            'user': {
              'id': m.user.id,
              'display_name': m.user.display_name or m.user.username
            },
            'is_pinned': True
        } for m in pinned_q]

    paginated = (ShoutBoardMessage.query
                 .filter_by(game_id=game_id, is_pinned=False)
                 .order_by(ShoutBoardMessage.timestamp.desc())
                 .paginate(page=page, per_page=per_page, error_out=False))

    messages = [{
        'id': m.id,
        'message': m.message,
        'timestamp': m.timestamp.isoformat(),
        'user': {
          'id': m.user.id,
          'display_name': m.user.display_name or m.user.username
        },
        'is_pinned': False
    } for m in paginated.items]

    return jsonify({
        'pinned':   pinned,
        'messages': messages,
        'has_next': paginated.has_next
    })



@main_bp.route('/leaderboard_partial')
@login_required
def leaderboard_partial():
    """
    Provide leaderboard data for a specific game.
    """
    selected_game_id = get_int_param('game_id')
    if not selected_game_id:
        return jsonify({'error': 'Missing or invalid game_id'}), 400

    game = Game.query.get(selected_game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    top_users_query = db.session.query(
        User.id,
        User.username,
        User.display_name,
        db.func.sum(UserQuest.points_awarded).label('total_points'),
        db.func.sum(
            db.case((UserQuest.completions > 0, 1), else_=0)
        ).label('completed_quests')
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
        'total_points': total_points,
        'completed_quests': completed_quests
    } for uid, username, display_name, total_points, completed_quests in top_users_query]

    total_game_points = db.session.query(
        db.func.sum(UserQuest.points_awarded)
    ).join(Quest, UserQuest.quest_id == Quest.id
    ).filter(Quest.game_id == selected_game_id
    ).scalar() or 0

    # Use the user_games association to count participants. Older
    # `game_participants` table is no longer updated when users join a game,
    # so relying on `game.participants` returns an incorrect count of zero.
    num_participants = len(game.game_participants)
    num_quests = Quest.query.filter_by(game_id=selected_game_id).count()
    avg_points = round(total_game_points / num_participants, 2) if num_participants else 0
    secondary_stats = [
        {"label": "Participants", "value": num_participants},
        {"label": "Quests Available", "value": num_quests},
        {"label": "Avg Points", "value": avg_points},
    ]

    return jsonify({
        'top_users': top_users,
        'total_game_points': total_game_points,
        'game_goal': game.game_goal if game.game_goal else None,
        'secondary_stats': secondary_stats
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
    quest_submissions = (
        user.quest_submissions.order_by(QuestSubmission.timestamp.desc()).all()
    )
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
                        'category': badge.category, 'image': badge.image} for badge in badges],
            'follower_count': len(user.followers)
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

                                                                  
    response_data['current_user_following'] = (
        current_user.is_authenticated and
        User.query.get(user_id) in current_user.following
    )

    return jsonify(response_data)


def _coerce_to_list(raw: Any) -> List[str]:
    """
    Turn anything—string, list, tuple, JSON literal—into a Python list of strings.
    """
                  
    if isinstance(raw, (list, tuple, set)):
        return list(raw)

                         
    if isinstance(raw, str):
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, list):
                return loaded
        except json.JSONDecodeError:
            pass

                                          
        return [item.strip() for item in raw.split(',') if item.strip()]

                  
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
                                                
        errors = {f: e for f, e in form.errors.items()}
        logger.debug('Form validation failed: %s', errors)
        return jsonify({'error': 'Invalid form submission', 'details': errors}), 400

    try:
                                             
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
        return jsonify({'error': 'Internal server error'}), 500


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
            return jsonify({'error': 'Internal server error'}), 500

    logger.debug('Bike form validation failed.')
    for field, errors in bike_form.errors.items():
        for error in errors:
            logger.debug('Error in the %s field - %s', field, error)
    return jsonify({'error': 'Invalid form submission'}), 400


@main_bp.route('/pin_message/<int:game_id>/<int:message_id>', methods=['POST'])
@login_required
@require_admin
def pin_message(game_id, message_id):
    """
    Toggle the pin status of a shout board message.
    """
    message = ShoutBoardMessage.query.get_or_404(message_id)
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
            enqueue_email(recipient, subject, html)
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
    width_arg  = request.args.get('width')

                                                      
    try:
        width = int(width_arg)
    except (TypeError, ValueError):
        return jsonify({'error': "Invalid request: 'width' must be a positive integer"}), 400

    if not image_path or width <= 0:
        return jsonify({'error': "Invalid request: Missing 'path' or 'width'"}), 400

    try:
                                                                           
                                                                               
                               
        image_path = image_path.lstrip('/')
        if image_path.startswith('static/'):
            image_path = image_path[len('static/'):] 

        full_image_path = os.path.abspath(os.path.join(current_app.static_folder, image_path))
        if not full_image_path.startswith(os.path.abspath(current_app.static_folder)):
            current_app.logger.error("Attempted path traversal detected: %s", image_path)
            return jsonify({'error': 'Invalid file path'}), 400

        if not os.path.exists(full_image_path):
            current_app.logger.error("File not found: %s", full_image_path)
            return jsonify({'error': 'File not found'}), 404

        with Image.open(full_image_path) as img:
            img = correct_image_orientation(img)
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

    except UnidentifiedImageError:
        current_app.logger.error(
            "Unsupported image format encountered: %s", full_image_path
        )
        return jsonify({"error": "Unsupported image format"}), 415
    except Exception as exc:
        current_app.logger.error(
            "Exception occurred during image processing: %s", exc
        )
        return jsonify({"error": "Image processing failed"}), 500


@main_bp.route('/sw.js')
def service_worker():
    """Serve the compiled service worker from ``static/dist``."""
    response = current_app.send_static_file('dist/sw.js')
    response.headers['Content-Type'] = 'application/javascript'
    return response


@main_bp.route('/manifest.json')
def manifest():
    """Serve the PWA manifest with dynamic shortcuts."""
    base_path = os.path.join(current_app.static_folder, 'manifest.json')
    with open(base_path) as f:
        data = json.load(f)

    game_id = get_int_param('game_id')
    if not game_id and current_user.is_authenticated:
        game_id = current_user.selected_game_id

    if game_id:
        quests = (
            Quest.query.filter_by(game_id=game_id, enabled=True)
            .order_by(Quest.id.asc())
            .limit(4)
            .all()
        )
        shortcuts = []
        for q in quests:
            shortcuts.append({
                "name": q.title,
                "short_name": q.title[:12],
                "description": q.description or "",
                "url": url_for('main.index', game_id=game_id) + f"?quest_shortcut={q.id}",
                "icons": [
                    {
                        "src": "/static/icons/icon_96x96.webp",
                        "sizes": "96x96",
                        "type": "image/webp",
                    }
                ],
            })
        if shortcuts:
            data["shortcuts"] = shortcuts

    response = jsonify(data)
    response.headers['Content-Type'] = 'application/json'
    return response


@main_bp.route('/offline.html')
def offline_page():
    """Return the offline fallback page."""
    return current_app.send_static_file('offline.html')


@main_bp.route('/favicon.ico')
def favicon():
    """Serve the site's favicon."""
    return current_app.send_static_file('favicon.ico')


@main_bp.route('/robots.txt')
def robots_txt():
    """Serve the robots.txt file."""
    return send_from_directory(current_app.root_path, 'robots.txt', mimetype='text/plain')


@main_bp.route('/share-target', methods=['POST'])
def share_target_handler():
    """Handle incoming data from the Web Share Target API."""
    file = request.files.get('file')
    text = request.form.get('text')
    title = request.form.get('title')
    if file:
        upload_dir = current_app.config.get('UPLOAD_FOLDER', '/tmp')
        os.makedirs(upload_dir, exist_ok=True)
        filename = secure_filename(file.filename)
        file.save(os.path.join(upload_dir, filename))
    if text or title:
        flash('Shared content received.', 'success')
    return redirect(url_for('main.index'))


@main_bp.route('/.well-known/assetlinks.json')
def assetlinks():
    """Serve digital asset links for TWA validation."""
    fingerprint = current_app.config.get("TWA_SHA256_FINGERPRINT", "")
    data = [
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": "org.questbycycle.app",
                "sha256_cert_fingerprints": [fingerprint],
            },
        }
    ]
    return current_app.response_class(
        response=json.dumps(data),
        mimetype="application/json",
    )


@main_bp.route('/protocol-handler')
def protocol_handler():
    """Handle custom web+questbycycle protocol links."""
    url_param = request.args.get('url', '')
    if url_param.startswith('web+questbycycle:'):
        remainder = url_param.split(':', 1)[1]
        quest_id = None
        if remainder.isdigit():
            quest_id = int(remainder)
        else:
            parsed = urlparse(remainder)
            qid = parse_qs(parsed.query).get('id', [None])[0]
            if qid and qid.isdigit():
                quest_id = int(qid)
        if quest_id:
            return redirect(url_for('quests.quest_details', quest_id=quest_id))
    current_app.logger.warning('Invalid custom protocol URL: %s', url_param)
    return redirect(url_for('main.index'))
