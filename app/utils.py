from flask import flash, current_app, jsonify, request
from .models import db, Quest, Badge, Game, UserQuest, User, ShoutBoardMessage, QuestSubmission, UserIP
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
        total_points = sum(quest.points_awarded for quest in user.user_quests if quest.points_awarded is not None)

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


def can_complete_quest(user_id, quest_id):
    now = datetime.now()
    quest = Quest.query.get(quest_id)
    
    if not quest:
        print(f"No quest found for Quest ID: {quest_id}")
        return False, None  # Quest does not exist
    
    print(f"Current time: {now}")
    print(f"Quest found: {quest.title} with frequency {quest.frequency} and completion limit {quest.completion_limit}")

    # Determine the start of the relevant period based on frequency
    period_start_map = {
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1),
        'monthly': timedelta(days=30)  # Approximation for monthly
    }
    period_start = now - period_start_map.get(quest.frequency, timedelta(days=1))
    print(f"Period start calculated as: {period_start}")

    # Count completions in the defined period
    completions_within_period = QuestSubmission.query.filter(
        QuestSubmission.user_id == user_id,
        QuestSubmission.quest_id == quest_id,
        QuestSubmission.timestamp >= period_start
    ).count()

    print(f"Completions within period for user {user_id} on quest {quest_id}: {completions_within_period}")

    # Check if the user can verify the quest again
    can_verify = completions_within_period < quest.completion_limit
    next_eligible_time = None
    if not can_verify:
        first_completion_in_period = QuestSubmission.query.filter(
            QuestSubmission.user_id == user_id,
            QuestSubmission.quest_id == quest_id,
            QuestSubmission.timestamp >= period_start
        ).order_by(QuestSubmission.timestamp.asc()).first()

        if first_completion_in_period:
            print(f"First Completion in the period found at: {first_completion_in_period.timestamp}")
            # Calculate when the user is eligible next, based on the first completion time
            increment_map = {
                'daily': timedelta(days=1),
                'weekly': timedelta(weeks=1),
                'monthly': timedelta(days=30)
            }
            next_eligible_time = first_completion_in_period.timestamp + increment_map.get(quest.frequency, timedelta(days=1))
            print(f"Next eligible time calculated as: {next_eligible_time}")
        else:
            print("No completions found within the period.")
    else:
        print("User can currently verify the quest.")

    return can_verify, next_eligible_time


def getLastRelevantCompletionTime(user_id, quest_id):
    now = datetime.now()
    quest = Quest.query.get(quest_id)
    
    if not quest:
        return None  # Quest does not exist

    # Start of the period calculation must reflect the frequency
    period_start_map = {
        'daily': now - timedelta(days=1),
        'weekly': now - timedelta(weeks=1),
        'monthly': now - timedelta(days=30)
    }
    
    # Get the period start time based on the quest's frequency
    period_start = period_start_map.get(quest.frequency, now)  # Default to now if frequency is not recognized


    # Fetch the last completion that affects the current period
    last_relevant_completion = QuestSubmission.query.filter(
        QuestSubmission.user_id == user_id,
        QuestSubmission.quest_id == quest_id,
        QuestSubmission.timestamp >= period_start
    ).order_by(QuestSubmission.timestamp.desc()).first()

    return last_relevant_completion.timestamp if last_relevant_completion else None


