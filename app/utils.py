from flask import flash, current_app, jsonify, request
from .models import db, Task, Badge, Game, UserTask, User, ShoutBoardMessage, TaskSubmission, UserIP
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from PIL import Image
from pytz import utc
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

import uuid
import os
import csv
import bleach
import json
import base64
import smtplib

SCOPES = ['https://mail.google.com/']

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


MAX_POINTS_INT = 2**63 - 1
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_leaderboard_image(image_file):
    if not hasattr(image_file, 'filename'):
        raise ValueError("Invalid file object passed.")
    
    try:
        ext = image_file.filename.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError("File extension not allowed.")
        filename = secure_filename(f"{uuid.uuid4()}.{ext}")
        rel_path = os.path.join('images', 'leaderboard', filename)
        abs_path = os.path.join(current_app.root_path, 'static', rel_path)

        leaderboard_images_dir = os.path.join(current_app.root_path, 'static/images/leaderboard')
        if not os.path.exists(leaderboard_images_dir):
            os.makedirs(leaderboard_images_dir)

        print(f"Saving file to {abs_path}")
        image_file.save(abs_path)
        print(f"File saved successfully to {abs_path}")
        return rel_path

    except Exception as e:
        print(f"Error saving leaderboard image: {e}")
        raise ValueError(f"Failed to save image: {str(e)}")

def create_smog_effect(image, smog_level):
    smog_overlay = Image.new('RGBA', image.size, (169, 169, 169, int(255 * smog_level)))
    smog_image = Image.alpha_composite(image.convert('RGBA'), smog_overlay)
    return smog_image

def generate_smoggy_images(image_path, game_id):
    try:
        original_image = Image.open(image_path)

        for i in range(10):
            smog_level = i / 9.0
            smoggy_image = create_smog_effect(original_image, smog_level)
            smoggy_image.save(os.path.join(current_app.root_path, f'static/images/leaderboard/smoggy_skyline_{game_id}_{i}.png'))
            print(f"Smoggy image saved: smoggy_skyline_{game_id}_{i}.png")
    except Exception as e:
        print(f"Error generating smoggy images: {e}")
        raise ValueError(f"Failed to generate smoggy images: {str(e)}")

