"""
Badge related routes.
"""
from markupsafe import escape
import os
import csv
from flask import Blueprint, current_app, render_template, flash, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
from .forms import BadgeForm
                                                          
from .utils import save_badge_image
from .models import db, Quest, Badge, UserQuest, Game
from werkzeug.utils import secure_filename

badges_bp = Blueprint('badges', __name__, template_folder='templates')

def sanitize_html(html_content: str) -> str:
    return escape(html_content)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'csv'}
    return '.' in filename and\
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@badges_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_badge():
    if not current_user.is_admin:
        flash('Access denied: Only administrators can manage badges.', 'danger')
        return redirect(url_for('main.index'))

                                              
    quest_categories = db.session.query(Quest.category).filter(Quest.category.isnot(None)).distinct().all()

                                        
    category_choices = sorted([category.category for category in quest_categories])

    form = BadgeForm(category_choices=category_choices)

    if form.validate_on_submit():
        filename = None
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename != '':
                filename = save_badge_image(image_file)
        new_badge = Badge(
            name=sanitize_html(form.name.data),
            description=sanitize_html(form.description.data),
            image=filename,
            category=sanitize_html(form.category.data)
        )
        db.session.add(new_badge)
        db.session.commit()
        flash('Badge created successfully!', 'success')
        return redirect(url_for('badges.list_badges'))
    return render_template('create_badge.html', form=form)


@badges_bp.route('', methods=['GET'])
def get_badges():
    game_id = request.args.get('game_id', type=int)
    if game_id:
        game = Game.query.get(game_id)
        if not game:
            return jsonify(error="Game not found"), 404
                                                                       
        badges = Badge.query.join(Quest).filter(
            Quest.game_id == game_id,
            Quest.badge_id.isnot(None)
        ).distinct().all()
    else:
        badges = Badge.query.all()
    
    badges_data = []
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
            task_names = None
            task_ids = None
            badge_awarded_counts = "1"
        
                                       
                                                                                        
        is_complete = False
                                                                                  
                                                                
        user_completions_total = 0
        if awarding_quests and current_user.is_authenticated:
            completions_list = []
            for quest in awarding_quests:
                user_quest = UserQuest.query.filter_by(user_id=current_user.id, quest_id=quest.id).first()
                completions = user_quest.completions if user_quest else 0
                completions_list.append(completions)
                                                                                                       
                if completions >= quest.badge_awarded:
                    is_complete = True
            user_completions_total = max(completions_list) if completions_list else 0
        else:
            user_completions_total = 0
        
        badges_data.append({
            'id': badge.id,
            'name': badge.name,
            'description': badge.description,
            'image': url_for('static', filename='images/badge_images/' + badge.image) if badge.image else None,
            'category': badge.category,
            'task_names': task_names,
            'task_ids': task_ids,
            'badge_awarded_counts': badge_awarded_counts,
            'is_complete': is_complete,
            'user_completions': user_completions_total
        })
    
    return jsonify(badges=badges_data)


@badges_bp.route('/manage_badges', methods=['GET', 'POST'])
@login_required
def manage_badges():
    if not current_user.is_admin:
        flash('Access denied: Only administrators can manage badges.', 'danger')
        return redirect(url_for('main.index'))

                                              
    quest_categories = db.session.query(Quest.category).filter(Quest.category.isnot(None)).distinct().all()

                                        
    category_choices = sorted([category.category for category in quest_categories])

    form = BadgeForm(category_choices=category_choices)

    if form.validate_on_submit():
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename != '':
                filename = save_badge_image(image_file)
                new_badge = Badge(
                    name=sanitize_html(form.name.data),
                    description=sanitize_html(form.description.data),
                    image=filename,
                    category=sanitize_html(request.form['category'])
                )
                db.session.add(new_badge)
                db.session.commit()
                flash('Badge added successfully.', 'success')
            else:
                flash('No file selected for upload.', 'error')
        else:
            flash('No file part in the request.', 'error')

        return redirect(url_for('badges.manage_badges'))

    badges = Badge.query.all()
    return render_template('manage_badges.html', form=form, badges=badges,
        in_admin_dashboard=True)


