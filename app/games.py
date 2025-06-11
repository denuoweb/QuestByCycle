                              
import os
import base64
import qrcode

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    make_response,
    abort,
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
    sanitize_html,
)
from io import BytesIO


games_bp = Blueprint('games', __name__)

def serialize_game(game):
    """Return a dictionary representation of a ``Game``."""
    return {
        "id": game.id,
        "title": game.title,
        "name": game.title,
        "description": game.description,
        "start_date": game.start_date.isoformat() if game.start_date else None,
        "end_date": game.end_date.isoformat() if game.end_date else None,
        "game_goal": game.game_goal,
        "is_public": game.is_public,
        "allow_joins": game.allow_joins,
    }


def populate_game_from_form(game, form):
    """Populate ``game`` instance with sanitized form data."""
    sanitized_fields = [
        "title",
        "description",
        "description2",
        "details",
        "awards",
        "beyond",
        "twitter_username",
        "twitter_api_key",
        "twitter_api_secret",
        "twitter_access_token",
        "twitter_access_token_secret",
        "facebook_app_id",
        "facebook_app_secret",
        "facebook_access_token",
        "facebook_page_id",
        "instagram_user_id",
        "instagram_access_token",
        "social_media_liaison_email",
    ]

    raw_fields = [
        "start_date",
        "end_date",
        "game_goal",
        "is_public",
        "allow_joins",
        "social_media_email_frequency",
    ]

    for field in sanitized_fields:
        if hasattr(form, field):
            setattr(game, field, sanitize_html(getattr(form, field).data))

    for field in raw_fields:
        if hasattr(form, field):
            setattr(game, field, getattr(form, field).data)


def process_leaderboard_upload(game, defer=False):
    """Save leaderboard image from the request and optionally generate variants."""
    if (
        "leaderboard_image" not in request.files
        or not request.files["leaderboard_image"].filename
    ):
        return False

    image_file = request.files["leaderboard_image"]
    if not image_file or not allowed_image_file(image_file.filename):
        raise ValueError("Invalid file type for leaderboard image")

    filename = save_leaderboard_image(image_file)
    game.leaderboard_image = filename

    if not defer:
        image_path = os.path.join(current_app.root_path, "static", filename)
        generate_smoggy_images(image_path, game.id)

    return True



@games_bp.route('/create_game', methods=['GET', 'POST'])
@login_required
def create_game():
    """
    Create a new game using data from the submitted form.
    """
    form = GameForm()
    form.admins.choices = [
        (u.id, u.username) for u in User.query.filter_by(is_admin=True).all()
    ]
    if not form.admins.data:
        form.admins.data = [current_user.id]
    if form.validate_on_submit():
        game = Game()
        populate_game_from_form(game, form)
        game.admin_id = form.admins.data[0] if form.admins.data else current_user.id
        game.admins = User.query.filter(
            User.id.in_(form.admins.data or [current_user.id])
        ).all()
        try:
            process_leaderboard_upload(game, defer=True)
        except ValueError as error:
            flash(f'Error saving leaderboard image: {error}', 'error')
            return render_template('create_game.html', title='Create Game', form=form)

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
    game = db.session.get(Game, game_id)
    if not game:
        abort(404)
    if not current_user.is_admin_for_game(game_id):
        flash('Access denied: Only assigned admins can edit this game.', 'danger')
        return redirect(url_for('main.index'))
    form = GameForm(obj=game)
    form.admins.choices = [
        (u.id, u.username) for u in User.query.filter_by(is_admin=True).all()
    ]
    form.admins.data = [admin.id for admin in game.admins]
    if form.validate_on_submit():
        populate_game_from_form(game, form)
        game.admins = User.query.filter(User.id.in_(form.admins.data)).all()
        if form.admins.data:
            game.admin_id = form.admins.data[0]

        try:
            process_leaderboard_upload(game)
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
                                                 
        users_with_game = User.query.filter_by(selected_game_id=game.id).all()
        for user in users_with_game:
            user.selected_game_id = None                         

                                                       
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
    game_obj = db.session.get(Game, game_id)
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

    game = db.session.get(Game, game_id)
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
    demo = Game.query.filter_by(is_demo=True)\
                     .order_by(Game.start_date.desc())\
                     .first_or_404()

                                    
    if demo not in current_user.participated_games:
        db.session.execute(
            user_games.insert().values(user_id=current_user.id, game_id=demo.id)
        )

               
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
                                                           
    game = Game.query.get_or_404(game_id)
    
                                                                     
    next_url = url_for('main.index', game_id=game_id, _external=True)
    
                                                                                 
                                                       
    login_url = url_for('auth.login', next=next_url, _external=True)
    
                                              
    qr_code = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr_code.add_data(login_url)
    qr_code.make(fit=True)
    img = qr_code.make_image(fill_color="white", back_color="black")
    
                                          
    img_buffer = BytesIO()
    img.save(img_buffer, format="PNG")
    img_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
                                                   
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
def get_game(game_id):
    game = Game.query.get_or_404(game_id)
    return jsonify(serialize_game(game))
