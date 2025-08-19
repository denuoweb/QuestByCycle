from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from pywebpush import webpush, WebPushException
from pydantic import ValidationError

from app.models import db
from app.models.user import PushSubscription
from app.schemas import PushSubscribeSchema, PushSendSchema
import json

push_bp = Blueprint('push', __name__)

@push_bp.route('/public_key')
@login_required
def public_key():
    return jsonify(public_key=current_app.config.get('VAPID_PUBLIC_KEY', ''))

@push_bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    try:
        payload = PushSubscribeSchema.model_validate(request.get_json() or {})
    except ValidationError as exc:
        return jsonify(error="Invalid subscription", details=exc.errors()), 400

    sub = payload.subscription
    existing = PushSubscription.query.filter_by(
        user_id=current_user.id, endpoint=sub.endpoint
    ).first()
    if not existing:
        db.session.add(
            PushSubscription(
                user_id=current_user.id,
                endpoint=sub.endpoint,
                p256dh=sub.keys.p256dh,
                auth=sub.keys.auth,
            )
        )
        db.session.commit()
    return jsonify(success=True)

@push_bp.route('/send', methods=['POST'])
@login_required
def send_push():
    try:
        payload = PushSendSchema.model_validate(request.get_json() or {})
    except ValidationError as exc:
        return jsonify(error="Invalid payload", details=exc.errors()), 400

    user_id = payload.user_id or current_user.id
    title = payload.title
    body = payload.body

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
        current_app.logger.error("Errors occurred during web push: %s", errors)
        return jsonify(success=False, error="An internal error occurred while sending notifications."), 500
    return jsonify(success=True)
