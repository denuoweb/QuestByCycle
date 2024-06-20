from flask import Blueprint, make_response, jsonify, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.utils import update_user_score, getLastRelevantCompletionTime, check_and_award_badges, check_and_revoke_badges, save_badge_image, save_submission_image, can_complete_task
from app.forms import TaskForm, PhotoForm
from app.social import post_to_twitter, upload_media_to_twitter, post_to_facebook_with_image, get_long_lived_user_access_token, upload_image_to_facebook, get_facebook_page_access_token, get_facebook_user_access_token, post_photo_to_instagram
from .models import db, Game, Task, Badge, UserTask, TaskSubmission
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from datetime import datetime, timezone, timedelta
from io import BytesIO

import base64
import csv
import os
import qrcode
import bleach

tasks_bp = Blueprint('tasks', __name__, template_folder='templates')

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


@tasks_bp.route('/<int:game_id>/manage_tasks', methods=['GET'])
@login_required
def manage_game_tasks(game_id):
    game = Game.query.get_or_404(game_id)

    if not current_user.is_admin:
        flash('Access denied: Only administrators can manage tasks.', 'danger')
        return redirect(url_for('main.index', game_id=game_id))
    
    form = TaskForm()
    tasks = Task.query.filter_by(game_id=game_id).all()
    return render_template('manage_tasks.html', game=game, tasks=tasks, form=form, game_id=game_id)


@tasks_bp.route('/game/<int:game_id>/add_task', methods=['GET', 'POST'])
@login_required
def add_task(game_id):
    form = TaskForm()
    form.game_id.data = game_id  # Set the game_id field in the form

    if form.validate_on_submit():
        badge_id = form.badge_id.data if form.badge_id.data and form.badge_id.data != '0' else None

        if not badge_id and form.badge_name.data:
            badge_image_file = None
            if 'badge_image_filename' in request.files:
                badge_image_file = request.files['badge_image_filename']
                if badge_image_file and badge_image_file.filename != '':
                    badge_image_file = save_badge_image(badge_image_file)
                else:
                    flash('No badge image selected for upload.', 'error')

            new_badge = Badge(
                name=sanitize_html(form.badge_name.data),
                description=sanitize_html(form.badge_description.data),
                image=badge_image_file
            )
            db.session.add(new_badge)
            db.session.flush()
            badge_id = new_badge.id

        new_task = Task(
            title=sanitize_html(form.title.data),
            description=sanitize_html(form.description.data),
            tips=sanitize_html(form.tips.data),
            points=form.points.data,
            game_id=game_id,
            completion_limit=form.completion_limit.data,
            frequency=sanitize_html(form.frequency.data),
            enabled=form.enabled.data,
            is_sponsored=form.is_sponsored.data,
            category=sanitize_html(form.category.data),
            verification_type=sanitize_html(form.verification_type.data),
            badge_id=badge_id
        )
        db.session.add(new_task)
        try:
            db.session.commit()
            flash('Task added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {e}', 'error')

        return redirect(url_for('tasks.manage_game_tasks', game_id=game_id))

    return render_template('add_task.html', form=form, game_id=game_id)