def update_user_score(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            print(f"No user found with ID {user_id}")
            return False

        # Calculate the total points awarded to the user
        total_points = sum(task.points_awarded for task in user.user_tasks if task.points_awarded is not None)

        # Update user score, ensuring it doesn't exceed a predefined maximum
        user.score = min(total_points, MAX_POINTS_INT)

        # Commit changes to the database
        db.session.commit()
        print(f"Updated user score for user ID {user_id} to {user.score}")
        return True
    except Exception as e:
        db.session.rollback()  # Rollback in case of any exception
        print(f"Failed to update score for user ID {user_id}: {e}")
        return False




def award_task_badge(user_id, task_id):
    user_task = UserTask.query.filter_by(user_id=user_id, task_id=task_id).first()
    if user_task and user_task.completions >= user_task.task.completion_limit:
        if user_task.task.badge and user_task.task.badge not in user_task.user.badges:
            user_task.user.badges.append(user_task.task.badge)
            db.session.commit()
            flash(f"Badge '{user_task.task.badge.name}' awarded for completing task '{user_task.task.title}' the required number of times.", 'success')


def award_category_badge(user_id):
    user = User.query.get(user_id)
    completed_categories = {ut.task.category for ut in user.user_tasks if ut.completions >= ut.task.completion_limit}
    
    for category in completed_categories:
        category_badges = Badge.query.filter_by(category=category).all()
        category_tasks = Task.query.filter_by(category=category).all()
        completed_tasks = {ut.task for ut in user.user_tasks if ut.completions >= ut.task.completion_limit and ut.task.category == category}
        
        for badge in category_badges:
            if badge not in user.badges and set(category_tasks) == completed_tasks:
                user.badges.append(badge)
                db.session.commit()
                flash(f"Badge '{badge.name}' awarded for completing all tasks in the '{category}' category.", 'success')


def revoke_badge(user_id):
    user = User.query.get(user_id)
    completed_tasks = UserTask.query.filter_by(user_id=user_id, completions=0).all()

    try:
        for user_task in completed_tasks:

            task = Task.query.get(user_task.task_id)
            if task.badge and task.badge in user.badges:
                user.badges.remove(task.badge)
                db.session.commit()
                flash(f"Badge '{task.badge.name}' revoked as the task '{task.title}' is no longer completed.", 'info')
    except Exception as e:
        db.session.rollback()  # Rollback in case of any exception
        print(f"Failed to revoke badge for user ID {user_id}: {e}")
        return False


def save_profile_picture(profile_picture_file, old_filename=None):
    if old_filename:
        old_path = os.path.join(current_app.root_path, 'static', old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)  # Remove the old file

    ext = profile_picture_file.filename.rsplit('.', 1)[-1]
    filename = secure_filename(f"{uuid.uuid4()}.{ext}")
    uploads_path = os.path.join(current_app.root_path, 'static', current_app.config['main']['UPLOAD_FOLDER'])
    if not os.path.exists(uploads_path):
        os.makedirs(uploads_path)
    profile_picture_file.save(os.path.join(uploads_path, filename))
    return os.path.join(current_app.config['main']['UPLOAD_FOLDER'], filename)


def save_badge_image(image_file):
    try:
        # Generate a secure filename
        filename = secure_filename(f"{uuid.uuid4()}.png")
        rel_path = os.path.join('images', 'badge_images', filename)  # No leading slashes
        abs_path = os.path.join(current_app.root_path, current_app.static_folder, rel_path)

        # Save the file
        image_file.save(abs_path)
        return filename  # Return the correct relative path from 'static' directory

    except Exception as e:
        print(f"Error saving badge image: {e}")
        raise ValueError(f"Failed to save image: {str(e)}")


def save_bicycle_picture(bicycle_picture_file, old_filename=None):
    """
    Save the uploaded bicycle picture, replacing the old one if provided.
    """
    if old_filename:
        old_path = os.path.join(current_app.root_path, 'static', old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)  # Remove the old file

    ext = bicycle_picture_file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("File extension not allowed.")
    
    filename = secure_filename(f"{uuid.uuid4()}.{ext}")
    uploads_path = os.path.join(current_app.root_path, 'static', current_app.config['main']['UPLOAD_FOLDER'], 'bicycle_pictures')
    if not os.path.exists(uploads_path):
        os.makedirs(uploads_path)

    bicycle_picture_file.save(os.path.join(uploads_path, filename))
    return os.path.join(current_app.config['main']['UPLOAD_FOLDER'], 'bicycle_pictures', filename)


def save_submission_image(submission_image_file):
    try:
        ext = submission_image_file.filename.rsplit('.', 1)[-1]
        filename = secure_filename(f"{uuid.uuid4()}.{ext}")
        uploads_dir = os.path.join(current_app.static_folder, 'images', 'verifications')
        
        # Ensure the upload directory exists
        os.makedirs(uploads_dir, exist_ok=True)
        
        full_path = os.path.join(uploads_dir, filename)
        submission_image_file.save(full_path)
        return os.path.join('images', 'verifications', filename)
    except Exception as e:
        current_app.logger.error(f"Failed to save image: {e}")
        raise


def save_sponsor_logo(image_file, old_filename=None):
    # Check if the uploaded file has a valid filename
    if image_file and allowed_file(image_file.filename):
        # Secure the filename and generate a unique identifier to avoid collisions
        ext = image_file.filename.rsplit('.', 1)[-1].lower()
        filename = secure_filename(f"{uuid.uuid4()}.{ext}")

        # Define the upload path
        upload_path = os.path.join(current_app.root_path, 'static/images/sponsors')

        # Ensure the directory exists
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)

        # Save the new file
        file_path = os.path.join(upload_path, filename)
        try:
            image_file.save(file_path)
        except Exception as e:
            raise ValueError(f"Failed to save image: {str(e)}")

        # Remove the old file if provided
        if old_filename:
            old_file_path = os.path.join(current_app.root_path, 'static', old_filename)
            if os.path.exists(old_file_path):
                try:
                    os.remove(old_file_path)
                except Exception as e:
                    current_app.logger.error(f"Failed to remove old image: {str(e)}")

        # Return the relative path to the saved file
        return os.path.join('images', 'sponsors', filename)

    else:
        raise ValueError("Invalid file type or no file provided.")


