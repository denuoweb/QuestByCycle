"""
Admin and Admin Dashboard related routes.
"""
import logging

from sqlalchemy import or_
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from app.models import db, user_games
from app.models.user import User, UserIP
from app.models.game import Game, Sponsor
from app.models.quest import QuestSubmission
from app.forms import SponsorForm, TIMEZONE_CHOICES
from app.utils.file_uploads import save_sponsor_logo
from app.utils import sanitize_html, get_int_param
from app.decorators import require_admin, require_super_admin

admin_bp = Blueprint('admin', __name__)

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

                                   


def create_super_admin(app):
    with app.app_context():

        default_super_admin_password = current_app.config['DEFAULT_SUPER_ADMIN_PASSWORD']
        default_super_admin_username = current_app.config['DEFAULT_SUPER_ADMIN_USERNAME']
        default_super_admin_email = current_app.config['DEFAULT_SUPER_ADMIN_EMAIL']

                                                    
        super_admin_user = User.query.filter_by(email=default_super_admin_email).first()
        
        if super_admin_user:
                                              
            super_admin_user.email_verified = True
            super_admin_user.is_admin = True
            super_admin_user.is_super_admin = True
            super_admin_user.license_agreed = True
            super_admin_user.set_password(default_super_admin_password)
        else:
                                           
            super_admin_user = User(
                username=default_super_admin_username, 
                email=default_super_admin_email,
                email_verified=True,
                is_admin=True,
                is_super_admin=True,
                license_agreed=True
            )
            super_admin_user.set_password(default_super_admin_password)
            super_admin_user.is_admin = True                
            super_admin_user.email_verified = True
            super_admin_user.license_agreed = True
                                               
            db.session.add(super_admin_user)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating or updating super admin user: {e}")


@admin_bp.route('/admin_dashboard')
@login_required
@require_admin
def admin_dashboard():
    if current_user.is_super_admin:
        games = Game.query.order_by(Game.title).all()
    else:
        games = Game.query.filter(
            or_(
                Game.admin_id == current_user.id,
                Game.admins.any(id=current_user.id)
            )
        ).order_by(Game.title).all()
    return render_template('admin_dashboard.html', in_admin_dashboard=True, games=games)


@admin_bp.route('/user_management', methods=['GET'])
@admin_bp.route('/user_management/game/<int:game_id>', methods=['GET'])
@login_required
@require_super_admin
def user_management(game_id=None):
    games = Game.query.all()                                           

                                                          
    selected_game = None
    if game_id:
        selected_game = db.session.get(Game, game_id)

                                                   
    if selected_game:
                                                                   
        users = User.query.join(User.participated_games).filter(Game.id == game_id).all()
    else:
                                                        
        users = User.query.outerjoin(User.participated_games).all()

                                                                                   
    user_game_scores = {}
    for user in users:
                                                
        user_games = user.participated_games
        user_game_scores[user.id] = {
            game.id: user.get_score_for_game(game.id) for game in user_games
        }

                                                
    return render_template(
        'user_management.html',
        users=users,
        games=games,
        selected_game=selected_game,
        user_game_scores=user_game_scores,
        in_admin_dashboard=True
    )


