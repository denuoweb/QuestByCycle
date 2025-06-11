from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from app.models import db
from app.models.user import Notification

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/unread_count')
@login_required
def unread_count():
    n = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify(count=n)


@notifications_bp.route('/recent')
@login_required
def list_notifications():
                                                                     
    Notification.query\
        .filter_by(user_id=current_user.id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()

                                   
    try:
        page     = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
    except ValueError:
        page, per_page = 1, 10

                 
    pagination = Notification.query\
        .filter_by(user_id=current_user.id)\
        .order_by(Notification.timestamp.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

                  
    return jsonify({
        'items': [
            {
                'id':       n.id,
                'type':     n.type,
                'when':     n.timestamp.isoformat(),
                'payload':  n.payload,
                'is_read':  n.is_read
            }
            for n in pagination.items
        ],
        'page':        pagination.page,
        'per_page':    pagination.per_page,
        'total_pages': pagination.pages,
        'total_items': pagination.total
    })

@notifications_bp.route('/<int:note_id>/read', methods=['POST'])
@login_required
def mark_read(note_id):
    n = Notification.query.get_or_404(note_id)
    if n.user_id != current_user.id:
        return jsonify(error="Forbidden"), 403
    n.is_read = True
    db.session.commit()
    return jsonify(success=True)
