from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from .models import db, ProfileWallMessage, User
from .main import user_profile
from sqlalchemy.exc import IntegrityError

import bleach

profile_bp = Blueprint('profile', __name__)

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

@profile_bp.route('/<int:user_id>/messages', methods=['POST'])
@login_required
def post_profile_message(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    content = bleach.clean(data.get('content'), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

    if not content:
        return jsonify({'error': 'Content is required.'}), 400

    message = ProfileWallMessage(content=content, user_id=user_id, author_id=current_user.id)
    db.session.add(message)
    db.session.commit()
    return jsonify({'success': 'Message posted successfully.', 'message': {
        'id': message.id,
        'content': message.content,
        'timestamp': message.timestamp,
        'author_id': message.author_id,
        'author': {'username': message.author.username}
    }}), 201


@profile_bp.route('/<int:user_id>/messages/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(user_id, message_id):
    message = ProfileWallMessage.query.get_or_404(message_id)
    
    if message.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'You do not have permission to delete this message.'}), 403
    
    try:
        db.session.delete(message)
        db.session.commit()
        return jsonify({'success': True}), 200
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'error': str(e.orig)}), 500


@profile_bp.route('/<int:user_id>/messages/<int:message_id>/reply', methods=['POST'])
@login_required
def post_reply(user_id, message_id):
    user = User.query.get_or_404(user_id)
    message = ProfileWallMessage.query.get_or_404(message_id)

    if not (
        current_user.id == user.id or
        current_user.id == message.author_id or
        current_user.id == message.user_id or
        (message.parent_id and current_user.id == ProfileWallMessage.query.get(message.parent_id).author_id)
    ):
        return jsonify({'error': 'You are not authorized to reply to messages on this profile.'}), 403

    data = request.get_json()
    content = bleach.clean(data.get('content'), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

    if not content:
        return jsonify({'error': 'Content is required.'}), 400

    reply = ProfileWallMessage(content=content, user_id=user_id, author_id=current_user.id, parent_id=message_id)
    db.session.add(reply)
    db.session.commit()
    return jsonify({'success': 'Reply posted successfully.', 'reply': {
        'id': reply.id,
        'content': reply.content,
        'timestamp': reply.timestamp,
        'author_id': reply.author_id,
        'author': {'username': reply.author.username},
        'parent_id': reply.parent_id
    }}), 201


@profile_bp.route('/<int:user_id>/messages/<int:message_id>/edit', methods=['POST'])
@login_required
def edit_message(user_id, message_id):
    message = ProfileWallMessage.query.get_or_404(message_id)
    
    if message.author_id != current_user.id:
        return jsonify({'error': 'Unauthorized access'}), 403

    data = request.get_json()
    new_content = bleach.clean(data.get('content'), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

    if not new_content:
        return jsonify({'error': 'Content is required.'}), 400

    message.content = new_content

    try:
        db.session.commit()
        return jsonify({'message': 'Message updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500