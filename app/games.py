# pylint: disable=import-error
import os
import base64
import bleach
import qrcode

from flask import (
    Blueprint, jsonify, render_template, request, redirect, url_for, flash,
    current_app, make_response
)
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from app.models import db, Game, Quest, UserQuest, user_games, User
from app.forms import GameForm
from app.utils import (
    save_leaderboard_image,
    generate_smoggy_images,
    allowed_image_file,
    send_social_media_liaison_email,
)
from io import BytesIO

ALLOWED_TAGS = [
    'a', 'b', 'i', 'u', 'em', 'strong', 'p', 'h1', 'h2', 'h3', 'h4', 'h5',
    'h6', 'blockquote', 'code', 'pre', 'br', 'div', 'span', 'ul', 'ol', 'li',
    'hr', 'sub', 'sup', 's', 'strike', 'font', 'img', 'video', 'figure'
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
    Sanitize the provided HTML content using bleach with allowed tags and attributes.
    """
    return bleach.clean(html_content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)


games_bp = Blueprint('games', __name__)


@games_bp.route('/create_game', methods=['GET', 'POST'])
@login_required
def create_game():
    """
    Create a new game using data from the submitted form.
    """
    form = GameForm()
    if form.validate_on_submit():
        game = Game(
            title=sanitize_html(form.title.data),
            description=sanitize_html(form.description.data),
            description2=sanitize_html(form.description2.data),
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            game_goal=form.game_goal.data,
            details=sanitize_html(form.details.data),
            awards=sanitize_html(form.awards.data),
            beyond=sanitize_html(form.beyond.data),
            twitter_username=sanitize_html(form.twitter_username.data),
            twitter_api_key=sanitize_html(form.twitter_api_key.data),
            twitter_api_secret=sanitize_html(form.twitter_api_secret.data),
            twitter_access_token=sanitize_html(form.twitter_access_token.data),
            twitter_access_token_secret=sanitize_html(
                form.twitter_access_token_secret.data
            ),
            facebook_app_id=sanitize_html(form.facebook_app_id.data),
            facebook_app_secret=sanitize_html(form.facebook_app_secret.data),
            facebook_access_token=sanitize_html(form.facebook_access_token.data),
            facebook_page_id=sanitize_html(form.facebook_page_id.data),
            is_public=form.is_public.data,
            allow_joins=form.allow_joins.data,
            social_media_liaison_email = sanitize_html(form.social_media_liaison_email.data),
            social_media_email_frequency = form.social_media_email_frequency.data,
            admin_id=current_user.id
        )
        if 'leaderboard_image' in request.files:
            image_file = request.files['leaderboard_image']
            if image_file and allowed_image_file(image_file.filename):
                try:
                    filename = save_leaderboard_image(image_file)
                    game.leaderboard_image = filename
                except ValueError as error:
                    flash(f'Error saving leaderboard image: {error}', 'error')
                    return render_template(
                        'create_game.html', title='Create Game', form=form
                    )
            else:
                flash('Invalid file type for leaderboard image', 'error')
                return render_template(
                    'create_game.html', title='Create Game', form=form
                )

        db.session.add(game)
        try:
            db.session.commit()
            if game.leaderboard_image:
                image_path = os.path.join(
                    current_app.root_path, 'static', game.leaderboard_image
                )
                generate_smoggy_images(image_path, game.id)
            flash('Game created successfully!', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        except SQLAlchemyError as error:
            db.session.rollback()
            flash(f'An error occurred while creating the game: {error}', 'error')
    return render_template('create_game.html', title='Create Game', form=form,
        in_admin_dashboard=True)


@games_bp.route('/update_game/<int:game_id>', methods=['GET', 'POST'])
@login_required
def update_game(game_id):
    """
    Update an existing game's information based on the submitted form data.
    """
    game = Game.query.get_or_404(game_id)
    form = GameForm(obj=game)
    if form.validate_on_submit():
        game.title = sanitize_html(form.title.data)
        game.description = sanitize_html(form.description.data)
        game.description2 = sanitize_html(form.description2.data)
        game.start_date = form.start_date.data
        game.end_date = form.end_date.data
        game.game_goal = form.game_goal.data
        game.details = sanitize_html(form.details.data)
        game.awards = sanitize_html(form.awards.data)
        game.beyond = sanitize_html(form.beyond.data)
        game.twitter_username = sanitize_html(form.twitter_username.data)
        game.twitter_api_key = sanitize_html(form.twitter_api_key.data)
        game.twitter_api_secret = sanitize_html(form.twitter_api_secret.data)
        game.twitter_access_token = sanitize_html(form.twitter_access_token.data)
        game.twitter_access_token_secret = sanitize_html(
            form.twitter_access_token_secret.data
        )
        game.facebook_app_id = sanitize_html(form.facebook_app_id.data)
        game.facebook_app_secret = sanitize_html(form.facebook_app_secret.data)
        game.facebook_access_token = sanitize_html(form.facebook_access_token.data)
        game.facebook_page_id = sanitize_html(form.facebook_page_id.data)
        game.instagram_user_id = sanitize_html(form.instagram_user_id.data)
        game.instagram_access_token = sanitize_html(form.instagram_access_token.data)
        game.is_public = form.is_public.data
        game.allow_joins = form.allow_joins.data
        game.social_media_liaison_email = sanitize_html(form.social_media_liaison_email.data)  
        game.social_media_email_frequency = form.social_media_email_frequency.data

        if ('leaderboard_image' in request.files and
                request.files['leaderboard_image'].filename):
            image_file = request.files['leaderboard_image']
            if image_file and allowed_image_file(image_file.filename):
                try:
                    filename = save_leaderboard_image(image_file)
                    game.leaderboard_image = filename

                    image_path = os.path.join(
                        current_app.root_path, 'static', game.leaderboard_image
                    )
                    generate_smoggy_images(image_path, game.id)
                except ValueError as error:
                    flash(f'Error saving leaderboard image: {error}', 'error')
                    return render_template(
                        'update_game.html',
                        form=form,
                        game_id=game_id,
                        leaderboard_image=game.leaderboard_image
                    )

        try:
            db.session.commit()
            flash('Game updated successfully!', 'success')
            return redirect(url_for('main.index', game_id=game_id))
        except SQLAlchemyError as error:
            db.session.rollback()
            flash(f'An error occurred while updating the game: {error}', 'error')
    return render_template(
        'update_game.html',
        form=form,
        game_id=game_id,
        leaderboard_image=game.leaderboard_image,
        in_admin_dashboard=True
    )


@games_bp.route('/send_liaison_email/<int:game_id>', methods=['POST'])
@login_required
def send_liaison_email(game_id):
    """Manually trigger sending of liaison emails for a game."""
    if not current_user.is_admin:
        flash('Access denied: Only administrators can send liaison emails.', 'danger')
        return redirect(url_for('main.index'))

    if send_social_media_liaison_email(game_id, fallback_to_last=True):
        flash('Liaison email sent successfully.', 'success')
    else:
        flash('No submissions available to email.', 'info')

    return redirect(url_for('games.update_game', game_id=game_id))


@games_bp.route('/register_game/<int:game_id>', methods=['POST'])
@login_required
def register_game(game_id):
    """
    Register the current user for the specified game.
    """
    try:
        game = Game.query.get_or_404(game_id)
        if game not in current_user.participated_games:
            stmt = user_games.insert().values(user_id=current_user.id,
                                              game_id=game_id)
            db.session.execute(stmt)
            db.session.commit()
            flash('You have successfully joined the game.', 'success')
        else:
            flash('You are already registered for this game.', 'info')
        return redirect(url_for('main.index', game_id=game_id))
    except SQLAlchemyError as error:
        db.session.rollback()
        current_app.logger.error(
            f'Failed to register user for game {game_id}: {error}'
        )
        flash('An error occurred. Please try again.', 'error')
    return redirect(url_for('main.index', game_id=game_id))


@games_bp.route('/delete_game/<int:game_id>', methods=['POST'])
@login_required
def delete_game(game_id):
    """
    Delete a game. Only administrators are allowed to delete games.
    Prior to deletion, ensure that users referencing the game have their selected_game_id set to NULL.
    """
    if not current_user.is_admin:
        flash('Access denied: Only administrators can delete games.', 'danger')
        return redirect(url_for('main.index'))

    game = Game.query.get_or_404(game_id)
    
    try:
        # Find all users that reference this game
        users_with_game = User.query.filter_by(selected_game_id=game.id).all()
        for user in users_with_game:
            user.selected_game_id = None  # Disassociate the game

        # Now delete the game after removing references
        db.session.delete(game)
        db.session.commit()
        flash('Game deleted successfully!', 'success')

    except SQLAlchemyError as error:
        db.session.rollback()
        flash(f'An error occurred while deleting the game: {error}', 'error')

    return redirect(url_for('admin.admin_dashboard'))


@games_bp.route('/game-info/<int:game_id>')
def game_info(game_id):
    """
    Display game information. If a 'modal' query parameter is provided,
    render a modal template; otherwise, render the full game info page.
    """
    game_obj = Game.query.get(game_id)
    if not game_obj:
        flash("Game details are not available.", "error")
        return redirect(url_for('main.index'))

    if request.args.get('modal'):
        return render_template(
            'modals/game_info_modal.html',
            game=game_obj,
            game_id=game_id
        )

    return render_template('game_info.html', game=game_obj, game_id=game_id)


@games_bp.route('/get_game_points/<int:game_id>', methods=['GET'])
@login_required
def get_game_points(game_id):
    """
    Get the total points awarded for a specific game along with its goal.
    """
    total_game_points = db.session.query(
        db.func.sum(UserQuest.points_awarded)
    ).join(
        Quest, UserQuest.quest_id == Quest.id
    ).filter(
        Quest.game_id == game_id
    ).scalar() or 0

    game = Game.query.get(game_id)
    game_goal = game.game_goal

    return jsonify(total_game_points=total_game_points, game_goal=game_goal)


@games_bp.route('/game/<int:game_id>/details')
@login_required
def game_details(game_id):
    """
    Render the details page for the specified game.
    """
    game = Game.query.get_or_404(game_id)
    return render_template('details.html', game=game)


@games_bp.route('/game/<int:game_id>/awards')
@login_required
def game_awards(game_id):
    """
    Render the awards page for the specified game.
    """
    game = Game.query.get_or_404(game_id)
    return render_template('awards.html', game=game)


@games_bp.route('/game/<int:game_id>/beyond')
@login_required
def game_beyond(game_id):
    """
    Render the 'beyond' page for the specified game.
    """
    game = Game.query.get_or_404(game_id)
    return render_template('beyond.html', game=game)


@games_bp.route('/join_custom_game', methods=['GET', 'POST'])
@login_required
def join_custom_game():
    """
    Allow a user to join a custom game using a game code.
    Never delete any existing participations—just add this game and select it.
    """
    raw_code = request.form.get('custom_game_code') or request.args.get('custom_game_code')
    game_code = sanitize_html(raw_code or '').strip()

    if not game_code:
        flash('Game code is required to join a custom game.', 'error')
        # Re-open the modal so they can pick again:
        return redirect(url_for('main.index', show_join_custom=1))

    game = Game.query.filter_by(custom_game_code=game_code, is_public=True).first()
    if not game:
        flash('Invalid game code. Please try again.', 'error')
        return redirect(url_for('main.index', show_join_custom=1))

    if not game.allow_joins:
        flash('This game does not allow new participants.', 'error')
        return redirect(url_for('main.index', show_join_custom=1))

    if game in current_user.participated_games:
        flash(f'You are already registered for {game.title}.', 'info')
        return redirect(url_for('main.index', game_id=game.id))

    # Register & select
    db.session.execute(
        user_games.insert().values(user_id=current_user.id, game_id=game.id)
    )
    current_user.selected_game_id = game.id
    db.session.commit()

    flash(f'You`ve joined {game.title}!', 'success')
    return redirect(url_for('main.index', game_id=game.id))


@games_bp.route('/join_demo')
@login_required
def join_demo():
    """
    Join the latest demo game—never deleting any other games,
    just add it and select it.
    """
    demo = Game.query.filter_by(is_demo=True) \
                     .order_by(Game.start_date.desc()) \
                     .first_or_404()

    # add demo if not already joined
    if demo not in current_user.participated_games:
        db.session.execute(
            user_games.insert().values(user_id=current_user.id, game_id=demo.id)
        )

    # select it
    current_user.selected_game_id = demo.id
    db.session.commit()

    flash('You’ve been added to the demo game.', 'info')
    return redirect(url_for('main.index', game_id=demo.id))


@games_bp.route('/generate_qr_for_game/<int:game_id>')
@login_required
def generate_qr_for_game(game_id):
    """
    Generate a QR code for a game login URL that includes a "next" parameter
    to redirect the user to the main index page with the appropriate game context.
    """
    # Retrieve the game object or return a 404 if not found
    game = Game.query.get_or_404(game_id)
    
    # Create the URL for the main index page with the desired game_id
    next_url = url_for('main.index', game_id=game_id, _external=True)
    
    # Build the login URL with a "next" parameter. This ensures that after login,
    # the user is redirected to the intended game page.
    login_url = url_for('auth.login', next=next_url, _external=True)
    
    # Generate the QR code using the login_url
    qr_code = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr_code.add_data(login_url)
    qr_code.make(fit=True)
    img = qr_code.make_image(fill_color="white", back_color="black")
    
    # Save the generated image to a buffer
    img_buffer = BytesIO()
    img.save(img_buffer, format="PNG")
    img_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    # Build the HTML content displaying the QR code
    html_content = (
        "<!DOCTYPE html>\n"
        "<html lang='en'>\n"
        "<head>\n"
        "    <meta charset='UTF-8'>\n"
        f"    <title>QR Code for {game.title}</title>\n"
        "    <style>\n"
        "        body { text-align: center; padding: 20px; font-family: Arial, sans-serif; }\n"
        "        .qrcodeHeader img { max-width: 100%; height: auto; }\n"
        "        h1, h2 { margin: 10px 0; }\n"
        "        img { margin-top: 20px; }\n"
        "        @media print { .no-print { display: none; } }\n"
        "    </style>\n"
        "</head>\n"
        "<body>\n"
        "    <div class='qrcodeHeader'>\n"
        f"        <img src='{url_for('static', filename='images/welcomeQuestByCycle.webp')}' alt='Welcome'>\n"
        "    </div>\n"
        "    <h1>Join the Game!</h1>\n"
        f"    <h2>Scan to join '{game.title}'!</h2>\n"
        f"    <img src='data:image/png;base64,{img_data}' alt='QR Code'>\n"
        "</body>\n"
        "</html>\n"
    )
    
    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html'
    return response


@games_bp.route('/get_game/<int:game_id>', methods=['GET'])
@login_required
def get_game(game_id):
    """
    Retrieve the game with the given game_id and return its title as JSON.
    """
    game = Game.query.get_or_404(game_id)
    return jsonify(name=game.title)
