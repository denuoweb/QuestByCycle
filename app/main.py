from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user, login_required, logout_user
from app.utils import save_profile_picture, save_bicycle_picture
from app.models import db, Game, User, Task, Badge, UserTask, TaskSubmission, TaskLike, ShoutBoardMessage, ShoutBoardLike, ProfileWallMessage, user_games
from app.forms import ProfileForm, ShoutBoardForm, ContactForm
from app.utils import send_email, allowed_file, generate_tutorial_game
from .config import load_config
from werkzeug.utils import secure_filename
from sqlalchemy import func
from sqlalchemy.orm import aliased
from datetime import datetime, timedelta, timezone
from pytz import utc
from flask_wtf.csrf import generate_csrf

import bleach
import os
import logging

main_bp = Blueprint('main', __name__)

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

config = load_config()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_datetime(activity):
    if hasattr(activity, 'timestamp') and isinstance(activity.timestamp, datetime):
        return activity.timestamp.replace(tzinfo=None) if activity.timestamp.tzinfo is not None else activity.timestamp
    elif hasattr(activity, 'completed_at') and isinstance(activity.completed_at, datetime):
        return activity.completed_at.replace(tzinfo=None)
    else:
        raise ValueError("Activity object does not contain valid timestamp information.")


@main_bp.route('/', defaults={'game_id': None, 'task_id': None, 'user_id': None})
@main_bp.route('/<int:game_id>', defaults={'task_id': None, 'user_id': None})
@main_bp.route('/<int:game_id>/<int:task_id>', defaults={'user_id': None})
@main_bp.route('/<int:game_id>/<int:task_id>/<int:user_id>')
def index(game_id, task_id, user_id):
    user_games_list = []
    profile = None
    user_tasks = []
    badges = []
    total_points = None

    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id

    if game_id is None and current_user.is_authenticated:
        joined_games = current_user.participated_games
        if joined_games:
            game_id = joined_games[0].id

    game = Game.query.get(game_id) if game_id else None

    # Ensure the user has joined the game before proceeding
    if game_id and current_user.is_authenticated:
        if game not in current_user.participated_games:
            return redirect(url_for('main.index'))

    carousel_images_dir = os.path.join(current_app.root_path, 'static', 'images', current_app.config['CAROUSEL_IMAGES_DIR'])

    if not os.path.exists(carousel_images_dir):
        os.makedirs(carousel_images_dir)

    carousel_images = os.listdir(carousel_images_dir)
    carousel_images = [os.path.join('images', current_app.config['CAROUSEL_IMAGES_DIR'], filename) for filename in carousel_images]

    if current_user.is_authenticated:
        user_tasks = UserTask.query.filter_by(user_id=current_user.id).all()
        total_points = sum(ut.points_awarded for ut in user_tasks if ut.task.game_id == game_id)

    tasks = Task.query.filter_by(game_id=game.id, enabled=True).all() if game else []
    has_joined = game in current_user.participated_games if game else False
    game_participation = {game.id: has_joined} if game else {}

    form = ShoutBoardForm()
    pinned_messages = ShoutBoardMessage.query.filter_by(is_pinned=True, game_id=game_id).order_by(ShoutBoardMessage.timestamp.desc()).all()
    unpinned_messages = ShoutBoardMessage.query.filter_by(is_pinned=False, game_id=game_id).order_by(ShoutBoardMessage.timestamp.desc()).all()
    completed_tasks = UserTask.query.filter(UserTask.completions > 0).order_by(UserTask.completed_at.desc()).all()

    if game:
        pinned_activities = pinned_messages
        unpinned_activities = unpinned_messages + [ut for ut in completed_tasks if ut.task.game_id == game_id]
    else:
        pinned_activities = []
        unpinned_activities = []

    unpinned_activities.sort(key=lambda x: get_datetime(x), reverse=True)
    activities = pinned_activities + unpinned_activities

    selected_task = Task.query.get(task_id) if task_id else None

    if current_user.is_authenticated:
        liked_message_ids = {like.message_id for like in ShoutBoardLike.query.filter_by(user_id=current_user.id)}
        liked_task_ids = {like.task_id for like in TaskLike.query.filter_by(user_id=current_user.id)}
        
        # Fetch games along with joined_at timestamps
        user_games_list = db.session.query(Game, user_games.c.joined_at).join(user_games, user_games.c.game_id == Game.id).filter(user_games.c.user_id == current_user.id).all()
        
        profile = User.query.get_or_404(user_id)
        user_tasks = UserTask.query.filter_by(user_id=profile.id).all()
        badges = [badge for badge in profile.badges if any(task.game_id == game_id for task in badge.tasks)]

        if not profile.display_name:
            profile.display_name = profile.username

    now = datetime.now(utc)
    period_start_map = {
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1),
        'monthly': timedelta(days=30)
    }

    for task in tasks:
        task.total_completions = db.session.query(TaskSubmission).filter(TaskSubmission.task_id == task.id).count()
        task.personal_completions = db.session.query(TaskSubmission).filter(TaskSubmission.task_id == task.id, TaskSubmission.user_id == user_id).count() if user_id else 0
        task.completions_within_period = 0
        task.can_verify = False
        task.last_completion = None
        task.first_completion_in_period = None
        task.next_eligible_time = None
        task.completion_timestamps = []

        if user_id:
            period_start = now - period_start_map.get(task.frequency, timedelta(days=1))
            submissions = TaskSubmission.query.filter(
                TaskSubmission.user_id == user_id,
                TaskSubmission.task_id == task.id,
                TaskSubmission.timestamp >= period_start
            ).all()

            if submissions:
                task.completions_within_period = len(submissions)
                task.first_completion_in_period = min(submissions, key=lambda x: x.timestamp).timestamp
                task.completion_timestamps = [sub.timestamp for sub in submissions]

            relevant_user_tasks = [ut for ut in user_tasks if ut.task_id == task.id]
            task.last_completion = max((ut.completed_at for ut in relevant_user_tasks), default=None)

            if task.personal_completions < task.completion_limit:
                task.can_verify = True
            else:
                last_completion = max(submissions, key=lambda x: x.timestamp, default=None)
                if last_completion:
                    increment_map = {
                        'daily': timedelta(days=1),
                        'weekly': timedelta(weeks=1),
                        'monthly': timedelta(days=30)
                    }
                    task.next_eligible_time = last_completion.timestamp + increment_map.get(task.frequency, timedelta(days=1))

    tasks.sort(key=lambda x: (-x.is_sponsored, -x.personal_completions, -x.total_completions))

    custom_games = Game.query.filter(Game.custom_game_code.isnot(None), Game.is_public.is_(True)).all()

    return render_template('index.html',
                           form=form,
                           games=user_games_list,
                           game=game,
                           user_games=user_games_list,
                           activities=activities,
                           tasks=tasks,
                           game_participation=game_participation,
                           selected_task=selected_task,
                           has_joined=has_joined,
                           profile=profile,
                           user_tasks=user_tasks,
                           badges=badges,
                           carousel_images=carousel_images,
                           total_points=total_points,
                           completions=completed_tasks,
                           custom_games=custom_games,
                           selected_game_id=game_id,
                           selected_game=game)


