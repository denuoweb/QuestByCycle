import json
import requests
from .utils import REQUEST_TIMEOUT, sanitize_html
from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user, login_required
from .models import db, ProfileWallMessage, User, Notification
from sqlalchemy.exc import IntegrityError
from app.activitypub_utils import sign_activitypub_request
from urllib.parse import urlparse
from threading import Thread

profile_bp = Blueprint('profile', __name__)


def _deliver_follow_activity(app, actor_url, activity, sender_id):
    """Background thread: fetch target’s actor doc and POST the activity."""
    with app.app_context():
        try:

            sender = db.session.get(User, sender_id)
            sender.ensure_activitypub_actor()

            doc = requests.get(actor_url, timeout=REQUEST_TIMEOUT).json()
            inbox = doc.get("inbox")
            if inbox:
                hdrs = sign_activitypub_request(sender, 'POST', inbox, json.dumps(activity))
                requests.post(
                    inbox,
                    json=activity,
                    headers=hdrs,
                    timeout=REQUEST_TIMEOUT,
                )
        except Exception as e:
            app.logger.error(
                "Failed to deliver ActivityPub activity to %s: %s", actor_url, e
            )


@profile_bp.route('/<int:user_id>/messages', methods=['POST'])
@login_required
def post_profile_message(user_id):
    User.query.get_or_404(user_id)
    data = request.get_json()
    content = sanitize_html(data.get('content'))

    if not content:
        return jsonify({'error': 'Content is required.'}), 400

    message = ProfileWallMessage(
        content=content,
        user_id=user_id,
        author_id=current_user.id
    )
    db.session.add(message)
    db.session.commit()

                                                               
    from app.models.user import Notification
    follower_ids = [u.id for u in current_user.followers]
    for fid in follower_ids:
        notif = Notification(
            user_id=fid,
            type='profile_message',
            payload={
                'profile_message_id': message.id,
                'from_user_id': current_user.id,
                'from_user_name': current_user.display_name or current_user.username,
                'profile_user_id': user_id,
                'content': message.content
            }
        )
        db.session.add(notif)
    db.session.commit()

    return jsonify({
        'success': 'Message posted successfully.',
        'message': {
            'id': message.id,
            'content': message.content,
            'timestamp': message.timestamp,
            'author_id': message.author_id,
            'author': {'username': message.author.username}
        }
    }), 201


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
    except IntegrityError:
        db.session.rollback()
        return


@profile_bp.route('/<int:user_id>/messages/<int:message_id>/reply', methods=['POST'])
@login_required
def post_reply(user_id, message_id):
    user = User.query.get_or_404(user_id)
    message = ProfileWallMessage.query.get_or_404(message_id)

    if not (
        current_user.id == user.id or
        current_user.id == message.author_id or
        current_user.id == message.user_id or
        (
            message.parent_id
            and current_user.id
            == db.session.get(ProfileWallMessage, message.parent_id).author_id
        )
    ):
        return jsonify({'error': 'You are not authorized to reply to messages on this profile.'}), 403

    data = request.get_json()
    content = sanitize_html(data.get('content'))
    if not content:
        return jsonify({'error': 'Content is required.'}), 400

    reply = ProfileWallMessage(
        content=content,
        user_id=user_id,
        author_id=current_user.id,
        parent_id=message_id
    )
    db.session.add(reply)
    db.session.commit()

                                                     
    from app.models.user import Notification
    follower_ids = [u.id for u in current_user.followers]
    for fid in follower_ids:
        notif = Notification(
            user_id=fid,
            type='profile_reply',
            payload={
                'reply_id': reply.id,
                'from_user_id': current_user.id,
                'from_user_name': current_user.display_name or current_user.username,
                'profile_user_id': user_id,
                'content': reply.content
            }
        )
        db.session.add(notif)
    db.session.commit()

    return jsonify({
        'success': 'Reply posted successfully.',
        'reply': {
            'id': reply.id,
            'content': reply.content,
            'timestamp': reply.timestamp,
            'author_id': reply.author_id,
            'author': {'username': reply.author.username},
            'parent_id': reply.parent_id
        }
    }), 201