@admin_bp.route('/user_details/<int:user_id>', methods=['GET'])
@login_required
@require_super_admin
def user_details(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return

    return render_template('user_details.html', user=user)


@admin_bp.route('/update_user/<int:user_id>', methods=['POST'])
@login_required
@require_super_admin
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin.user_management'))

    user.username = sanitize_html(request.form.get('username'))
    user.email = sanitize_html(request.form.get('email'))
    user.is_admin = 'is_admin' in request.form
    user.is_super_admin = 'is_super_admin' in request.form
    user.license_agreed = 'license_agreed' in request.form
    user.score = request.form.get('score')
    user.display_name = sanitize_html(request.form.get('display_name'))
    user.profile_picture = request.form.get('profile_picture')
    user.age_group = sanitize_html(request.form.get('age_group'))
    user.interests = sanitize_html(request.form.get('interests'))
    user.email_verified = 'email_verified' in request.form

    try:
        db.session.commit()
        flash('User updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user: {e}")
        flash('An error occurred while updating the user.', 'error')
    return redirect(url_for('admin.user_management'))


@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@require_super_admin
def edit_user(user_id):
    logging.debug("Entered edit_user function with user_id: %s", user_id)
    
    user = db.session.get(User, user_id)
    if not user:
        logging.error("User not found with id: %s", user_id)
        flash('User not found', 'error')
        return redirect(url_for('admin.user_management'))
    
                                                                               
    user.riding_preferences = user.riding_preferences or []
    user.participated_games = user.participated_games or []
    user.badges = user.badges or []
    
    if request.method == 'POST':
        logging.debug("Received POST request with form data: %s", request.form)

        try:
                                               
            user.username = request.form.get('username')
            user.email = request.form.get('email')
            user.is_admin = 'is_admin' in request.form
            user.is_super_admin = 'is_super_admin' in request.form
            user.license_agreed = 'license_agreed' in request.form
            user.score = int(request.form.get('score') or 0)
            user.display_name = request.form.get('display_name')
            user.profile_picture = request.form.get('profile_picture')
            user.age_group = request.form.get('age_group')
            user.timezone = request.form.get('timezone')
            user.interests = request.form.get('interests')
            user.email_verified = 'email_verified' in request.form

                                                                  
            riding_preferences = request.form.get('riding_preferences')
            user.riding_preferences = riding_preferences.split(',') if riding_preferences else []
            user.ride_description = request.form.get('ride_description')
            user.bike_picture = request.form.get('bike_picture')
            user.bike_description = request.form.get('bike_description')
            user.upload_to_socials = 'upload_to_socials' in request.form
            user.upload_to_mastodon = 'upload_to_mastodon' in request.form
            user.show_carbon_game = 'show_carbon_game' in request.form
            user.onboarded = 'onboarded' in request.form

                                                 
            selected_game_id = request.form.get('selected_game_id')
            user.selected_game_id = int(selected_game_id) if selected_game_id else None

            logging.debug("Updated user object with new form data: %s", user)

            db.session.commit()
            logging.info("User with id %s updated successfully", user_id)
            flash('User updated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error("Error updating user: %s", e)
            flash(f'Error updating user: {e}', 'error')
            return redirect(url_for('admin.edit_user', user_id=user.id))

        return redirect(url_for('admin.edit_user', user_id=user.id))

                                                                                      
    try:
        participated_games = user.get_participated_games() or []
        logging.debug("Fetched participated games: %s", participated_games)
    except Exception as e:
        logging.error("Error fetching participated games for user %s: %s", user_id, e)
        participated_games = []

    try:
        user_submissions = QuestSubmission.query.filter_by(user_id=user_id).all() or []
        logging.debug("Fetched user submissions: %s", user_submissions)
    except Exception as e:
        logging.error("Error fetching user submissions for user %s: %s", user_id, e)
        user_submissions = []

    try:
        user_ips = UserIP.query.filter_by(user_id=user_id).all() or []
        logging.debug("Fetched user IP addresses: %s", user_ips)
    except Exception as e:
        logging.error("Error fetching user IPs for user %s: %s", user_id, e)
        user_ips = []

                                                                                           
    try:
        games = Game.query.all() or []
        logging.debug("Fetched all games for dropdown: %s", games)
    except Exception as e:
        logging.error("Error fetching games for dropdown: %s", e)
        games = []

    return render_template(
        'edit_user.html',
        user=user,
        participated_games=participated_games,
        user_submissions=user_submissions,
        user_ips=user_ips,
        games=games,
        timezone_choices=TIMEZONE_CHOICES,
    )

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@require_super_admin
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin.user_management'))

    try:
        user.delete_user()
        flash('User deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user: {e}")
        flash('An error occurred while deleting the user.', 'error')
    return redirect(url_for('admin.user_management'))


@admin_bp.route('/sponsors/edit/<int:sponsor_id>', methods=['GET', 'POST'])
@login_required
@require_admin
def edit_sponsor(sponsor_id):
    sponsor = Sponsor.query.get_or_404(sponsor_id)
    game_id = sponsor.game_id if sponsor.game_id else get_int_param('game_id')

    form = SponsorForm(obj=sponsor)
    form.game_id.data = game_id                                               

    if form.validate_on_submit():
                             
        if 'logo' in request.files and request.files['logo'].filename:
            image_file = request.files['logo']
            try:
                sponsor.logo = save_sponsor_logo(image_file, old_filename=sponsor.logo)
            except ValueError as e:
                flash(f"Error saving sponsor logo: {e}", 'error')
                return render_template('edit_sponsors.html', form=form, sponsor=sponsor, game_id=game_id)
        
                                      
        sponsor.name = sanitize_html(form.name.data)
        sponsor.website = sanitize_html(form.website.data)
        sponsor.description = sanitize_html(form.description.data)
        sponsor.tier = sanitize_html(form.tier.data)
        sponsor.game_id = game_id                             
        db.session.commit()
        flash('Sponsor updated successfully!', 'success')
        return redirect(url_for('admin.manage_sponsors', game_id=game_id))

    return render_template('edit_sponsors.html', form=form, sponsor=sponsor, game_id=game_id)



@admin_bp.route('/sponsors/delete/<int:sponsor_id>', methods=['POST'])
@login_required
@require_admin
def delete_sponsor(sponsor_id):

    game_id = get_int_param('game_id', source=request.form)

    sponsor = Sponsor.query.get_or_404(sponsor_id)
    db.session.delete(sponsor)
    try:
        db.session.commit()
        flash('Sponsor deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error occurred: {e}', 'danger')
    
                                                           
    return redirect(url_for('admin.manage_sponsors', game_id=game_id))



@admin_bp.route('/sponsors', methods=['GET'])
def sponsors():
    game_id = get_int_param('game_id')
    if game_id:
        sponsors = Sponsor.query.filter_by(game_id=game_id).all()
    else:
        sponsors = Sponsor.query.all()
    return render_template('modal/sponsors_modal.html', sponsors=sponsors, game_id=game_id)


@admin_bp.route('/admin/sponsors', methods=['GET', 'POST'])
@login_required
@require_admin
def manage_sponsors():

    game_id = get_int_param('game_id')
    if request.method == 'POST':
        game_id = get_int_param('game_id', source=request.form)

    form = SponsorForm()
    form.game_id.data = game_id                           

    if form.validate_on_submit():
        sponsor = Sponsor(
            name=sanitize_html(form.name.data),
            website=sanitize_html(form.website.data),
            description=sanitize_html(form.description.data),
            tier=sanitize_html(form.tier.data),
            game_id=game_id
        )

                             
        if 'logo' in request.files and request.files['logo'].filename:
            image_file = request.files['logo']
            try:
                sponsor.logo = save_sponsor_logo(image_file)
            except ValueError as e:
                flash(f"Error saving sponsor logo: {e}", 'error')
                return render_template('manage_sponsors.html', form=form, sponsors=[], game_id=game_id)

        db.session.add(sponsor)
        try:
            db.session.commit()
            flash('Sponsor added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while adding the sponsor: {e}', 'error')
        return redirect(url_for('admin.manage_sponsors', game_id=game_id))

    sponsors = Sponsor.query.filter_by(game_id=game_id).all() if game_id else Sponsor.query.all()
    return render_template('manage_sponsors.html', form=form, sponsors=sponsors, game_id=game_id)


@admin_bp.route('/user_emails', methods=['GET'])
@login_required
@require_super_admin
def user_emails():
    games = Game.query.all()
    game_email_map = {}

                                          
    for game in games:
        users = User.query.join(user_games).filter(user_games.c.game_id == game.id).all()
        game_email_map[game.title] = [user.email for user in users]

    return render_template('user_emails.html', game_email_map=game_email_map, games=games)
