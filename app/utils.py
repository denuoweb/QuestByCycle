import uuid
import os
import csv
import bleach
import smtplib
from flask import current_app, request, url_for
from .models import db, Quest, Badge, Game, UserQuest, User, ShoutBoardMessage, QuestSubmission, UserIP
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from PIL import Image
from pytz import utc
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image    import MIMEImage
from sqlalchemy.exc import SQLAlchemyError, OperationalError

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

        image_file.save(abs_path)
        return rel_path

    except Exception as e:
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
    except Exception as e:
        raise ValueError(f"Failed to generate smoggy images: {str(e)}")

def update_user_score(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return False

        # Calculate the total points awarded to the user
        total_points = sum(quest.points_awarded for quest in user.user_quests if quest.points_awarded is not None)

        # Update user score, ensuring it doesn't exceed a predefined maximum
        user.score = min(total_points, MAX_POINTS_INT)

        # Commit changes to the database
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()  # Rollback in case of any exception
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
    now = datetime.now(utc)
    quest = Quest.query.get(quest_id)
    
    if not quest:
        return False, None  # Quest does not exist
    
    # Determine the start of the relevant period based on frequency
    period_start_map = {
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1),
        'monthly': timedelta(days=30)  # Approximation for monthly
    }
    period_start = now - period_start_map.get(quest.frequency, timedelta(days=1))
    # Count completions in the defined period
    completions_within_period = QuestSubmission.query.filter(
        QuestSubmission.user_id == user_id,
        QuestSubmission.quest_id == quest_id,
        QuestSubmission.timestamp >= period_start
    ).count()

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
            # Calculate when the user is eligible next, based on the first completion time
            increment_map = {
                'daily': timedelta(days=1),
                'weekly': timedelta(weeks=1),
                'monthly': timedelta(days=30)
            }
            next_eligible_time = first_completion_in_period.timestamp + increment_map.get(quest.frequency, timedelta(days=1))

    return can_verify, next_eligible_time


