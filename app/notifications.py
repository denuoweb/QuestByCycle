from flask import Blueprint, render_template, jsonify
from flask_login import current_user, login_required
from app.models import Notification, db

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/', methods=['GET'])
@login_required
def index():
    # Fetch all notifications for this user
    notifs = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.timestamp.desc()).all()

    # Auto-mark any unread ones as read
    unread = [n for n in notifs if not n.is_read]
    if unread:
        for n in unread:
            n.is_read = True
        db.session.commit()

    return render_template('notifications.html', notifications=notifs)


@notifications_bp.route('/unread_count')
@login_required
def unread_count():
    n = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify(count=n)


@notifications_bp.route('/recent')
@login_required
def list_notifications():
    notes = (Notification.query
             .filter_by(user_id=current_user.id)
             .order_by(Notification.timestamp.desc())
             .limit(20))
    return jsonify([
        {
          'id':    n.id,
          'type':  n.type,
          'when':  n.timestamp.isoformat(),
          'payload': n.payload,
          'is_read': n.is_read
        } for n in notes
    ])

@notifications_bp.route('/<int:note_id>/read', methods=['POST'])
@login_required
def mark_read(note_id):
    n = Notification.query.get_or_404(note_id)
    if n.user_id != current_user.id:
        return jsonify(error="Forbidden"), 403
    n.is_read = True
    db.session.commit()
    return jsonify(success=True)
