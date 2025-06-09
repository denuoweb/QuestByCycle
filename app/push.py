from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from pywebpush import webpush, WebPushException
from app.models import db, PushSubscription
import json

push_bp = Blueprint('push', __name__)

@push_bp.route('/public_key')
@login_required
def public_key():
    return jsonify(public_key=current_app.config.get('VAPID_PUBLIC_KEY', ''))

@push_bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    data = request.get_json() or {}
    sub = data.get('subscription')
    if not sub:
        return jsonify(error='Invalid subscription'), 400
    endpoint = sub.get('endpoint')
    keys = sub.get('keys', {})
    p256dh = keys.get('p256dh')
    auth = keys.get('auth')
    if not endpoint or not p256dh or not auth:
        return jsonify(error='Incomplete subscription'), 400
    existing = PushSubscription.query.filter_by(user_id=current_user.id, endpoint=endpoint).first()
    if not existing:
        db.session.add(PushSubscription(user_id=current_user.id, endpoint=endpoint, p256dh=p256dh, auth=auth))
        db.session.commit()
    return jsonify(success=True)

@push_bp.route('/send', methods=['POST'])
@login_required
def send_push():
    data = request.get_json() or {}
    user_id = data.get('user_id', current_user.id)
    title = data.get('title', 'QuestByCycle')
    body = data.get('body', '')

    if current_user.id != user_id and not current_user.is_admin:
        return jsonify(error='Forbidden'), 403

    subs = PushSubscription.query.filter_by(user_id=user_id).all()
    vapid_private_key = current_app.config.get('VAPID_PRIVATE_KEY')
    vapid_claims = {"sub": f"mailto:{current_app.config.get('VAPID_ADMIN_EMAIL')}"}

    errors = []
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth}
                },
                data=json.dumps({"title": title, "body": body}),
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims
            )
        except WebPushException as exc:
            current_app.logger.error("Web push failed: %s", exc)
            errors.append(str(exc))
    if errors:
        return jsonify(success=False, errors=errors), 500
    return jsonify(success=True)