def can_complete_task(user_id, task_id):
    now = datetime.now()
    task = Task.query.get(task_id)
    
    if not task:
        print(f"No task found for Task ID: {task_id}")
        return False, None  # Task does not exist
    
    print(f"Current time: {now}")
    print(f"Task found: {task.title} with frequency {task.frequency} and completion limit {task.completion_limit}")

    # Determine the start of the relevant period based on frequency
    period_start_map = {
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1),
        'monthly': timedelta(days=30)  # Approximation for monthly
    }
    period_start = now - period_start_map.get(task.frequency, timedelta(days=1))
    print(f"Period start calculated as: {period_start}")

    # Count completions in the defined period
    completions_within_period = TaskSubmission.query.filter(
        TaskSubmission.user_id == user_id,
        TaskSubmission.task_id == task_id,
        TaskSubmission.timestamp >= period_start
    ).count()

    print(f"Completions within period for user {user_id} on task {task_id}: {completions_within_period}")

    # Check if the user can verify the task again
    can_verify = completions_within_period < task.completion_limit
    next_eligible_time = None
    if not can_verify:
        first_completion_in_period = TaskSubmission.query.filter(
            TaskSubmission.user_id == user_id,
            TaskSubmission.task_id == task_id,
            TaskSubmission.timestamp >= period_start
        ).order_by(TaskSubmission.timestamp.asc()).first()

        if first_completion_in_period:
            print(f"First Completion in the period found at: {first_completion_in_period.timestamp}")
            # Calculate when the user is eligible next, based on the first completion time
            increment_map = {
                'daily': timedelta(days=1),
                'weekly': timedelta(weeks=1),
                'monthly': timedelta(days=30)
            }
            next_eligible_time = first_completion_in_period.timestamp + increment_map.get(task.frequency, timedelta(days=1))
            print(f"Next eligible time calculated as: {next_eligible_time}")
        else:
            print("No completions found within the period.")
    else:
        print("User can currently verify the task.")

    return can_verify, next_eligible_time


def getLastRelevantCompletionTime(user_id, task_id):
    now = datetime.now()
    task = Task.query.get(task_id)
    
    if not task:
        return None  # Task does not exist

    # Start of the period calculation must reflect the frequency
    period_start_map = {
        'daily': now - timedelta(days=1),
        'weekly': now - timedelta(weeks=1),
        'monthly': now - timedelta(days=30)
    }
    
    # Get the period start time based on the task's frequency
    period_start = period_start_map.get(task.frequency, now)  # Default to now if frequency is not recognized


    # Fetch the last completion that affects the current period
    last_relevant_completion = TaskSubmission.query.filter(
        TaskSubmission.user_id == user_id,
        TaskSubmission.task_id == task_id,
        TaskSubmission.timestamp >= period_start
    ).order_by(TaskSubmission.timestamp.desc()).first()

    return last_relevant_completion.timestamp if last_relevant_completion else None