@main_bp.route('/shout-board/<int:game_id>', methods=['POST'])
@login_required
def shout_board(game_id):
    print(f"Game ID received (initial): {game_id}")  # Debugging line
    
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
    else:
        print("Form Errors:", form.errors)  # Output form errors to the console
        flash('There was an error with your submission.', 'error')
        return redirect(url_for('main.index', game_id=game_id))


@main_bp.route('/like-message/<int:message_id>', methods=['POST'])
@login_required
def like_message(message_id):
    # Retrieve the message by ID
    message = ShoutBoardMessage.query.get_or_404(message_id)
    # Check if the current user already liked this message
    already_liked = ShoutBoardLike.query.filter_by(user_id=current_user.id, message_id=message.id).first() is not None

    if not already_liked:
        # User has not liked this message before, so create a new like
        new_like = ShoutBoardLike(user_id=current_user.id, message_id=message.id)
        db.session.add(new_like)
        db.session.commit()
        success = True
    else:
        # User already liked the message. Optionally, handle "unliking" here
        success = False

    # Fetch the new like count for the message
    new_like_count = db.session.query(ShoutBoardLike).filter_by(message_id=message_id).count()
    return jsonify(success=success, new_like_count=new_like_count, already_liked=already_liked)


@main_bp.route('/leaderboard_partial')
@login_required
def leaderboard_partial():
    selected_game_id = request.args.get('game_id', type=int)

    if selected_game_id:
        game = Game.query.get(selected_game_id)
        if not game:
            return jsonify({'error': 'Game not found'}), 404

        top_users_query = db.session.query(
            User.id,
            User.username,
            User.display_name,
            db.func.sum(UserTask.points_awarded).label('total_points')
        ).join(UserTask, UserTask.user_id == User.id
        ).join(Task, Task.id == UserTask.task_id
        ).filter(Task.game_id == selected_game_id
        ).group_by(User.id, User.username, User.display_name
        ).order_by(db.func.sum(UserTask.points_awarded).desc()
        ).all()

        top_users = [{
            'user_id': user_id,
            'username': username,
            'display_name': display_name,
            'total_points': total_points
        } for user_id, username, display_name, total_points in top_users_query]

        total_game_points = db.session.query(
            db.func.sum(UserTask.points_awarded)
        ).join(Task, UserTask.task_id == Task.id
        ).filter(Task.game_id == selected_game_id
        ).scalar() or 0

        return jsonify({
            'top_users': top_users,
            'total_game_points': total_game_points,
            'game_goal': game.game_goal if game.game_goal else None
        })