def check_and_award_badges(user_id, quest_id, game_id):
    """
    Check if a badge should be awarded for a quest and award it.
    For quests that award a badge, if the user’s completion count
    reaches or exceeds the quest’s badge_awarded value, only the badge-award
    message is created (suppressing a generic "completed a quest" message).
    Also, this function handles awarding any category-based badges.
    """
    print(f"Checking and awarding badges for user_id={user_id}, quest_id={quest_id}")
    user = User.query.get(user_id)
    quest = Quest.query.get(quest_id)
    user_quest = UserQuest.query.filter_by(user_id=user_id, quest_id=quest_id).first()

    if not user_quest:
        print("No UserQuest found.")
        return

    print(f"UserQuest found: completions={user_quest.completions}, quest completion limit={quest.completion_limit}")

    # --- Quest-Specific Badge Awarding ---
    if quest.badge and user_quest.completions >= quest.badge_awarded:
        if quest.badge not in user.badges:
            user.badges.append(quest.badge)
            db.session.add(ShoutBoardMessage(
                message=(
                    f" earned the badge "
                    f"<a href='javascript:void(0);' onclick='openBadgeModal(this)' "
                    f"data-badge-id='{quest.badge.id}' "
                    f"data-badge-name='{quest.badge.name}' "
                    f"data-badge-description='{quest.badge.description}' "
                    f"data-badge-image='{quest.badge.image}' "
                    f"data-task-name='{quest.title}' "
                    f"data-badge-awarded-count='{quest.badge_awarded}' "  # Use quest.badge_awarded from the Quest model
                    f"data-task-id='{quest.id}' "
                    f"data-user-completions='{user_quest.completions}'>{quest.badge.name}</a> for completing quest "
                    f"<a href='javascript:void(0);' onclick='openQuestDetailModal({quest.id})'>{quest.title}</a>"
                ),
                user_id=user_id,
                game_id=game_id
            ))
            db.session.commit()
            print(f"Badge '{quest.badge.name}' awarded to user '{user.display_name}' for quest '{quest.title}'")
        else:
            print("Badge already awarded; no duplicate message generated.")
    else:
        print("No badge awarded or quest has no badge; generic completion message suppressed.")

    # --- Category-Based Badge Awarding ---
    if quest.category and quest.game_id:
        category_badges = Badge.query.filter_by(category=quest.category).all()
        category_quests = Quest.query.filter_by(category=quest.category, game_id=quest.game_id).all()
        completed_quests = {
            ut.quest for ut in user.user_quests
            if ut.completions >= ut.quest.completion_limit and ut.quest.category == quest.category
        }

        for badge in category_badges:
            if badge not in user.badges and set(category_quests) == completed_quests:
                user.badges.append(badge)
                db.session.add(ShoutBoardMessage(
                    message=(
                        f" earned the badge "
                        f"<a href='javascript:void(0);' onclick='openBadgeModal(this)' "
                        f"data-badge-id='{badge.id}' "
                        f"data-badge-name='{badge.name}' "
                        f"data-badge-description='{badge.description}' "
                        f"data-badge-image='{badge.image}' "
                        f"data-task-name='{quest.title}' "  # For category badges, you may choose to display a representative task name.
                        f"data-badge-awarded-count='1' "  # Constant value for category badges.
                        f"data-task-id='{quest.id}' "
                        f"data-user-completions='{user_quest.completions}'>{badge.name}</a> for completing all quests in category '{quest.category}'"
                    ),
                    user_id=user_id,
                    game_id=game_id
                ))
                db.session.commit()
                print(f"Badge '{badge.name}' awarded for completing all quests in category '{quest.category}' within game ID {quest.game_id}")
            else:
                print(f"User already has badge '{badge.name}', not awarded again")


def check_and_revoke_badges(user_id, game_id=None):
    """
    Check if any badges awarded to the user should be revoked because
    the required quest completions are no longer met. When revoking a badge,
    delete the original awarded message associated with the badge instead of
    creating a new revocation message.
    
    Args:
        user_id (int): The ID of the user.
        game_id (int, optional): The game ID to associate with the revocation.
    """
    user = User.query.get(user_id)
    if not user:
        print(f"No user found with ID {user_id}")
        return

    badges_to_remove = []
    
    # Check each badge and determine if it should be revoked.
    for badge in user.badges:
        all_quests_completed = True
        for quest in badge.quests:
            user_quest = UserQuest.query.filter_by(user_id=user_id, quest_id=quest.id).first()
            # Using quest.badge_awarded as the threshold for completion.
            if not user_quest or user_quest.completions < quest.badge_awarded:
                all_quests_completed = False
                break

        if not all_quests_completed:
            badges_to_remove.append(badge)

    # Process each badge that needs to be revoked.
    for badge in badges_to_remove:
        user.badges.remove(badge)
        print(f"Revoking badge '{badge.name}' from user '{user.username}'")

        # Retrieve all shoutboard messages for this user and game.
        messages = ShoutBoardMessage.query.filter_by(
            user_id=user_id,
            game_id=game_id if game_id is not None else 0
        ).all()

        found_message = None
        # Look for the message containing the specific badge identifier.
        for message in messages:
            if f"data-badge-id='{badge.id}'" in message.message:
                found_message = message
                break

        if found_message:
            db.session.delete(found_message)
            print(f"Deleted awarded message for badge '{badge.name}' (message ID: {found_message.id})")
        else:
            print(f"No awarded message found for badge '{badge.name}', nothing to delete.")

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

    Quest Instructions:

    Concepts:

    How to Play:

    Play solo or join forces with friends in teams.
    Explore the quests and have fun completing them to earn Carbon Reduction Points.
    Once a quest is verified, you'll earn points displayed on the Leaderboard and badges of honor. Quests can be verified by uploading an image from your computer, taking a photo, writing a comment, or using a QR code.
    Earn achievement badges by completing a group of quests or repeating quests. Learn more about badge criteria by clicking on the quest name. 
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

        Sign In and Access Quests: Log into the game, navigate to the homepage, and scroll down on the main game page to see the quest list.
        Complete a Quest: Choose by clicking on a quest from the list, and after completion, click "Verify Quest". You will need to upload a picture as proof of your achievement and/or you can add a comment about your experience.
        Submit Verification: After uploading your verification photo and adding a comment, click the "Submit Verification" button. You should receive a confirmation message indicating your quest completion has been updated. Your image will appear at the bottom of the page and it will be automatically uploaded to Quest by Cycle’s social Media accounts.
        Social Media Interaction: The uploaded photo will be shared on QuestByCycle’s Twitter, Facebook, and Instagram pages. You can view and expand thumbnail images of completed quests by others, read comments, and visit their profiles by clicking on the images. Use the social media buttons to comment and engage with the community.
        Explore the Leaderboard: Check the dynamic leaderboard to see the progress of players and teams. The community-wide impact is displayed via a "thermometer" showing collective carbon reduction efforts. Clicking on a player's name reveals their completed quests and badges.

        Earning Badges:

        Quest Categories: Each quest belongs to a category. Completing all quests in a category earns you a badge. The more quests you complete, the higher your chances of earning badges.
        Quest Limits: The quest detail popup provides completion limits. If you reach the limit set for a quest, you will earn a badge.

        Social Media Interaction:

        Quest Entries: Engage with the community by commenting and sharing your achievements on social media platforms directly through the game. Click on the thumbnail images at the bottom of a Quest to view user's submissions. At the bottom, there will be buttons to take you to Facebook, X, and Instagram where you can comment on various quests that have been posted and communicate with other players. Through friendly competition, let's strive to reduce carbon emissions and make a positive impact on the atmosphere.
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

    # Import quests and badges for the tutorial game
    import_quests_and_badges_from_csv(tutorial_game.id, os.path.join(current_app.static_folder, 'defaultquests.csv'))

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