@badges_bp.route('/update/<int:badge_id>', methods=['POST'])
@login_required
def update_badge(badge_id):
                                                                  
    badge = Badge.query.get_or_404(badge_id)
                                              
    quest_categories = db.session.query(Quest.category).filter(Quest.category.isnot(None)).distinct().all()

                                        
    category_choices = sorted([category.category for category in quest_categories])

    form = BadgeForm(category_choices=category_choices, formdata=request.form)

                              
    if form.validate_on_submit():

                                                       
        badge.name = sanitize_html(form.name.data)
        badge.description = sanitize_html(form.description.data)
        badge.category = sanitize_html(form.category.data)

                                        
        if badge.category == 'none':
            badge.category = None

                             
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename != '':
                badge.image = save_badge_image(image_file)
                                        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Badge updated successfully'})

    return jsonify({'success': False, 'message': 'Invalid form data', 'errors': form.errors})


@badges_bp.route('/delete/<int:badge_id>', methods=['DELETE'])
@login_required
def delete_badge(badge_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    badge = Badge.query.get(badge_id)
    if not badge:
        return jsonify({'success': False, 'message': 'Badge not found'}), 404
    try:
        db.session.delete(badge)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Badge deleted successfully'})
    except Exception:
        db.session.rollback()
        return


@badges_bp.route('/categories', methods=['GET'])
def get_quest_categories():
                                                
    quest_categories = db.session.query(Quest.category).filter(Quest.category.isnot(None)).distinct().all()
    categories = [category.category for category in quest_categories]
    return jsonify(categories=sorted(categories))


@badges_bp.route('/upload_images', methods=['POST'])
@login_required
def upload_images():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized access'}), 403

    uploaded_files = request.files.getlist('file')
    images_folder = os.path.join(current_app.root_path, 'static', 'images', 'badge_images')

    if not os.path.exists(images_folder):
        os.makedirs(images_folder)

    for uploaded_file in uploaded_files:
        if uploaded_file and allowed_file(uploaded_file.filename):
                                                                                    
            filename = secure_filename(uploaded_file.filename.split('/')[-1])
            file_path = os.path.join(images_folder, filename)
            uploaded_file.save(file_path)

                                            
            badge_name = ' '.join(word.capitalize() for word in filename.rsplit('.', 1)[0].replace('_', ' ').split())
            badge = Badge.query.filter_by(name=badge_name).first()
            if badge:
                badge.image = filename 
                
                db.session.commit()

    return jsonify({'success': True, 'message': 'Images uploaded successfully'})


@badges_bp.route('/bulk_upload', methods=['POST'])
@login_required
def bulk_upload():
    if not current_user.is_admin:
        flash('Access denied: Only administrators can manage badges.', 'danger')
        return redirect(url_for('main.index'))

    csv_file = request.files.get('csv_file')
    image_files = request.files.getlist('image_files')

    if not csv_file or not allowed_file(csv_file.filename):
        flash('Invalid or missing CSV file.', 'danger')
        return redirect(url_for('badges.manage_badges'))

                                 
    image_dict = {}
    for image_file in image_files:
        if allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(current_app.root_path, 'static', 'images', 'badge_images', filename)
            image_file.save(image_path)
            image_dict[filename] = filename
                 
    try:
        csv_data = csv_file.read().decode('utf-8').splitlines()

                                
        csv_reader = csv.DictReader(csv_data, delimiter='\t')
        headers = csv_reader.fieldnames
        if headers is None or len(headers) == 1:
                                      
            csv_reader = csv.DictReader(csv_data, delimiter=',')
            headers = csv_reader.fieldnames
        if 'badge_name' not in headers or 'badge_description' not in headers:
            raise ValueError("CSV file does not contain required headers: 'badge_name' and 'badge_description'")

        for row in csv_reader:
            badge_name = row['badge_name']
            badge_description = row['badge_description']
            badge_filename = badge_name.lower().replace(' ', '_')
            badge_image = image_dict.get(f"{badge_filename}.png")

            if badge_image:
                new_badge = Badge(name=badge_name, description=badge_description, image=badge_image)
                db.session.add(new_badge)
            else:
                flash(f'Image for badge "{badge_name}" not found.', 'warning')
                print(f'Image for badge "{badge_name}" not found.')

    except Exception:
        flash('Error processing CSV file.', 'danger')
        return redirect(url_for('badges.manage_badges'))

    db.session.commit()
    flash('Badges and images uploaded successfully.', 'success')
    return redirect(url_for('badges.manage_badges'))