@main_bp.route('/profile/<int:user_id>')
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    user_tasks = UserTask.query.filter(UserTask.user_id == user.id, UserTask.completions > 0).all()
    badges = user.badges
    participated_games = user.participated_games
    task_submissions = user.task_submissions
    profile_messages = ProfileWallMessage.query.filter_by(user_id=user_id).order_by(ProfileWallMessage.timestamp.desc()).all()

    # Define riding preferences choices here
    riding_preferences_choices = [
        ('new_novice', 'New and novice rider'),
        ('middle_school', 'Middle school rider'),
        ('high_school', 'High school rider'),
        ('college', 'College student rider'),
        ('families', 'Families who ride with their children'),
        ('grandparents', 'Grandparents who ride with their grandchildren'),
        ('seasoned', 'Seasoned riders who ride all over town for their transportation needs'),
        ('adaptive', 'Adaptive bike users'),
        ('occasional', 'Occasional rider'),
        ('ebike', 'E-bike rider'),
        ('long_distance', 'Long distance rider'),
        ('no_car', 'Don’t own a car'),
        ('commute', 'Commute'),
        ('seasonal', 'Seasonal riders: I don’t like riding in inclement weather')
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
            'riding_preferences': user.riding_preferences or [],  # Ensure this is a list
            'ride_description': user.ride_description,
            'bike_picture': user.bike_picture,
            'bike_description': user.bike_description,
            'upload_to_socials': user.upload_to_socials,
            'show_carbon_game': user.show_carbon_game,
            'badges': [{'id': badge.id, 'name': badge.name, 'description': badge.description, 'category': badge.category, 'image': badge.image} for badge in badges]
        },
        'user_tasks': [
            {'id': task.id, 'completions': task.completions}
            for task in user_tasks
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
            }
            for message in profile_messages
        ],
        'participated_games': [
            {'id': game.id, 'title': game.title, 'description': game.description, 'start_date': game.start_date.strftime('%B %d, %Y'), 'end_date': game.end_date.strftime('%B %d, %Y')}
            for game in participated_games
        ],
        'task_submissions': [
            {'id': submission.id, 'task': {'title': submission.task.title}, 'comment': submission.comment, 'timestamp': submission.timestamp.strftime('%B %d, %Y %H:%M'), 'image_url': submission.image_url, 'twitter_url': submission.twitter_url, 'fb_url': submission.fb_url, 'instagram_url': submission.instagram_url}
            for submission in task_submissions
        ],
        'riding_preferences_choices': riding_preferences_choices  # Use centralized preferences
    }

    return jsonify(response_data)