def import_quests_and_badges_from_csv(game_id, csv_path):
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

                quest = Quest(
                    category=sanitize_html(row['category']),
                    title=sanitize_html(row['title']),
                    description=sanitize_html(row['description']),
                    tips=sanitize_html(row['tips']),
                    points=int(row['points'].replace(',', '')),
                    badge_awarded=int(row['badge_awarded']),
                    completion_limit=int(row['completion_limit']),
                    frequency=sanitize_html(row['frequency']),
                    verification_type=sanitize_html(row['verification_type']),
                    badge_id=badge.id,
                    game_id=game_id
                )
                db.session.add(quest)
                print(f"Added new quest: {quest}")

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


def get_game_badges(game_id):
    print(f"get_game_badges called for game_id: {game_id}")  # Logging game_id
    game = Game.query.get(game_id)
    if not game:
        print("Game not found in get_game_badges")  # Log if game is not found
        return []

    badges = Badge.query.join(Quest).filter(Quest.game_id == game_id, Quest.badge_id.isnot(None)).distinct().all()

    print(f"get_game_badges returning {len(badges)} badges")  # Log number of badges returned
    return badges


def enhance_badges_with_task_info(badges, game_id=None, user_id=None):
    enhanced_badges = []
    for badge in badges:
        # Filter awarding quests for this badge for the current game (if provided)
        if game_id:
            awarding_quests = [quest for quest in badge.quests if quest.game_id == game_id]
        else:
            awarding_quests = badge.quests

        if awarding_quests:
            task_names = ", ".join(quest.title for quest in awarding_quests)
            task_ids = ", ".join(str(quest.id) for quest in awarding_quests)
            badge_awarded_counts = ", ".join(str(quest.badge_awarded) for quest in awarding_quests)
        else:
            task_names = ""
            task_ids = ""
            badge_awarded_counts = "1"
        
        # Compute the user's completions and a flag for award status.
        user_completions_total = 0
        is_complete = False
        if awarding_quests and user_id:
            completions_list = []
            for quest in awarding_quests:
                user_quest = UserQuest.query.filter_by(user_id=user_id, quest_id=quest.id).first()
                completions = user_quest.completions if user_quest else 0
                completions_list.append(completions)
                if completions >= quest.badge_awarded:
                    is_complete = True
            user_completions_total = max(completions_list) if completions_list else 0

        enhanced_badges.append({
            'id': badge.id,
            'name': badge.name,
            'description': badge.description,
            'image': badge.image,
            'category': badge.category,
            'task_names': task_names,
            'task_ids': task_ids,
            'badge_awarded_counts': badge_awarded_counts,
            'user_completions': user_completions_total,
            'is_complete': is_complete
        })
    return enhanced_badges
