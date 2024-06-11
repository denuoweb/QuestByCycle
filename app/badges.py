from flask import Blueprint, current_app, render_template, flash, redirect, url_for, jsonify, request
from flask_login import login_required, current_user
from .forms import BadgeForm
from .utils import save_badge_image, allowed_file
from .models import db, Task, Badge, UserTask, Game
from werkzeug.utils import secure_filename

import bleach
import os
import csv

badges_bp = Blueprint('badges', __name__, template_folder='templates')

ALLOWED_TAGS = [
    'a', 'b', 'i', 'u', 'em', 'strong', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre', 'br', 'div', 'span', 'ul', 'ol', 'li', 'hr',
    'sub', 'sup', 's', 'strike', 'font', 'img', 'iframe', 'video', 'figure'
]

ALLOWED_ATTRIBUTES = {
    '*': ['class', 'style', 'id'],
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'width', 'height'],
    'iframe': ['src', 'width', 'height', 'frameborder', 'allow', 'allowfullscreen'],
    'video': ['src', 'width', 'height', 'controls'],
    'p': ['class', 'style'],
    'span': ['class', 'style'],
    'div': ['class', 'style'],
    'h1': ['class', 'style'],
    'h2': ['class', 'style'],
    'h3': ['class', 'style'],
    'h4': ['class', 'style'],
    'h5': ['class', 'style'],
    'h6': ['class', 'style'],
    'blockquote': ['class', 'style'],
    'code': ['class', 'style'],
    'pre': ['class', 'style'],
    'ul': ['class', 'style'],
    'ol': ['class', 'style'],
    'li': ['class', 'style'],
    'hr': ['class', 'style'],
    'sub': ['class', 'style'],
    'sup': ['class', 'style'],
    's': ['class', 'style'],
    'strike': ['class', 'style'],
    'font': ['color', 'face', 'size']
}

def sanitize_html(html_content):
    return bleach.clean(html_content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'csv'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@badges_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_badge():
    if not current_user.is_admin:
        flash('Access denied: Only administrators can manage badges.', 'danger')
        return redirect(url_for('main.index'))

    categories = db.session.query(Task.category).filter(Task.category != None).distinct().all()
    category_choices = [(category.category, category.category) for category in categories]
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


@badges_bp.route('/badges', methods=['GET'])
def get_badges():
    badges = Badge.query.all()
    badges_data = [{
        'id': badge.id,
        'name': badge.name,
        'description': badge.description,
        'image': url_for('static', filename='images/badge_images/' + badge.image) if badge.image else None,
        'category': badge.category
    } for badge in badges]
    return jsonify(badges=badges_data)


@badges_bp.route('/badges/manage_badges', methods=['GET', 'POST'])
@login_required
def manage_badges():
    if not current_user.is_admin:
        flash('Access denied: Only administrators can manage badges.', 'danger')
        return redirect(url_for('main.index'))

    categories = db.session.query(Task.category).filter(Task.category != None).distinct().all()
    category_choices = [(category.category, category.category) for category in categories]
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
    return render_template('manage_badges.html', form=form, badges=badges)


@badges_bp.route('/update/<int:badge_id>', methods=['POST'])
@login_required
def update_badge(badge_id):
    badge = Badge.query.get_or_404(badge_id)
    categories = db.session.query(Task.category).filter(Task.category != None).distinct().all()
    category_choices = [(category.category, category.category) for category in categories]
    form = BadgeForm(category_choices=category_choices)

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
    return jsonify({'success': False, 'message': 'Invalid form data'})


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
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting badge: {e}'}), 500


@badges_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = [category[0] for category in Badge.query.with_entities(Badge.category).distinct()]
    return jsonify(categories)


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
            # Extract filename and remove any directory path included by the browser
            filename = secure_filename(uploaded_file.filename.split('/')[-1])
            file_path = os.path.join(images_folder, filename)
            uploaded_file.save(file_path)

            # Convert filename to badge name
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

    print("bulk_upload function started")

    csv_file = request.files.get('csv_file')
    image_files = request.files.getlist('image_files')

    if csv_file:
        print(f"Received CSV file: {csv_file.filename}")
    else:
        print("No CSV file received")

    if image_files:
        print(f"Number of image files received: {len(image_files)}")
    else:
        print("No image files received")

    if not csv_file or not allowed_file(csv_file.filename):
        flash('Invalid or missing CSV file.', 'danger')
        print("Invalid or missing CSV file")
        return redirect(url_for('badges.manage_badges'))

    # Save images to a dictionary
    image_dict = {}
    for image_file in image_files:
        if allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(current_app.root_path, 'static', 'images', 'badge_images', filename)
            image_file.save(image_path)
            image_dict[filename] = filename
            print(f"Saved image: {filename} to {image_path}")

    # Process CSV
    try:
        csv_data = csv_file.read().decode('utf-8').splitlines()

        # Try with tab delimiter
        csv_reader = csv.DictReader(csv_data, delimiter='\t')
        headers = csv_reader.fieldnames
        print(f"CSV Headers with tab delimiter: {headers}")

        if headers is None or len(headers) == 1:
            # Try with comma delimiter
            csv_reader = csv.DictReader(csv_data, delimiter=',')
            headers = csv_reader.fieldnames
            print(f"CSV Headers with comma delimiter: {headers}")

        if 'badge_name' not in headers or 'badge_description' not in headers:
            raise ValueError("CSV file does not contain required headers: 'badge_name' and 'badge_description'")

        for row in csv_reader:
            print(f"Processing row: {row}")
            badge_name = row['badge_name']
            badge_description = row['badge_description']
            badge_filename = badge_name.lower().replace(' ', '_')
            badge_image = image_dict.get(f"{badge_filename}.png")

            if badge_image:
                new_badge = Badge(name=badge_name, description=badge_description, image=badge_image)
                db.session.add(new_badge)
                print(f"Added badge: {badge_name}")
            else:
                flash(f'Image for badge "{badge_name}" not found.', 'warning')
                print(f'Image for badge "{badge_name}" not found.')

    except Exception as e:
        print(f"Error processing CSV file: {e}")
        flash('Error processing CSV file.', 'danger')
        return redirect(url_for('badges.manage_badges'))

    db.session.commit()
    print("Database commit successful")
    flash('Badges and images uploaded successfully.', 'success')
    return redirect(url_for('badges.manage_badges'))