def check_and_award_badges(user_id, task_id, game_id):
    print(f"Checking and awarding badges for user_id={user_id}, task_id={task_id}")
    user = User.query.get(user_id)
    task = Task.query.get(task_id)
    user_task = UserTask.query.filter_by(user_id=user_id, task_id=task_id).first()

    if not user_task:
        print("No UserTask found.")
        return

    print(f"UserTask found: completions={user_task.completions}, task completion limit={task.completion_limit}")
    
    if user_task.completions >= task.completion_limit:
        print("Condition met for awarding badge based on task completion limit.")
        if task.badge and task.badge not in user.badges:
            user.badges.append(task.badge)
            db.session.add(ShoutBoardMessage(
                message=f" earned the badge '{task.badge.name}' for task <a href='javascript:void(0);' onclick='openTaskDetailModal({task.id})'>{task.title}</a>",
                user_id=user_id,
                game_id=game_id
            ))
            db.session.commit()
            print(f"Badge '{task.badge.name}' awarded to user '{user.display_name}' for completing task '{task.title}'")
        else:
            print(f"No badge awarded: either no badge assigned for task or user already has the badge")
    else:
        print("Condition not met for awarding badge based on task completion limit.")

    if task.category and task.game_id:
        tasks_in_category = Task.query.filter_by(category=task.category, game_id=task.game_id).all()
        completed_tasks = {ut.task_id for ut in user.user_tasks.join(Task).filter(Task.category == task.category, Task.game_id == task.game_id) if ut.completions >= 1}

        category_task_ids = {t.id for t in tasks_in_category}
        print(f"Tasks in category '{task.category}' for game ID {task.game_id}: {category_task_ids}")
        print(f"Completed tasks in category by user for this game: {completed_tasks}")

        if category_task_ids == completed_tasks:
            print("Condition met for awarding badge based on category completion.")
            category_badges = Badge.query.filter_by(category=task.category).all()
            for badge in category_badges:
                if badge not in user.badges:
                    user.badges.append(badge)
                    db.session.add(ShoutBoardMessage(
                        message=f" earned the badge '{badge.name}' for completing all tasks in category '{task.category}'",
                        user_id=user_id,
                        game_id=game_id
                    ))
                    db.session.commit()
                    print(f"Badge '{badge.name}' awarded for completing all tasks in category '{task.category}' within game ID {task.game_id}")
                else:
                    print(f"User already has badge '{badge.name}', not awarded again")
        else:
            print("Condition not met for awarding badge based on category completion.")

def check_and_revoke_badges(user_id):
    user = User.query.get(user_id)
    badges_to_remove = []

    for badge in user.badges:
        # Determine the logic to check if the badge should still be held
        # This depends heavily on how badge conditions are defined. Here's a generic example:

        # Check if all tasks required for the badge are still completed as required
        all_tasks_completed = True
        for task in badge.tasks:
            user_task = UserTask.query.filter_by(user_id=user_id, task_id=task.id).first()
            if not user_task or user_task.completions < task.completion_limit:
                all_tasks_completed = False
                break

        if not all_tasks_completed:
            badges_to_remove.append(badge)

    for badge in badges_to_remove:
        user.badges.remove(badge)
        print(f"Badge '{badge.name}' removed from user '{user.username}'")

    db.session.commit()