@profile_bp.route('/<int:user_id>/messages/<int:message_id>/edit', methods=['POST'])
@login_required
def edit_message(user_id, message_id):
    message = ProfileWallMessage.query.get_or_404(message_id)
    
    if message.author_id != current_user.id:
        return jsonify({'error': 'Unauthorized access'}), 403

    data = request.get_json()
    new_content = sanitize_html(data.get('content'))

    if not new_content:
        return jsonify({'error': 'Content is required.'}), 400

    message.content = new_content

    try:
        db.session.commit()
        return jsonify({'message': 'Message updated successfully'})
    except Exception:
        db.session.rollback()
        return


def is_local_actor(actor_url):
    host = urlparse(actor_url).netloc
    locals = {
        current_app.config['LOCAL_DOMAIN'],
        '127.0.0.1:5000',
        'localhost:5000',
    }
    return host in locals


@profile_bp.route('/<string:username>/follow', methods=['POST'])
@login_required
def follow_user(username):
    target = User.query.filter_by(username=username).first_or_404()

                       
    if target.id == current_user.id:
        return jsonify(error="You can't follow yourself"), 400

                           
    if target in current_user.following:
        return jsonify(success=True, message="Already following"), 200

                                                               
    current_user.ensure_activitypub_actor()
    target.ensure_activitypub_actor()
    db.session.commit()

                                    
    current_user.following.append(target)
    db.session.commit()

    follower_name = current_user.display_name or current_user.username
    db.session.add(Notification(
        user_id = target.id,
        type    = 'followed_by',
        payload = {
            'follower_id':   current_user.id,
            'follower_name': follower_name
        }
    ))
    db.session.commit()

    db.session.add(Notification(
        user_id = current_user.id,
        type    = 'follow',
        payload = {
            'from_user_id':   target.id,
            'from_user_name': target.display_name or target.username
        }
    ))
    db.session.commit()

                                    
    activity = {
      "@context": "https://www.w3.org/ns/activitystreams",
      "type":      "Follow",
      "actor":     current_user.activitypub_id,
      "object":    target.activitypub_id
    }

                                                                      
    if not is_local_actor(target.activitypub_id):
        app_obj = current_app._get_current_object()
        Thread(
            target=_deliver_follow_activity,
            args=(app_obj, target.activitypub_id, activity, current_user.id),
            daemon=True
        ).start()
    else:
        current_app.logger.debug("Skipping HTTP delivery for local actor %s", username)

    return jsonify(success=True, message="Now following"), 200


@profile_bp.route('/<string:username>/unfollow', methods=['POST'])
@login_required
def unfollow_user(username):
    target = User.query.filter_by(username=username).first_or_404()

                         
    if target.id == current_user.id:
        return jsonify(error="Invalid operation"), 400

                                        
    if target not in current_user.following:
        return jsonify(success=True, message="Already not following"), 200

                   
    current_user.ensure_activitypub_actor()
    target.ensure_activitypub_actor()
    db.session.commit()

                             
    current_user.following.remove(target)
    db.session.commit()

                                          
    activity = {
      "@context": "https://www.w3.org/ns/activitystreams",
      "type":      "Undo",
      "actor":     current_user.activitypub_id,
      "object": {
        "type":  "Follow",
        "actor": current_user.activitypub_id,
        "object": target.activitypub_id
      }
    }

                                        
    if not is_local_actor(target.activitypub_id):
        app_obj = current_app._get_current_object()
        Thread(
            target=_deliver_follow_activity,
            args=(app_obj, target.activitypub_id, activity, current_user.id),
            daemon=True
        ).start()
    else:
        current_app.logger.debug("Skipping HTTP delivery for local actor %s", username)

    return jsonify(success=True, message="Unfollowed"), 200