@tasks_bp.route('/task/<int:task_id>/submit', methods=['POST'])
@login_required
def submit_task(task_id):
    task = Task.query.get_or_404(task_id)
    game = Game.query.get_or_404(task.game_id)
    now = datetime.now()
    game_start = game.start_date
    game_end = game.end_date
    user_task = UserTask.query.filter_by(user_id=current_user.id, task_id=task_id).first()
    tweet_url = None
    fb_url = None

    if not (game_start <= now <= game_end):
        print(f"Task submission failed: Current date {now} is outside game dates {game_start} to {game_end}")
        return jsonify({'success': False, 'message': 'This task cannot be completed outside of the game dates'}), 403

    verification_type = task.verification_type
    image_file = request.files.get('image')
    comment = sanitize_html(request.form.get('verificationComment', ''))

    print(f"Task verification type: {verification_type}")
    print(f"Image file: {image_file}")
    print(f"Verification comment: {comment}")

    if verification_type == 'qr_code':
        print("QR Code verification does not require any submission")
        return jsonify({'success': True, 'message': 'QR Code verification does not require any submission'}), 200
    if verification_type == 'photo' and (not image_file or image_file.filename == ''):
        print("No file selected for photo verification")
        return jsonify({'success': False, 'message': 'No file selected for photo verification'}), 400
    if verification_type == 'comment' and not comment:
        print("Comment required for verification")
        return jsonify({'success': False, 'message': 'Comment required for verification'}), 400
    if verification_type == 'photo_comment' and (not image_file or image_file.filename == ''):
        print("Both photo and comment are required for verification")
        return jsonify({'success': False, 'message': 'Both photo and comment are required for verification'}), 400
    if task.verification_type == 'Pause':
        print("This task is currently paused")
        return jsonify({'success': False, 'message': 'This task is currently paused'}), 403

    try:
        image_url = None
        tweet_url = None
        fb_url = None

        if image_file and image_file.filename:
            print("Saving submission image")
            image_url = save_submission_image(image_file)
            image_path = os.path.join(current_app.static_folder, image_url)
            print(f"Image URL: {image_url}")
            print(f"Image Path: {image_path}")
        
        display_name = current_user.display_name or current_user.username
        status = f"{display_name} completed '{task.title}'! #QuestByCycle"
        print(f"Status: {status}")
        
        if image_url is not None:
            print("Uploading media to Twitter")
            media_id, error = upload_media_to_twitter(image_path, game.twitter_api_key, game.twitter_api_secret, game.twitter_access_token, game.twitter_access_token_secret)
            if not error:
                print("Posting tweet")
                tweet_url, error = post_to_twitter(status, media_id, game.twitter_username, game.twitter_api_key, game.twitter_api_secret, game.twitter_access_token, game.twitter_access_token_secret)
                if error:
                    print(f"Failed to post tweet: {error}")
                else:
                    print(f"Tweet URL: {tweet_url}")
            else:
                print(f"Failed to upload media to Twitter: {error}")

            print(f"Using Facebook Access Token: {game.facebook_access_token}")
            page_access_token = get_facebook_page_access_token(game.facebook_access_token, game.facebook_page_id)
            print(f"Using Facebook Page Access Token: {page_access_token}")
            media_response = upload_image_to_facebook(game.facebook_page_id, image_path, page_access_token)
            if media_response and 'id' in media_response:
                image_id = media_response['id']
                print(f"Image ID from Facebook: {image_id}")
                fb_url, error = post_to_facebook_with_image(game.facebook_page_id, status, image_id, page_access_token)
                if error:
                    print(f"Failed to post image to Facebook: {error}")
                else:
                    print(f"Facebook URL: {fb_url}")
            else:
                print(f"Failed to upload image to Facebook: {media_response}")

        new_submission = TaskSubmission(
            task_id=task_id,
            user_id=current_user.id,
            image_url=url_for('static', filename=image_url) if image_url else url_for('static', filename='images/commentPlaceholder.png'),
            comment=comment,
            twitter_url=tweet_url,
            fb_url=fb_url,
            timestamp=datetime.now(),
        )
        print(f"Creating new task submission: {new_submission}")
        db.session.add(new_submission)

        # Explicitly print all attributes of the new_submission
        print(f"TaskSubmission Details: ID: {new_submission.id}, Task ID: {new_submission.task_id}, User ID: {new_submission.user_id}, "
              f"Image URL: {new_submission.image_url}, Comment: {new_submission.comment}, Timestamp: {new_submission.timestamp}, "
              f"Twitter URL: {new_submission.twitter_url}, Facebook URL: {new_submission.fb_url}")

        if not user_task:
            print(f"No existing UserTask entry, creating new for task ID: {task_id}")

            user_task = UserTask(
                user_id=current_user.id,
                task_id=task_id,
                completions=0,
                points_awarded=0,
                completed_at=datetime.now()
            )
            db.session.add(user_task)

        if user_task.completions is None:
            user_task.completions = 0
        if user_task.points_awarded is None:
            user_task.points_awarded = 0

        user_task.completions += 1
        user_task.points_awarded += task.points
        user_task.completed = True

        print(f"UserTask after update: {user_task}")

        db.session.commit()

        update_user_score(current_user.id)
        check_and_award_badges(user_id=current_user.id, task_id=task_id)

        total_points = sum(ut.points_awarded for ut in UserTask.query.filter_by(user_id=current_user.id))
        print(f"Total points for user {current_user.id}: {total_points}")

        return jsonify({
            'success': True,
            'new_completion_count': user_task.completions,
            'total_points': total_points,
            'image_url': image_url,
            'comment': comment,
            'tweet_url': tweet_url,
            'fb_url': fb_url
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error during task submission: {e}")
        return jsonify({'success': False, 'message': str(e)})


    

@tasks_bp.route('/task/<int:task_id>/update', methods=['POST'])
@login_required
def update_task(task_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    task = Task.query.get_or_404(task_id)
    data = request.get_json()

    task.title = sanitize_html(data.get('title', task.title))
    task.description = sanitize_html(data.get('description', task.description))
    task.tips = sanitize_html(data.get('tips', task.tips))
    task.points = data.get('points', task.points)
    task.completion_limit = data.get('completion_limit', task.completion_limit)
    task.enabled = data.get('enabled', task.enabled)
    task.is_sponsored = data.get('is_sponsored', task.is_sponsored)
    task.category = sanitize_html(data.get('category', task.category))
    task.verification_type = sanitize_html(data.get('verification_type', task.verification_type))
    task.frequency = sanitize_html(data.get('frequency', task.frequency))

    badge_id = data.get('badge_id')
    if badge_id is not None:
        try:
            task.badge_id = int(badge_id)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid badge ID'}), 400

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Task updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    

@tasks_bp.route('/task/<int:task_id>/delete', methods=['DELETE'])
@login_required
def delete_task(task_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    # Fetch the task to be deleted
    task_to_delete = Task.query.get_or_404(task_id)
    
    # Deleting the task. The cascade options in the relationship should handle deletion of related records.
    db.session.delete(task_to_delete)

    try:
        db.session.commit()
        return jsonify({'success': True, 'message': 'Task deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Failed to delete task {task_id}: {e}')
        return jsonify({'success': False, 'message': 'Failed to delete task'})


@tasks_bp.route('/game/<int:game_id>/tasks', methods=['GET'])
def get_tasks_for_game(game_id):
    tasks = Task.query.filter_by(game_id=game_id).all()
    tasks_data = [
        {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'tips': task.tips,
            'points': task.points,
            'completion_limit': task.completion_limit,
            'enabled': task.enabled,
            'is_sponsored': task.is_sponsored,
            'verification_type': task.verification_type,
            'badge_name': task.badge.name if task.badge else 'None',
            'badge_description': task.badge.description if task.badge else '',
            'frequency': task.frequency,  # Handling Frequency Enum
            'category': task.category if task.category else 'Not Set',  # Handling potentially undefined Category
        }
        for task in tasks
    ]
    return jsonify(tasks=tasks_data)

@tasks_bp.route('/game/<int:game_id>/import_tasks', methods=['POST'])
@login_required
def import_tasks(game_id):
    if 'tasks_csv' not in request.files:
        return jsonify(success=False, message="No file part"), 400
    
    file = request.files['tasks_csv']
    if file.filename == '':
        return jsonify(success=False, message="No selected file"), 400
    
    if file:
        upload_dir = current_app.config['TASKCSV']
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, secure_filename(file.filename))
        file.save(filepath)

        imported_badges = []
        with open(filepath, mode='r', encoding='utf-8') as csv_file:
            tasks_data = csv.DictReader(csv_file)
            for task_info in tasks_data:
                badge = Badge.query.filter_by(name=sanitize_html(task_info['badge_name'])).first()
                if not badge:
                    badge = Badge(
                        name=sanitize_html(task_info['badge_name']),
                        description=sanitize_html(task_info['badge_description']),
                    )
                    db.session.add(badge)
                    db.session.flush()
                    imported_badges.append(badge.id)

                new_task = Task(
                    category=sanitize_html(task_info['category']),
                    title=sanitize_html(task_info['title']),
                    description=sanitize_html(task_info['description']),
                    tips=sanitize_html(task_info['tips']),
                    points=task_info['points'].replace(',', ''),
                    completion_limit=task_info['completion_limit'],
                    frequency=sanitize_html(task_info['frequency']),
                    verification_type=sanitize_html(task_info['verification_type']),
                    badge_id=badge.id,
                    game_id=game_id
                )
                db.session.add(new_task)
            
            db.session.commit()
            os.remove(filepath)
        
        return jsonify(success=True, redirectUrl=url_for('tasks.manage_game_tasks', game_id=game_id))

    return jsonify(success=False, message="Invalid file"), 400


@tasks_bp.route('/task/<int:task_id>/submissions')
def get_task_submissions(task_id):
    submissions = TaskSubmission.query.filter_by(task_id=task_id).all()
    submissions_data = [{
        'id': sub.id,
        'image_url': sub.image_url,
        'comment': sub.comment,
        'timestamp': sub.timestamp.strftime('%Y-%m-%d %H:%M'),
        'user_id': sub.user_id,
        'twitter_url': sub.twitter_url,
        'fb_url': sub.fb_url
    } for sub in submissions]
    return jsonify(submissions_data)


@tasks_bp.route('/detail/<int:task_id>/user_completion')
@login_required
def task_user_completion(task_id):
    task = Task.query.get_or_404(task_id)
    badge = Badge.query.get(task.badge_id) if task.badge_id else None
    user_task = UserTask.query.filter_by(user_id=current_user.id, task_id=task_id).first()
    can_verify, next_eligible_time = can_complete_task(current_user.id, task_id)
    last_relevant_completion_time = getLastRelevantCompletionTime(current_user.id, task_id)

    badge_info = {
        'id': badge.id,
        'name': badge.name,
        'description': badge.description,
        'image': badge.image
    } if badge else {'name': 'Default', 'image': 'default_badge.png'}

    task_details = {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'tips': task.tips,
        'points': task.points,
        'completion_limit': task.completion_limit,
        'category': task.category,
        'frequency': task.frequency, 
        'enabled': task.enabled,
        'is_sponsored': task.is_sponsored,
        'verification_type': task.verification_type,
        'badge': badge_info,
        'nextEligibleTime': next_eligible_time.isoformat() if next_eligible_time else None
    }

    user_completion_data = {
        'completions': user_task.completions if user_task else 0,
        'lastCompletionTimestamp': user_task.completed_at.isoformat() if user_task and user_task.completed_at else None
    }

    response_data = {
        'task': task_details,
        'userCompletion': user_completion_data,
        'canVerify': can_verify,
        'nextEligibleTime': next_eligible_time.isoformat() if next_eligible_time else None,
        'lastRelevantCompletionTime': last_relevant_completion_time.isoformat() if last_relevant_completion_time else None
    }

    return jsonify(response_data)


@tasks_bp.route('/get_last_relevant_completion_time/<int:task_id>/<int:user_id>')
@login_required
def get_last_relevant_completion_time(task_id, user_id):
    last_time = getLastRelevantCompletionTime(user_id, task_id)
    if last_time:
        return jsonify(success=True, lastRelevantCompletionTime=last_time.isoformat())
    else:
        return jsonify(success=False, message="No relevant completion found")


@tasks_bp.route('/generate_qr/<int:task_id>')
def generate_qr(task_id):
    task = Task.query.get_or_404(task_id)
    url = url_for('tasks.submit_photo', task_id=task_id, _external=True)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="white", back_color="black")
    img_buffer = BytesIO()
    img.save(img_buffer, format="PNG")
    img_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>QR Code - {task.title}</title>
        <style>
            body {{ text-align: center; padding: 20px; font-family: Arial, sans-serif; }}
            .qrcodeHeader img {{ max-width: 100%; height: auto; }}
            h1, h2 {{ margin: 10px 0; }}
            img {{ margin-top: 20px; }}
            @media print {{
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="qrcodeHeader">
            <img src="{url_for('static', filename='images/welcomeQuestByCycle.png')}" alt="Welcome">
        </div>
        <h1>Congratulations! You made it!</h1>
        <h2>Scan to complete '{task.title}' and gain {task.points} points!</h2>
        <img src="data:image/png;base64,{img_data}" alt="QR Code">
        <br>
        <button class="no-print" onclick="window.print();">Print this page</button>
    </body>
    </html>
    """

    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html'
    return response


@tasks_bp.route('/submit_photo/<int:task_id>', methods=['GET', 'POST'])
@login_required
def submit_photo(task_id):
    form = PhotoForm()
    task = Task.query.get_or_404(task_id)
    game = Game.query.get_or_404(task.game_id)
    game_start = game.start_date
    game_end = game.end_date
    now = datetime.now()

    if not (game_start <= now <= game_end):
        return jsonify({'success': False, 'message': 'This task cannot be completed outside of the game dates'}), 403

    if request.method == 'POST':
        photo = request.files.get('photo')
        if photo:
            image_url = save_submission_image(photo)
            image_path = os.path.join(current_app.static_folder, image_url)
            status = f"Check out this task completion for '{task.title}'! #QuestByCycle"

            tweet_url = None
            fb_url = None

            if image_url:
                if game.twitter_api_key and game.twitter_api_secret and game.twitter_access_token and game.twitter_access_token_secret:
                    media_id, error = upload_media_to_twitter(image_path, game.twitter_api_key, game.twitter_api_secret, game.twitter_access_token, game.twitter_access_token_secret)
                    if not error:
                        tweet_url, error = post_to_twitter(status, media_id, game.twitter_username, game.twitter_api_key, game.twitter_api_secret, game.twitter_access_token, game.twitter_access_token_secret)
                        if error:
                            print(f"Failed to post tweet: {error}")

                if game.facebook_access_token and game.facebook_page_id:
                    page_access_token = get_facebook_page_access_token(game.facebook_access_token, game.facebook_page_id)
                    media_response = upload_image_to_facebook(game.facebook_page_id, image_path, page_access_token)
                    if media_response and 'id' in media_response:
                        image_id = media_response['id']
                        fb_url, error = post_to_facebook_with_image(game.facebook_page_id, status, image_id, page_access_token)
                        if error:
                            print(f"Failed to post image to Facebook: {error}")

            new_submission = TaskSubmission(
                task_id=task_id,
                user_id=current_user.id,
                image_url=url_for('static', filename=image_url) if image_url else url_for('static', filename='images/commentPlaceholder.png'),
                twitter_url=tweet_url,
                fb_url=fb_url,
                timestamp=datetime.now(),
            )
            db.session.add(new_submission)

            user_task = UserTask.query.filter_by(user_id=current_user.id, task_id=task_id).first()
            if not user_task:
                user_task = UserTask(
                    user_id=current_user.id,
                    task_id=task_id,
                    completions=1,
                    points_awarded=task.points
                )
                db.session.add(user_task)
            else:
                user_task.completions += 1
                user_task.points_awarded += task.points

            db.session.commit()

            update_user_score(current_user.id)

            flash('Photo submitted successfully!', 'success')
            return redirect(url_for('main.index', game_id=task.game_id))
        else:
            flash('No photo detected, please try again.', 'error')

    return render_template('submit_photo.html', form=form, task=task)


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@tasks_bp.errorhandler(RequestEntityTooLarge)
def handle_large_file_error(e):
    return "File too large", 413


@tasks_bp.route('/task/my_submissions', methods=['GET'])
def get_user_submissions():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        submissions = TaskSubmission.query.filter_by(user_id=current_user.id).all()
        submissions_data = [{
            'id': submission.id,
            'image_url': submission.image_url,
            'comment': submission.comment,
            'user_id': submission.user_id,
            'task_id': submission.task_id,
            'twitter_url': submission.twitter_url,  # Assume twitter_url is an attribute
            'timestamp': submission.timestamp.isoformat()  # Adjusted to string format for JSON serialization
        } for submission in submissions]
        return jsonify(submissions_data)
    except Exception as e:
        print(f"Error fetching submissions: {e}")
        return jsonify({'error': 'Failed to fetch submissions'}), 500
    

@tasks_bp.route('/task/delete_submission/<int:submission_id>', methods=['DELETE'])
@login_required
def delete_submission(submission_id):
    submission = TaskSubmission.query.get(submission_id)

    # Check if the current user is the admin or the user who created the submission.
    if not current_user.is_admin:
        if not submission.user_id == current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

    if not submission:
        return jsonify({'error': 'Submission not found'}), 404

    # Find the UserTask entry
    user_task = UserTask.query.filter_by(user_id=submission.user_id, task_id=submission.task_id).first()

    if user_task:
        # Decrement completions and update points
        user_task.completions = max(user_task.completions - 1, 0)  # Ensure it doesn't go negative
        if user_task.completions == 0:
            user_task.points_awarded = 0
        else:
            task = Task.query.get(submission.task_id)
            user_task.points_awarded = max(user_task.points_awarded - task.points, 0)  # Adjust the points accordingly

        # Check if badges need to be revoked
        check_and_revoke_badges(submission.user_id)

        # Commit UserTask changes
        db.session.commit()

    # Now remove the submission
    db.session.delete(submission)
    db.session.commit()
    return jsonify({'success': True})


@tasks_bp.route('/task/all_submissions')
@login_required
def all_submissions():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 403

    submissions = TaskSubmission.query.all()
    submissions_data = [
        {
            'id': submission.id,
            'user_id': submission.user_id,
            'task_id': submission.task_id,
            'image_url': submission.image_url,
            'comment': submission.comment,
            'twitter_url': submission.twitter_url,
            'timestamp': submission.timestamp.isoformat()  # Adjusted to string format for JSON serialization
        } for submission in submissions
    ]
    return jsonify({
        'submissions': submissions_data,
        'is_admin': current_user.is_admin
    })


@tasks_bp.route('/task/<int:task_id>')
@login_required
def task_details(task_id):
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 403

    task = Task.query.get_or_404(task_id)
    task_data = {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'due_date': task.due_date.isoformat(),
        'status': task.status
    }
    return jsonify({'task': task_data})