def getLastRelevantCompletionTime(user_id, quest_id):
    now = datetime.now(utc)
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
    Award badges for a quest:
      - For quest-specific badges: Award if the user’s completions for the quest 
        reach or exceed quest.badge_awarded.
      - For category badges: Award if the user has at least one completion on 
        every quest in that category for the specified game.
    All awards and associated shoutboard messages are tied to the given game_id.
    """
    user = User.query.get(user_id)
    quest = Quest.query.get(quest_id)
    user_quest = UserQuest.query.filter_by(user_id=user_id, quest_id=quest_id).first()
    if not user_quest:
        return

    # --- Quest-Specific Badge Awarding ---
    if quest.badge and user_quest.completions >= quest.badge_awarded:
        # Check for an existing award message for this quest badge in this game.
        existing_award = ShoutBoardMessage.query.filter_by(
            user_id=user_id,
            game_id=game_id
        ).filter(ShoutBoardMessage.message.contains(f"data-badge-id='{quest.badge.id}'")).first()
        if not existing_award:
            # Award the quest-specific badge.
            user.badges.append(quest.badge)
            msg = (
                f" earned the badge"
                f"<a class='quest-title' href='javascript:void(0);' onclick='openBadgeModal(this)' "
                f"data-badge-id='{quest.badge.id}' "
                f"data-badge-name='{quest.badge.name}' "
                f"data-badge-description='{quest.badge.description}' "
                f"data-badge-image='{quest.badge.image}' "
                f"data-task-name='{quest.title}' "
                f"data-badge-awarded-count='{quest.badge_awarded}' "
                f"data-task-id='{quest.id}' "
                f"data-user-completions='{user_quest.completions}'>"
                f"{quest.badge.name}"
                f"</a>for completing quest "
                f"<a class='quest-title' href='javascript:void(0);' onclick='openQuestDetailModal({quest.id})'>"
                f"{quest.title}"
                f"</a>"
            )
            sbm = ShoutBoardMessage(message=msg, user_id=user_id, game_id=game_id)
            db.session.add(sbm)
            db.session.commit()

    # --- Category-Based Badge Awarding ---
    if quest.category and game_id:
        # Get all quests in the category for the specified game.
        category_quests = Quest.query.filter_by(category=quest.category, game_id=game_id).all()
        if not category_quests:
            return
        # Determine which of those quests the user has completed at least once.
        completed_quests = [
            ut.quest for ut in user.user_quests
            if ut.quest.category == quest.category and ut.quest.game_id == game_id and ut.completions >= 1
        ]
        # Only award if the user has at least one completion for every quest.
        if len(completed_quests) == len(category_quests):
            # Retrieve all badges for this category.
            category_badges = Badge.query.filter_by(category=quest.category).all()
            for badge in category_badges:
                # Check for an existing award message for this category badge in this game.
                existing_award = ShoutBoardMessage.query.filter_by(
                    user_id=user_id,
                    game_id=game_id
                ).filter(ShoutBoardMessage.message.contains(f"data-badge-id='{badge.id}'")).first()
                if not existing_award:
                    url = url_for(
                        'static',
                        filename=f'images/badge_images/{badge.image}'
                    )
                    user.badges.append(badge)
                    msg = (
                        f" earned the badge "
                        f"<a class='quest-title' href='javascript:void(0);' onclick='openBadgeModal(this)' "
                        f"data-badge-id='{badge.id}' "
                        f"data-badge-name='{badge.name}' "
                        f"data-badge-description='{badge.description}' "
                        f"data-badge-image='{url}' "
                        f"data-task-name='{quest.title}' "
                        f"data-badge-awarded-count='1' "
                        f"data-task-id='{quest.id}' "
                        f"data-user-completed='{len(completed_quests)}' "
                        f"data-total-tasks='{len(category_quests)}'>"
                        f"{badge.name}"
                        f"</a> for completing all quests in category '{quest.category}'"
                    )
                    sbm = ShoutBoardMessage(message=msg, user_id=user_id, game_id=game_id)
                    db.session.add(sbm)
                    db.session.commit()


def check_and_revoke_badges(user_id, game_id=None):
    """
    Revoke badges awarded to the user if the tasks in the specified game no longer meet 
    the required conditions.
      - Quest-specific badges are revoked if the user’s completions for any awarding quest 
        fall below quest.badge_awarded.
      - Category badges are revoked if the user has not completed at least one of every quest 
        in that badge’s category for the specified game.
    When revoking a badge, its associated shoutboard award message is deleted.
    """
    user = User.query.get(user_id)
    if not user:
        return

    badges_to_remove = []
    for badge in user.badges:
        if badge.category:
            # Category badge: restrict to quests in this category for the current game.
            current_category_quests = Quest.query.filter_by(category=badge.category, game_id=game_id).all()
            completed_quests = {
                ut.quest for ut in user.user_quests
                if ut.quest.category == badge.category and ut.quest.game_id == game_id and ut.completions >= 1
            }
            if set(current_category_quests) != set(completed_quests):
                badges_to_remove.append(badge)
        else:
            # Quest-specific badge: revoke if for any awarding quest the user's completions are below threshold.
            all_met = True
            for quest in badge.quests:
                user_quest = UserQuest.query.filter_by(user_id=user_id, quest_id=quest.id).first()
                if not user_quest or user_quest.completions < quest.badge_awarded:
                    all_met = False
                    break
            if not all_met:
                badges_to_remove.append(badge)

    for badge in badges_to_remove:
        user.badges.remove(badge)
        # Delete any associated shoutboard award message in the specified game.
        messages = ShoutBoardMessage.query.filter_by(user_id=user_id, game_id=game_id).all()
        for message in messages:
            if f"data-badge-id='{badge.id}'" in message.message:
                db.session.delete(message)
        db.session.commit()


def enhance_badges_with_task_info(badges, game_id=None, user_id=None):
    """
    Enhance each badge with aggregated task information from its awarding quests.
    If a game_id is provided, only quests in that game are considered.
    If user_id is provided, the function computes the maximum completions among those quests 
    and a flag indicating if any quest’s threshold is met.
    Returns a list of dictionaries with:
      - id, name, description, image, category,
      - task_names: comma‑separated quest titles,
      - task_ids: comma‑separated quest IDs,
      - badge_awarded_counts: comma‑separated thresholds,
      - user_completions: maximum completions among awarding quests,
      - is_complete: True if any quest’s threshold is met.
    """
    enhanced_badges = []
    for badge in badges:
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


def send_email(to: str,
               subject: str,
               html_content: str,
               inline_images: list[tuple[str, bytes, str]] | None = None) -> bool:
    """
    Send an e-mail (via the Postfix SMTP settings in Flask config).

    Parameters
    ----------
    to : str
        Recipient address.
    subject : str
        Mail subject line.
    html_content : str
        Fully-rendered HTML body *that already contains* <img src="cid:XXX"> tags.
    inline_images : list[tuple[cid, data, mime_subtype]]
        Optional list where each element is:
            cid           the Content-ID without angle brackets
            data          raw image bytes
            mime_subtype  e.g. 'jpeg', 'png', …

    Returns
    -------
    bool
        True if the message was sent without raising; False otherwise.
    """
    # Build a multipart/related mail so HTML can reference inline parts
    msg_root        = MIMEMultipart('related')
    msg_root['Subject'] = subject
    msg_root['From']    = current_app.config['MAIL_DEFAULT_SENDER']
    msg_root['To']      = to

    # The HTML part goes into a multipart/alternative container
    alt_part = MIMEMultipart('alternative')
    msg_root.attach(alt_part)
    alt_part.attach(MIMEText(html_content, 'html'))

    # Attach all requested inline images
    inline_images = inline_images or []
    for cid, data, subtype in inline_images:
        img = MIMEImage(data, _subtype=subtype)
        img.add_header('Content-ID', f'<{cid}>')
        img.add_header('Content-Disposition', 'inline', filename=f'{cid}.{subtype}')
        msg_root.attach(img)

    # ---------- SMTP plumbing (unchanged except for message variable) --------
    try:
        mail_server   = current_app.config.get('MAIL_SERVER')
        mail_port     = current_app.config.get('MAIL_PORT')
        use_tls       = current_app.config.get('MAIL_USE_TLS', False)
        use_ssl       = current_app.config.get('MAIL_USE_SSL', False)
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')

        smtp_conn = (
            smtplib.SMTP_SSL(mail_server, mail_port)
            if use_ssl else
            smtplib.SMTP(mail_server, mail_port)
        )
        smtp_conn.ehlo()
        if use_tls:
            smtp_conn.starttls()
            smtp_conn.ehlo()
        if mail_username and mail_password:
            smtp_conn.login(mail_username, mail_password)

        smtp_conn.sendmail(msg_root['From'], [to], msg_root.as_string())
        smtp_conn.quit()
        current_app.logger.info('Email sent successfully to %s.', to)
        return True

    except Exception as exc:          # pylint: disable=broad-except
        current_app.logger.error('Failed to send email: %s', exc)
        return False


def generate_demo_game():
    current_quarter = (datetime.now(utc).month - 1) // 3 + 1
    year = datetime.now(utc).year
    title = f"Demo Game - Q{current_quarter} {year}"

    existing_game = Game.query.filter_by(is_demo=True, title=title).first()
    if existing_game:
        return  # Just return, do nothing if the game already exists

    description = """
    Welcome to the newest Demo Game! Embark on a quest to create a more sustainable future while enjoying everyday activities, having fun, and fostering teamwork in the real-life battle against climate change.

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

    demo_game = Game(
        title=title,
        description=description,
        description2="Rules and guidelines for the demo game.",
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
        is_demo=True,
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
    db.session.add(demo_game)
    db.session.commit()

    # Import quests and badges for the demo game
    import_quests_and_badges_from_csv(demo_game.id, os.path.join(current_app.static_folder, 'defaultquests.csv'))

    # Add pinned message from admin
    try:
        admin_id = 1  # Assuming admin_id=1 is the system admin
        pinned_message = ShoutBoardMessage(
            message="Get on your Bicycle this Quarter!",
            user_id=admin_id,
            game_id=demo_game.id,
            is_pinned=True,
            timestamp=datetime.now(utc)
        )
        db.session.add(pinned_message)
        db.session.commit()
    except Exception as e:
        db.session.rollback()

    return demo_game


def import_quests_and_badges_from_csv(game_id, csv_path):
    try:
        with open(csv_path, mode='r', encoding='utf-8') as csv_file:
            data = csv.DictReader(csv_file)
            for row in data:
                badge_name = sanitize_html(row['badge_name'])
                badge_description = sanitize_html(row['badge_description'])
                
                # Generate the badge image filename if it's not provided
                if 'badge_image_filename' in row and row['badge_image_filename']:
                    badge_image_filename = row['badge_image_filename']
                else:
                    badge_image_filename = f"{badge_name.lower().replace(' ', '_')}.png"
                
                badge_image_path = os.path.join(current_app.static_folder, 'images', 'badge_images', badge_image_filename)

                if not os.path.exists(badge_image_path):
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
            db.session.commit()
    except Exception as e:
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
    game = Game.query.get(game_id)
    if not game:
        return []

    badges = Badge.query.join(Quest).filter(Quest.game_id == game_id, Quest.badge_id.isnot(None)).distinct().all()
    return badges


def send_social_media_liaison_email(game_id: int) -> bool:
    game = Game.query.get(game_id)
    if not game or not game.social_media_liaison_email:
        return False

    cutoff_time = game.last_social_media_email_sent or game.start_date

    submissions = (
        QuestSubmission.query
        .join(Quest)
        .filter(Quest.game_id == game_id,
                QuestSubmission.timestamp > cutoff_time)
        .order_by(QuestSubmission.timestamp.desc())
        .all()
    )
    if not submissions:
        return False

    html_parts   = [f"""
        <h1>New submissions for {game.title}</h1>
        <p><b>Time period:</b> {cutoff_time:%Y-%m-%d %H:%M} → {datetime.now(utc):%Y-%m-%d %H:%M}</p>
        <p><b>Total new submissions:</b> {len(submissions)}</p>
        <hr>
    """]
    inline_images: list[tuple[str, bytes, str]] = []

    for idx, sub in enumerate(submissions, start=1):
        quest = sub.quest
        user  = sub.submitter

        html_parts.append(f"""
            <div style="margin-bottom:1.5rem">
              <h3>{idx}. Quest: {quest.title}</h3>
              <p>User: {user.username} &nbsp;|&nbsp; Submitted: {sub.timestamp:%Y-%m-%d %H:%M}</p>
        """)
        if sub.comment:
            html_parts.append(f"<p><i>{sanitize_html(sub.comment)}</i></p>")

        if sub.image_url:
            # If it's already a fully-qualified URL, just embed directly
            if sub.image_url.startswith(('http://', 'https://')):
                html_parts.append(
                    f'<img src="{sub.image_url}" alt="submission image" '
                    f'style="max-width:300px;max-height:300px"><br>'
                )
            else:
                image_rel = sub.image_url.lstrip('/')
                if image_rel.startswith('static/'):
                    image_rel = image_rel[len('static/') :]
                image_path = os.path.join(current_app.static_folder, image_rel)
                try:
                    with open(image_path, 'rb') as f:
                        img_bytes = f.read()
                    ext = os.path.splitext(image_path)[1].lstrip('.') or 'png'
                    cid = f'submission_{sub.id}'
                    inline_images.append((cid, img_bytes, ext))
                    html_parts.append(
                        f'<img src="cid:{cid}" alt="submission image" '
                        f'style="max-width:300px;max-height:300px"><br>'
                    )
                except OSError:
                    # Fall back to a public URL using url_for('static', …)
                    with current_app.test_request_context():
                        public_url = url_for('static', filename=image_rel, _external=True)
                    html_parts.append(f'<img src="{public_url}" alt="submission image"><br>')

        html_parts.append("</div>")

    html_body = "<html><body>" + "\n".join(html_parts) + "</body></html>"
    subject = f"New submissions for {game.title} – {datetime.now(utc):%Y-%m-%d}"
    sent = send_email(game.social_media_liaison_email, subject, html_body, inline_images)
    if sent:
        game.last_social_media_email_sent = datetime.now(utc)
        db.session.commit()

    return sent


def _ensure_aware(dt):
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=utc)