def load_credentials():
    creds = None
    creds_file = os.path.join(current_app.root_path, '..', 'credentials.json')
    creds_file = os.path.abspath(creds_file)
    current_app.logger.error(f'Looking for credentials.json at: {creds_file}')
    if os.path.exists(creds_file):
        creds = Credentials.from_authorized_user_file(creds_file, SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save the refreshed credentials
            with open(creds_file, 'w') as token_file:
                token_file.write(creds.to_json())
    else:
        current_app.logger.error('Credentials not found. Please run the authorization script.')
        return None
    return creds


def save_credentials(creds):
    """Helper function to save refreshed credentials."""
    creds_file = os.path.join(current_app.root_path, '..', 'credentials.json')
    with open(creds_file, 'w') as token_file:
        token_file.write(creds.to_json())


def refresh_credentials(creds):
    if creds:
        current_app.logger.info(f"Current token expiry: {creds.expiry}")
    if creds and creds.expired and creds.refresh_token:
        current_app.logger.info("Token expired. Refreshing token...")
        creds.refresh(Request())
        save_credentials(creds)
        current_app.logger.info(f"New token expiry: {creds.expiry}")
    return creds


def generate_oauth2_string(username, access_token):
    auth_string = f'user={username}\1auth=Bearer {access_token}\1\1'
    return base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')


def send_email(to, subject, html_content):
    creds = load_credentials()
    if not creds:
        current_app.logger.error('Failed to load credentials.')
        return False

    # Ensure credentials are valid and refresh them if necessary
    creds = refresh_credentials(creds)
    if not creds or not creds.valid:
        current_app.logger.error('Invalid or expired credentials.')
        return False

    access_token = creds.token
    auth_string = generate_oauth2_string(current_app.config['MAIL_USERNAME'], access_token)

    # Create the email message
    msg = MIMEText(html_content, 'html')
    msg['Subject'] = subject
    msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
    msg['To'] = to

    try:
        # Connect to Gmail SMTP server
        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.ehlo()

        # Authenticate using OAuth2
        smtp_server.docmd('AUTH', 'XOAUTH2 ' + auth_string)

        # Send the email
        smtp_server.sendmail(msg['From'], [to], msg.as_string())
        smtp_server.quit()
        current_app.logger.info('Email sent successfully.')
        return True
    except Exception as e:
        current_app.logger.error(f'Failed to send email: {e}')
        return False


def generate_tutorial_game():
    current_quarter = (datetime.now().month - 1) // 3 + 1
    year = datetime.now().year
    title = f"Tutorial Game - Q{current_quarter} {year}"

    existing_game = Game.query.filter_by(is_tutorial=True, title=title).first()
    if existing_game:
        return  # Just return, do nothing if the game already exists

    description = """
    Welcome to the newest Tutorial Game! Embark on a quest to create a more sustainable future while enjoying everyday activities, having fun, and fostering teamwork in the real-life battle against climate change.

    Task Instructions:

    Concepts:

    How to Play:

    Play solo or join forces with friends in teams.
    Explore the tasks and have fun completing them to earn Carbon Reduction Points.
    Once a task is verified, you'll earn points displayed on the Leaderboard and badges of honor. Tasks can be verified by uploading an image from your computer, taking a photo, writing a comment, or using a QR code.
    Earn achievement badges by completing a group of tasks or repeating tasks. Learn more about badge criteria by clicking on the task name. 
    """

    start_date = datetime(year, 3 * (current_quarter - 1) + 1, 1)
    if current_quarter == 4:
        end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        end_date = datetime(year, 3 * current_quarter + 1, 1) - timedelta(seconds=1)

    tutorial_game = Game(
        title=title,
        description=description,
        description2="Rules and guidelines for the tutorial game.",
        start_date=start_date,
        end_date=end_date,
        game_goal=20000,
        details="""
        Verifying and Earning "Carbon Reduction" Points:

        Sign In and Access Tasks: Log into the game, navigate to the homepage, and scroll down on the main game page to see the task list.
        Complete a Task: Choose by clicking on a task from the list, and after completion, click "Verify Task". You will need to upload a picture as proof of your achievement and/or you can add a comment about your experience.
        Submit Verification: After uploading your verification photo and adding a comment, click the "Submit Verification" button. You should receive a confirmation message indicating your task completion has been updated. Your image will appear at the bottom of the page and it will be automatically uploaded to Quest by Cycle’s social Media accounts.
        Social Media Interaction: The uploaded photo will be shared on QuestByCycle’s Twitter, Facebook, and Instagram pages. You can view and expand thumbnail images of completed tasks by others, read comments, and visit their profiles by clicking on the images. Use the social media buttons to comment and engage with the community.
        Explore the Leaderboard: Check the dynamic leaderboard to see the progress of players and teams. The community-wide impact is displayed via a "thermometer" showing collective carbon reduction efforts. Clicking on a player's name reveals their completed tasks and badges.

        Earning Badges:

        Task Categories: Each task belongs to a category. Completing all tasks in a category earns you a badge. The more tasks you complete, the higher your chances of earning badges.
        Task Limits: The task detail popup provides completion limits. If you reach the limit set for a task, you will earn a badge.

        Social Media Interaction:

        Task Entries: Engage with the community by commenting and sharing your achievements on social media platforms directly through the game. Click on the thumbnail images at the bottom of a Task to view user's submissions. At the bottom, there will be buttons to take you to Facebook, X, and Instagram where you can comment on various tasks that have been posted and communicate with other players. Through friendly competition, let's strive to reduce carbon emissions and make a positive impact on the atmosphere.
        """,
        awards="""
        Stay tuned for prizes...
        """,
        beyond="Visit your local bike club!",
        admin_id=1,  # Assuming admin_id=1 is the system admin
        is_tutorial=True,
        twitter_username=current_app.config['TWITTER_USERNAME'],
        twitter_api_key=current_app.config['TWITTER_API_KEY'],
        twitter_api_secret=current_app.config['TWITTER_API_SECRET'],
        twitter_access_token=current_app.config['TWITTER_ACCESS_TOKEN'],
        twitter_access_token_secret=current_app.config['TWITTER_ACCESS_TOKEN_SECRET'],
        facebook_app_id=current_app.config['FACEBOOK_APP_ID'],
        facebook_app_secret=current_app.config['FACEBOOK_APP_SECRET'],
        facebook_access_token=current_app.config['FACEBOOK_ACCESS_TOKEN'],
        facebook_page_id=current_app.config['FACEBOOK_PAGE_ID'],
        instagram_access_token=current_app.config['INSTAGRAM_ACCESS_TOKEN'],
        instagram_user_id=current_app.config['INSTAGRAM_USER_ID'],
        is_public=True,
        allow_joins=True,
        leaderboard_image="leaderboard_image.png"  # Assuming the image is stored in the static folder
    )
    db.session.add(tutorial_game)
    db.session.commit()

    # Import tasks and badges for the tutorial game
    import_tasks_and_badges_from_csv(tutorial_game.id, os.path.join(current_app.static_folder, 'defaulttasks.csv'))

    # Add pinned message from admin
    try:
        admin_id = 1  # Assuming admin_id=1 is the system admin
        print(f"Creating pinned message for game_id: {tutorial_game.id}")
        pinned_message = ShoutBoardMessage(
            message="Get on your Bicycle this Quarter!",
            user_id=admin_id,
            game_id=tutorial_game.id,
            is_pinned=True,
            timestamp=datetime.now(utc)
        )
        db.session.add(pinned_message)
        db.session.commit()
        print("Pinned message created successfully")
    except Exception as e:
        print(f"Error creating pinned message: {e}")
        db.session.rollback()

    return tutorial_game


def import_tasks_and_badges_from_csv(game_id, csv_path):
    print(f"Starting import for game_id: {game_id} from csv_path: {csv_path}")
    
    try:
        with open(csv_path, mode='r', encoding='utf-8') as csv_file:
            data = csv.DictReader(csv_file)
            for row in data:
                print(f"Processing row: {row}")

                badge_name = sanitize_html(row['badge_name'])
                badge_description = sanitize_html(row['badge_description'])
                
                # Generate the badge image filename if it's not provided
                if 'badge_image_filename' in row and row['badge_image_filename']:
                    badge_image_filename = row['badge_image_filename']
                else:
                    badge_image_filename = f"{badge_name.lower().replace(' ', '_')}.png"
                
                badge_image_path = os.path.join(current_app.static_folder, 'images', 'badge_images', badge_image_filename)

                print(f"Badge details - Name: {badge_name}, Description: {badge_description}, Image Path: {badge_image_path}")

                if not os.path.exists(badge_image_path):
                    print(f"Badge image not found at {badge_image_path}, skipping badge creation")
                    continue

                badge = Badge.query.filter_by(name=badge_name).first()
                if not badge:
                    badge = Badge(
                        name=badge_name,
                        description=badge_description,
                        image=badge_image_filename  # Store the filename, not the full path
                    )
                    db.session.add(badge)
                    db.session.flush()
                    print(f"Added new badge: {badge}")

                task = Task(
                    category=sanitize_html(row['category']),
                    title=sanitize_html(row['title']),
                    description=sanitize_html(row['description']),
                    tips=sanitize_html(row['tips']),
                    points=int(row['points'].replace(',', '')),
                    completion_limit=int(row['completion_limit']),
                    frequency=sanitize_html(row['frequency']),
                    verification_type=sanitize_html(row['verification_type']),
                    badge_id=badge.id,
                    game_id=game_id
                )
                db.session.add(task)
                print(f"Added new task: {task}")

            db.session.commit()
            print("Import completed successfully")
    except Exception as e:
        print(f"Error during import: {e}")
        db.session.rollback()


def log_user_ip(user):
    # Check if this IP address is already stored for this user
    ip_address = request.remote_addr
    existing_ip = UserIP.query.filter_by(user_id=user.id, ip_address=ip_address).first()

    if not existing_ip:
        # Only log the IP if it's not already stored
        new_ip = UserIP(user_id=user.id, ip_address=ip_address)
        db.session.add(new_ip)
        db.session.commit()