@main_bp.route('/profile/<int:user_id>/edit', methods=['POST'])
@login_required
def edit_profile(user_id):
    if user_id != current_user.id:
        print(f'Unauthorized access attempt by user {current_user.id}')
        return jsonify({'error': 'Unauthorized access'}), 403

    form = ProfileForm(request.form)  # Initialize form with request data

    user = User.query.get_or_404(user_id)

    if form.validate_on_submit():
        print('Form validated successfully.')

        try:
            # Handle profile picture upload
            if form.profile_picture.data:
                user.profile_picture = save_profile_picture(form.profile_picture.data, user.profile_picture)

            # Handle bicycle picture upload
            if 'bike_picture' in request.files:
                bike_picture_file = request.files['bike_picture']
                if bike_picture_file and allowed_file(bike_picture_file.filename):
                    bike_filename = save_bicycle_picture(bike_picture_file, user.bike_picture)
                    user.bike_picture = bike_filename

            # Update other fields
            if form.display_name.data:
                user.display_name = form.display_name.data

            if form.interests.data:
                user.interests = form.interests.data

            # Update riding preferences
            user.riding_preferences = request.form.getlist('riding_preferences')

            if form.ride_description.data:
                user.ride_description = form.ride_description.data

            if form.bike_description.data:
                user.bike_description = form.bike_description.data

            if form.upload_to_socials.data is not None:
                user.upload_to_socials = form.upload_to_socials.data

            if form.show_carbon_game.data is not None:
                user.show_carbon_game = form.show_carbon_game.data

            db.session.commit()
            print('Profile updated successfully in the database.')
            return jsonify({'success': True})

        except Exception as e:
            db.session.rollback()
            print(f'Exception occurred: {str(e)}')
            return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500

    # Debug: Log form validation errors
    print('Form validation failed.')
    for field, errors in form.errors.items():
        for error in errors:
            print(f'Error in the {field} field - {error}')

    return jsonify({'error': 'Invalid form submission'}), 400



@main_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file:
            old_filename = current_user.profile_picture
            current_user.profile_picture = save_profile_picture(file, old_filename)
    
    current_user.display_name = sanitize_html(request.form.get('display_name', current_user.display_name))
    current_user.age_group = sanitize_html(request.form.get('age_group', current_user.age_group))
    current_user.interests = sanitize_html(request.form.get('interests', current_user.interests))

    # Update new fields
    current_user.riding_preferences = request.form.getlist('riding_preferences')
    current_user.ride_description = sanitize_html(request.form.get('ride_description', current_user.ride_description))
    current_user.bike_description = sanitize_html(request.form.get('bike_description', current_user.bike_description))
    current_user.upload_to_socials = 'upload_to_socials' in request.form
    current_user.show_carbon_game = 'show_carbon_game' in request.form

    if 'bike_picture' in request.files:
        bike_picture_file = request.files['bike_picture']
        if bike_picture_file and allowed_file(bike_picture_file.filename):
            bike_filename = save_profile_picture(bike_picture_file)  # Assuming you have a separate method for saving bike images
            current_user.bike_picture = bike_filename

    db.session.commit()
    return jsonify(success=True)


@main_bp.route('/like_task/<int:task_id>', methods=['POST'])
@login_required
def like_task(task_id):
    task = Task.query.get_or_404(task_id)
    # Check if the current user already liked this task
    already_liked = TaskLike.query.filter_by(user_id=current_user.id, task_id=task.id).first() is not None

    if not already_liked:
        # User has not liked this task before, so create a new like
        new_like = TaskLike(user_id=current_user.id, task_id=task.id)
        db.session.add(new_like)
        db.session.commit()
        success = True
    else:
        # User already liked the task. Optionally, handle "unliking" here
        success = False

    # Fetch the new like count for the task
    new_like_count = TaskLike.query.filter_by(task_id=task.id).count()
    return jsonify(success=success, new_like_count=new_like_count, already_liked=already_liked)


@main_bp.route('/pin_message/<int:game_id>/<int:message_id>', methods=['POST'])
@login_required
def pin_message(game_id, message_id):
    message = ShoutBoardMessage.query.get_or_404(message_id)
    if not current_user.is_admin:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('main.index'))
    
    message.is_pinned = not message.is_pinned  # Toggle the pin status
    db.session.commit()
    flash('Message pin status updated.', 'success')
    return redirect(url_for('main.index', game_id=game_id))


@main_bp.route('/contact', methods=['POST'])
@login_required
def contact():    
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
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=False, message="Failed to send your message"), 500
            flash('Failed to send your message. Please try again later.', 'error')
            current_app.logger.error(f'Failed to send contact form message: {e}')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, message="Validation failed"), 400
        flash('Validation failed. Please ensure all fields are filled correctly.', 'warning')

    return redirect(url_for('main.index'))


@main_bp.route('/refresh-csrf', methods=['GET'])
def refresh_csrf():
    new_csrf_token = generate_csrf()
    response = jsonify({'csrf_token': new_csrf_token})
    response.set_cookie('csrf_token', new_csrf_token)
    return response