def check_and_send_liaison_emails():
    """
    For every game with a liaison email, send on its schedule:
      'minute', 'daily', 'weekly', or 'monthly'.
    """
    try:
        now = datetime.now(utc)

        # Build your thresholds in one place
        interval_map = {
            'hourly':  timedelta(hours=1),
            'daily':   timedelta(days=1),
            'weekly':  timedelta(weeks=1),
            'monthly': timedelta(days=30),
        }

        games = Game.query.filter(Game.social_media_liaison_email.isnot(None)).all()

        for game in games:
            freq = (game.social_media_email_frequency or 'weekly').lower()
            threshold = interval_map.get(freq, timedelta(days=1))

            # coerce both dates to tz-aware UTC
            started = _ensure_aware(game.start_date)
            last    = _ensure_aware(game.last_social_media_email_sent) or started

            # first send: only if we've passed at least one threshold since start
            if not game.last_social_media_email_sent:
                if now - started >= threshold:
                    send_social_media_liaison_email(game.id)
                continue

            # subsequent sends
            if now - last >= threshold:
                send_social_media_liaison_email(game.id)

    except OperationalError as exc:
        current_app.logger.exception("DB error in liaison email job: %s", exc)
        db.session.rollback()        # safety first
    except SQLAlchemyError:
        db.session.rollback()
        raise                       # let apscheduler log the traceback
    finally:
        # <-- THIS is the important line
        db.session.remove()          # close / return the connection