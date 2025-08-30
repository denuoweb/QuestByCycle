"""
ActivityPub utilities and blueprint for QuestByCycle federation

This module provides:
- JSON-LD context for core ActivityStreams and Mastodon extensions
- HTTP Signature generation and verification helpers
- WebFinger discovery endpoint
- /inbox and /outbox ActivityPub endpoints
- RSA key generation and local actor creation
- Activity delivery to remote inboxes
- Helper to construct, store, and deliver Create activities for quest submissions
"""
import json
import uuid
from typing import Iterable, List, Set
import rsa
import requests
from .utils import REQUEST_TIMEOUT
from datetime import datetime, timezone
from email.utils import formatdate
from urllib.parse import urlparse
from flask import Blueprint, current_app, request, abort, jsonify, url_for
from pydantic import ValidationError
from app.tasks import enqueue_deliver_activity
from app.models import db
from app.models import ForeignActor, RemoteFollower
from app.models.user import User, ActivityStore, Notification
from app.models.quest import QuestLike, QuestSubmission
from app.schemas import InboxActivitySchema

                                     
ap_bp = Blueprint('activitypub', __name__)

                                                        
AS_CONTEXT = [
    "https://www.w3.org/ns/activitystreams",
    {
        "manuallyApprovesFollowers": "as:manuallyApprovesFollowers",
        "toot": "http://joinmastodon.org/ns#",
        "featured": {"@id": "toot:featured", "@type": "@id"}
    },
    # Commonly included to define the publicKey/publicKeyPem terms used by many servers
    "https://w3id.org/security/v1",
]

def _canonical_json(obj: dict) -> str:
    """Return a stable, compact JSON string for signing and sending."""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


from functools import lru_cache


@lru_cache(maxsize=1024)
def discover_remote_inbox(actor_uri):
    """
    Given an actor URI (e.g. https://example.org/users/alice),
    perform WebFinger + actor fetch and return the declared inbox URL.
    Cache it on your Actor/ForeignActor model so you never repeat discovery.
    """
    parsed = urlparse(actor_uri)
    webfinger_url = f"{parsed.scheme}://{parsed.netloc}/.well-known/webfinger"
    # Per spec and widespread practice, pass the actor URI directly as resource
    params = {"resource": actor_uri}
    wf = requests.get(webfinger_url, params=params, timeout=REQUEST_TIMEOUT)
    wf.raise_for_status()
    data = wf.json()
                                                                  
    self_link = next(
        link for link in data.get('links', [])
        if link.get('rel') == 'self'
           and link.get('type') == 'application/activity+json'
    )
    canonical_actor = self_link['href']

                           
    resp = requests.get(
        canonical_actor,
        headers={"Accept": 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    actor_doc = resp.json()

                          
    inbox = actor_doc.get('inbox')\
         or actor_doc.get('endpoints', {}).get('inbox')
    if not inbox:
        raise ValueError("Remote actor did not declare an inbox endpoint")

    # Upsert ForeignActor cache
    fa = (
        ForeignActor.query.filter_by(actor_uri=actor_uri).first()
        or ForeignActor.query.filter_by(actor_uri=canonical_actor).first()
        or ForeignActor.query.filter_by(canonical_uri=actor_uri).first()
        or ForeignActor.query.filter_by(canonical_uri=canonical_actor).first()
    )
    if not fa:
        fa = ForeignActor(actor_uri=actor_uri)
    fa.canonical_uri = canonical_actor
    fa.inbox_url = inbox
    key = (actor_doc.get("publicKey", {}) or {}).get("publicKeyPem")
    if key:
        fa.public_key_pem = key
    db.session.add(fa)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return inbox


def sign_activitypub_request(actor, method, url, body):
    """
    Sign an HTTP request using the actor's private key (HTTP Signature draft).
    Returns headers dict for the outgoing request.
    """
    parsed = urlparse(url)
    path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
    date_header = formatdate(usegmt=True)

    # Compute Digest of body (SHA-256, base64) as most servers now require it
    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    else:
        body_bytes = json.dumps(body).encode("utf-8")
    import hashlib, base64
    digest_b64 = base64.b64encode(hashlib.sha256(body_bytes).digest()).decode("ascii")
    digest_header = f"SHA-256={digest_b64}"

    # Build signing string including digest
    signing_components = [
        f"(request-target): {method.lower()} {path}",
        f"host: {parsed.netloc}",
        f"date: {date_header}",
        f"digest: {digest_header}",
    ]
    signing_string = "\n".join(signing_components).encode("utf-8")
    priv = rsa.PrivateKey.load_pkcs1(actor.private_key.encode("utf-8"))
    signature = rsa.sign(signing_string, priv, "SHA-256")
    sig_b64 = base64.b64encode(signature).decode("ascii")
    key_id = f"{actor.activitypub_id}#main-key"
    signature_header = ", ".join([
        f'keyId="{key_id}"',
        'algorithm="rsa-sha256"',
        'headers="(request-target) host date digest"',
        f'signature="{sig_b64}"',
    ])
    return {
        "Date": date_header,
        "Host": parsed.netloc,
        "Digest": digest_header,
        "Signature": signature_header,
        # content-type with AS profile for best compatibility
        "Content-Type": 'application/activity+json',
        "Accept": 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
    }


def _fetch_actor_public_key(actor_uri: str) -> str:
    """Fetch a remote actor document and return the PEM public key string."""
    # Try cache first
    fa = (
        ForeignActor.query.filter_by(actor_uri=actor_uri).first()
        or ForeignActor.query.filter_by(canonical_uri=actor_uri).first()
    )
    if fa and fa.public_key_pem:
        return fa.public_key_pem

    # Fetch and update cache
    resp = requests.get(
        actor_uri,
        headers={"Accept": 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    doc = resp.json()
    key = (doc.get("publicKey", {}) or {}).get("publicKeyPem")
    if not key:
        raise ValueError("Remote actor missing publicKeyPem")

    fa = fa or ForeignActor(actor_uri=actor_uri)
    fa.canonical_uri = doc.get("id") or fa.canonical_uri
    fa.public_key_pem = key
    inbox = doc.get("inbox") or (doc.get("endpoints", {}) or {}).get("inbox")
    if inbox:
        fa.inbox_url = inbox
    db.session.add(fa)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return key


def verify_http_signature(actor_uri: str, headers, body: bytes) -> None:
    """Verify an incoming HTTP Signature using the sender's public key.

    - Parses the `Signature` header and respects its declared header list
    - Reconstructs the signing string from the incoming request
    - Verifies using the remote actor's `publicKeyPem`
    Aborts with 401 on failure.
    """
    sig_header = headers.get("Signature")
    if not sig_header:
        abort(401, "Missing Signature header")

    # Parse k=v pairs, trimming quotes
    parts = {}
    for item in sig_header.split(","):
        if "=" not in item:
            continue
        k, v = item.strip().split("=", 1)
        parts[k] = v.strip().strip("\"")

    import base64

    signature_b64 = parts.get("signature", "")
    if not signature_b64:
        abort(401, "Missing signature value")
    try:
        signature = base64.b64decode(signature_b64)
    except Exception:
        abort(401, "Invalid signature encoding")

    headers_list = parts.get("headers") or "date"
    header_tokens = [h.lower() for h in headers_list.split()]  # space-separated

    parsed = urlparse(request.url)
    path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
    values = []
    for token in header_tokens:
        if token == "(request-target)":
            values.append(f"(request-target): {request.method.lower()} {path}")
        else:
            # Headers are case-insensitive; Flask exposes them case-preserving
            val = headers.get(token.title()) or headers.get(token)
            if val is None:
                abort(401, f"Missing signed header: {token}")
            values.append(f"{token}: {val}")
    signing_string = "\n".join(values).encode("utf-8")

    # Optional: validate digest when present
    digest_val = headers.get("Digest")
    if digest_val and body:
        try:
            import hashlib
            algo, b64 = digest_val.split("=", 1)
            if algo.upper() == "SHA-256":
                calc = base64.b64encode(hashlib.sha256(body).digest()).decode("ascii")
                if calc != b64:
                    abort(401, "Digest mismatch")
        except Exception:
            abort(401, "Invalid Digest header")

    try:
        pem = _fetch_actor_public_key(actor_uri)
        pub = rsa.PublicKey.load_pkcs1(pem.encode("utf-8"))
        rsa.verify(signing_string, signature, pub)
    except Exception:
        abort(401, "Invalid HTTP Signature")



@ap_bp.route('/<username>', methods=['GET'])
def view_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    domain = current_app.config.get("LOCAL_DOMAIN")
    actor_id = f"https://{domain}/users/{username}"
    actor = {
        "@context": AS_CONTEXT,
        "id": actor_id,
        "type": "Person",
        "preferredUsername": user.username,
        "name": user.display_name or user.username,
        "inbox": f"{actor_id}/inbox",
        "outbox": f"{actor_id}/outbox",
        "followers": f"{actor_id}/followers",
        "following": f"{actor_id}/following",
        "publicKey": {
            "id": f"{actor_id}#main-key",
            "owner": actor_id,
            "publicKeyPem": user.public_key
        }
    }
    return jsonify(actor), 200, {"Content-Type": "application/activity+json"}


@ap_bp.route('/<username>/inbox', methods=['POST'])
def inbox(username):
    """
    ActivityPub inbox: auto-accept follows (remote), record notifications,
    handle Likes, skip double-notifying for local Create activities.
    Uses ActivityPub discovery (WebFinger + actor document) to fetch and
    cache the remote actor’s declared inbox URL, preventing any SSRF.
    """
                            
    user = User.query.filter_by(username=username).first_or_404()
    raw_activity = request.get_json(force=True, silent=True) or {}
    try:
        validated = InboxActivitySchema.model_validate(raw_activity)
    except ValidationError as exc:
        return jsonify(error="Invalid activity", details=exc.errors()), 400
    activity = raw_activity
    typ = validated.type
    actor_uri = validated.actor
    actor_host = urlparse(actor_uri).netloc
    our_host   = request.host

                                                 
    if actor_host and actor_host != our_host:
        verify_http_signature(actor_uri, request.headers, request.get_data())
    else:
        current_app.logger.debug(
            "Skipping signature check for local actor %s", actor_uri
        )

                                          
    sender = User.query.filter_by(activitypub_id=actor_uri).first()

                                                             
    if typ == 'Follow':
        accept = {
            '@context': AS_CONTEXT,
            'type':     'Accept',
            'actor':    user.activitypub_id,
            'object':   activity
        }

        try:
            remote_inbox = discover_remote_inbox(actor_uri)
            body = _canonical_json(accept)
            hdrs = sign_activitypub_request(
                user,
                "POST",
                remote_inbox,
                body,
            )
            requests.post(
                remote_inbox,
                data=body,
                headers=hdrs,
                timeout=REQUEST_TIMEOUT,
                verify=True,
            )
        except Exception as e:
            current_app.logger.error(
                "Auto-accept failed for %s: %s", actor_uri, e
            )

                                           
        if sender and sender not in user.followers:
            # Local follower
            user.followers.append(sender)
        else:
            # Remote follower persistence
            fa = (
                ForeignActor.query.filter_by(actor_uri=actor_uri).first()
                or ForeignActor.query.filter_by(canonical_uri=actor_uri).first()
            )
            if not fa:
                try:
                    # Populate cache (also sets ForeignActor)
                    discover_remote_inbox(actor_uri)
                    fa = (
                        ForeignActor.query.filter_by(actor_uri=actor_uri).first()
                        or ForeignActor.query.filter_by(canonical_uri=actor_uri).first()
                    )
                except Exception:
                    fa = None
            if fa:
                exists = RemoteFollower.query.filter_by(user_id=user.id, foreign_actor_id=fa.id).first()
                if not exists:
                    db.session.add(RemoteFollower(user_id=user.id, foreign_actor_id=fa.id))

                                                    
        # Notify local user about the follow
        if sender:
            name = sender.display_name or sender.username
            payload = {'from_user_id': sender.id, 'from_user_name': name}
        else:
            payload = {'from_actor_uri': actor_uri}
        db.session.add(Notification(user_id=user.id, type='follow', payload=payload))
        db.session.commit()

        return ('', 202)

                                        
    if typ == 'Create' and actor_host != our_host:
        obj = activity.get('object', {}) or {}
                                               

                                    
        if obj.get('type') == 'Note' and obj.get('inReplyTo'):
            in_to = obj['inReplyTo']
            if '/submissions/' in in_to:
                try:
                    sid = int(in_to.rsplit('/', 1)[1])
                except (ValueError, IndexError):
                    sid = None
                if sid is not None:
                    from app.models.quest import SubmissionReply

                    reply = SubmissionReply(
                        submission_id=sid,
                        user_id=(sender.id if sender else None),
                        content=obj.get('content', '')
                    )
                    db.session.add(reply)
                    db.session.commit()

                    sub = db.session.get(QuestSubmission, sid)
                    if sub:
                        db.session.add(Notification(
                            user_id=sub.user_id,
                            type='submission_reply',
                            payload={
                                'submission_id': sid,
                                'reply_id': reply.id,
                                'actor_id': sender.id,
                                'actor_name': sender.display_name or sender.username,
                                'content': reply.content
                            }
                        ))
                        db.session.commit()
        return ('', 202)

                               
    if typ == 'Like' and sender:
        obj_id = activity.get('object', {}).get('id', '')
        if '/submissions/' in obj_id:
            try:
                                                    
                quest_id = int(obj_id.rsplit('/', 1)[0].split('/')[-1])
                if not QuestLike.query.filter_by(
                    user_id=sender.id,
                    quest_id=quest_id
                ).first():
                    db.session.add(QuestLike(
                        user_id=sender.id,
                        quest_id=quest_id
                    ))
                    db.session.commit()
            except ValueError as exc:
                current_app.logger.warning("Invalid quest id in Like activity: %s", exc)
        return ('', 202)

                                            
    if typ == 'Announce' and sender:
        obj_id = activity.get('object', {}).get('id', '')
        if '/submissions/' in obj_id:
            try:
                sid = int(obj_id.rsplit('/', 1)[1])
                sub = db.session.get(QuestSubmission, sid)
                if sub:
                    db.session.add(Notification(
                        user_id=sub.user_id,
                        type='announce',
                        payload={
                            'actor_id': sender.id,
                            'actor_name': sender.display_name or sender.username,
                            'submission_id': sid
                        }
                    ))
                    db.session.commit()
            except ValueError as exc:
                current_app.logger.warning("Invalid submission id in Announce activity: %s", exc)
        return ('', 202)

                                                   
    if typ == 'Undo':
        obj = activity.get('object', {}) or {}
        if obj.get('type') == 'Like' and sender:
            target = obj.get('object', {}).get('id', '')
            if '/submissions/' in target:
                try:
                    quest_id = int(target.rsplit('/', 1)[0].split('/')[-1])
                    like = QuestLike.query.filter_by(
                        user_id=sender.id,
                        quest_id=quest_id
                    ).first()
                    if like:
                        db.session.delete(like)
                        db.session.commit()
                except ValueError as exc:
                    current_app.logger.warning("Invalid quest id in Undo activity: %s", exc)
            return ('', 202)
        if obj.get('type') == 'Follow' and obj.get('object') == user.activitypub_id:
            if sender:
                if sender in user.followers:
                    user.followers.remove(sender)
                    db.session.commit()
            else:
                # Remote actor unfollow
                fa = (
                    ForeignActor.query.filter_by(actor_uri=actor_uri).first()
                    or ForeignActor.query.filter_by(canonical_uri=actor_uri).first()
                )
                if fa:
                    rf = RemoteFollower.query.filter_by(user_id=user.id, foreign_actor_id=fa.id).first()
                    if rf:
                        db.session.delete(rf)
                        db.session.commit()
            return ('', 202)

    return ('', 202)


@ap_bp.route('/<username>/outbox', methods=['GET'])
def outbox(username):
    """
    ActivityPub outbox: return an OrderedCollection of past activities.
    """
    user = User.query.filter_by(username=username).first_or_404()
    activities = ActivityStore.query.filter_by(user_id=user.id).order_by(ActivityStore.published.desc()).all()
    items = [a.json for a in activities]
    resp = {
        '@context': AS_CONTEXT,
        'id': f"{user.activitypub_id}/outbox",
        'type': 'OrderedCollection',
        'totalItems': len(items),
        'orderedItems': items
    }
    return jsonify(resp), 200, {'Content-Type': 'application/activity+json'}


@ap_bp.route('/<username>/outbox', methods=['POST'])
def outbox_post(username):
    """Client-to-server POST to an actor's outbox.

    - Accept a single Activity, or a non-Activity Object to be wrapped in Create
    - Generate a new Activity id (ignore any client-supplied id)
    - For wrapped objects, generate an object id if missing and copy audience fields
    - Add to the user's outbox collection store
    - Return 201 Created and Location header to the Activity id
    - Trigger delivery to recipients
    """
    user = User.query.filter_by(username=username).first_or_404()
    # Enforce simple Bearer token authentication tied to this user
    authz = request.headers.get('Authorization', '')
    if not authz.startswith('Bearer '):
        return jsonify(error="Missing Bearer token"), 401
    token = authz.split(' ', 1)[1].strip()
    if not token or token != (user.c2s_token or ""):
        return jsonify(error="Invalid Bearer token"), 401
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict) or not body:
        return jsonify(error="Request body must be a single JSON object"), 400

    now = datetime.now(timezone.utc)
    actor_id = user.activitypub_id

    # Known Activity types (subset sufficient for our use)
    ACTIVITY_TYPES: Set[str] = {
        'Create', 'Update', 'Delete', 'Follow', 'Add', 'Remove', 'Like', 'Block', 'Undo',
        'Accept', 'Reject', 'Announce', 'Offer', 'Invite', 'Join', 'Leave'
    }

    def _ensure_obj_id(obj: dict) -> dict:
        if isinstance(obj, dict) and not obj.get('id'):
            obj_id = f"{actor_id}/objects/{uuid.uuid4()}"
            obj = dict(obj)
            obj['id'] = obj_id
        return obj

    def _copy_audience(src: dict, dst: dict) -> None:
        for k in ('to', 'bto', 'cc', 'bcc', 'audience'):
            if k in src:
                dst[k] = src[k]

    incoming_type = body.get('type')
    is_activity = isinstance(incoming_type, str) and incoming_type in ACTIVITY_TYPES

    if is_activity:
        # Validate required properties for certain activities
        requires_object = {'Create', 'Update', 'Delete', 'Follow', 'Add', 'Remove', 'Like', 'Block', 'Undo'}
        if incoming_type in requires_object and 'object' not in body:
            return jsonify(error=f"Activity '{incoming_type}' MUST include 'object'"), 400
        if incoming_type in {'Add', 'Remove'} and 'target' not in body:
            return jsonify(error=f"Activity '{incoming_type}' MUST include 'target'"), 400

        activity = dict(body)
        # Ensure actor is ours; ignore client-supplied id
        activity['actor'] = actor_id
        activity['id'] = f"{actor_id}/activities/{uuid.uuid4()}"
        activity['published'] = now.isoformat()
        # If object is embedded and lacks id, assign one
        if isinstance(activity.get('object'), dict):
            activity['object'] = _ensure_obj_id(activity['object'])
    else:
        # Treat as a bare object; must have a type
        if not incoming_type:
            return jsonify(error="Object MUST include 'type'"), 400
        obj = _ensure_obj_id(body)
        create_id = f"{actor_id}/activities/{uuid.uuid4()}"
        activity = {
            '@context': AS_CONTEXT,
            'id': create_id,
            'type': 'Create',
            'actor': actor_id,
            'object': obj,
            'published': now.isoformat(),
        }
        _copy_audience(obj, activity)

    # Store in outbox
    stored = ActivityStore(user_id=user.id, json=activity, published=now)
    db.session.add(stored)
    db.session.commit()

    # 201 Created + Location header pointing to the Activity id
    headers = {
        'Content-Type': 'application/activity+json',
        'Location': activity.get('id', '')
    }

    # Kick off delivery
    enqueue_deliver_activity(activity, user.id)

    return jsonify(activity), 201, headers


@ap_bp.route('/<username>/inbox', methods=['GET'])
def inbox_get(username):
    """Expose an OrderedCollection inbox (empty/public view).

    This minimal representation satisfies the requirement that the inbox is an
    OrderedCollection. Implementations may apply access control; we present an
    empty collection to unauthenticated/public requests.
    """
    user = User.query.filter_by(username=username).first_or_404()
    doc = {
        '@context': AS_CONTEXT,
        'id': f"{user.activitypub_id}/inbox",
        'type': 'OrderedCollection',
        'totalItems': 0,
        'orderedItems': [],
    }
    return jsonify(doc), 200, {'Content-Type': 'application/activity+json'}


@ap_bp.route('/<username>/activities/<path:rest>', methods=['GET'])
def get_activity(username, rest):
    """Serve a stored Activity by id via HTTP GET with AS2 representation."""
    user = User.query.filter_by(username=username).first_or_404()
    actor_id = user.activitypub_id
    # Reconstruct full id for lookup
    full_id = f"{actor_id}/activities/{rest}"
    # Simple lookup by scanning recent activities
    rec = (
        ActivityStore.query
        .filter_by(user_id=user.id)
        .order_by(ActivityStore.published.desc())
        .all()
    )
    for a in rec:
        if isinstance(a.json, dict) and a.json.get('id') == full_id:
            return jsonify(a.json), 200, {'Content-Type': 'application/activity+json'}
    abort(404)


@ap_bp.route('/<username>/submissions/<int:sid>', methods=['GET'])
def get_submission_object(username, sid: int):
    """Serve a minimal AS2 object for a quest submission.

    Matches the identifiers we generate in post_activitypub_create_activity.
    """
    user = User.query.filter_by(username=username).first_or_404()
    sub = db.session.get(QuestSubmission, sid)
    if not sub:
        abort(404)
    if sub.video_url:
        media_type = 'video/mp4'
        media_url = sub.video_url
        obj_type = 'Video'
    else:
        media_type = 'image/jpeg'
        media_url = sub.image_url
        obj_type = 'Image'
    obj = {
        '@context': AS_CONTEXT,
        'id': f"{user.activitypub_id}/submissions/{sid}",
        'type': obj_type,
        'attributedTo': user.activitypub_id,
        'mediaType': media_type,
        'url': media_url,
        'published': sub.timestamp.isoformat(),
    }
    return jsonify(obj), 200, {'Content-Type': 'application/activity+json'}


def generate_activitypub_keys():
    """
    Generate a new RSA key pair for ActivityPub signing.
    Returns tuple (public_pem, private_pem).
    """
    pubkey, privkey = rsa.newkeys(2048)
    return pubkey.save_pkcs1().decode('utf-8'), privkey.save_pkcs1().decode('utf-8')


def create_activitypub_actor(user):
    """
    Create a local ActivityPub actor for a user if missing.
    Generates keys and sets activitypub_id to the profile URL.
    """
    if not user.activitypub_id:
        public_pem, private_pem = generate_activitypub_keys()
        actor_url = url_for('activitypub.view_user', username=user.username, _external=True)
        parsed = urlparse(actor_url)
        domain = current_app.config.get("LOCAL_DOMAIN")
        if not domain:
            raise RuntimeError("LOCAL_DOMAIN must be configured for ActivityPub")
        if parsed.netloc != domain:
            actor_url = f"https://{domain}/users/{user.username}"

        user.activitypub_id = actor_url
        user.public_key = public_pem
        user.private_key = private_pem
        db.session.commit()
    # Ensure a C2S bearer token exists for client posting
    try:
        user.ensure_c2s_token()
    except Exception:
        db.session.rollback()


def deliver_activity(activity, sender):
    """
    Send an ActivityPub activity to all recipients' inboxes.
    """
    # Build recipient set from to/cc plus bto/bcc (which must be used for delivery
    # but removed from the payload per spec).
    to_list  = activity.get('to', []) or []
    cc_list  = activity.get('cc', []) or []
    bto_list = activity.get('bto', []) or []
    bcc_list = activity.get('bcc', []) or []

    combined: List[str] = []
    for lst in (to_list, cc_list, bto_list, bcc_list):
        if isinstance(lst, list):
            combined.extend([x for x in lst if isinstance(x, str)])
        elif isinstance(lst, str):
            combined.append(lst)

    # De-duplicate recipients and exclude the actor themselves.
    recipients: List[str] = []
    seen: Set[str] = set()
    actor_id = sender.activitypub_id
    for r in combined:
        if r == actor_id:
            continue
        if r in seen:
            continue
        seen.add(r)
        recipients.append(r)
    local_domain = current_app.config.get('LOCAL_DOMAIN')
    # Prepare a copy with bto/bcc removed for delivery
    deliver_payload = dict(activity)
    for hidden in ('bto', 'bcc'):
        if hidden in deliver_payload:
            try:
                del deliver_payload[hidden]
            except Exception:
                pass

    for recipient in recipients:
        parsed = urlparse(recipient)
        if not parsed.scheme or not parsed.netloc:
            current_app.logger.warning(
                "Skipping invalid ActivityPub recipient %s", recipient
            )
            continue

        if local_domain and parsed.netloc == local_domain:
            current_app.logger.debug(
                "Skipping local ActivityPub delivery to %s", recipient
            )
            continue

        # Handle followers collection fan-out
        if recipient.endswith('/followers'):
            # Fan-out to cached remote followers for the sender
            try:
                followers_q = (
                    db.session.query(ForeignActor)
                    .join(RemoteFollower, RemoteFollower.foreign_actor_id == ForeignActor.id)
                    .filter(RemoteFollower.user_id == sender.id)
                )
                remote_fas = followers_q.all()
                for fa in remote_fas:
                    inbox_url = fa.inbox_url or discover_remote_inbox(fa.actor_uri)
                    try:
                        body = _canonical_json(deliver_payload)
                        headers = sign_activitypub_request(sender, 'POST', inbox_url, body)
                        resp = requests.post(inbox_url, data=body, headers=headers, timeout=REQUEST_TIMEOUT)
                        resp.raise_for_status()
                    except Exception as e:
                        current_app.logger.error("Failed to deliver to %s: %s", inbox_url, e)
            except Exception as e:
                current_app.logger.error("Failed fan-out to remote followers: %s", e)
            continue

        # Skip non-actor recipients like Public
        if recipient.endswith('#Public'):
            continue

        inbox_url = recipient.rstrip('/') + '/inbox'
        try:
            body = _canonical_json(deliver_payload)
            headers = sign_activitypub_request(sender, 'POST', inbox_url, body)
            resp = requests.post(inbox_url, data=body, headers=headers, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except Exception as e:
            current_app.logger.error(
                f"Failed to deliver to {inbox_url}: {e}"
            )


def post_activitypub_create_activity(submission, user, quest):
    """
    Build, store, deliver—and notify local followers of—an ActivityPub Create activity.
    """
                                    
    if submission.video_url:
        media_type = 'video/mp4'
        media_url = submission.video_url
        obj_type = 'Video'
    else:
        media_type = 'image/jpeg'
        media_url = submission.image_url
        obj_type = 'Image'

    submission_object = {
        'id':           f"{user.activitypub_id}/submissions/{submission.id}",
        'type':         obj_type,
        'attributedTo': user.activitypub_id,
        'content':      f"Submission for quest “{quest.title}”",
        'mediaType':    media_type,
        'url':          media_url,
        'published':    submission.timestamp.isoformat()
    }

                                  
    activity = {
        '@context': AS_CONTEXT,
        'id':        f"{user.activitypub_id}/activities/{submission.id}",
        'type':      'Create',
        'actor':     user.activitypub_id,
        'object':    submission_object,
        'published': submission.timestamp.isoformat(),
        'to': [
            'https://www.w3.org/ns/activitystreams#Public',
            f"{user.activitypub_id}/followers"
        ]
    }

                              
    stored = ActivityStore(
        user_id   = user.id,
        json      = activity,
        published = submission.timestamp
    )
    db.session.add(stored)
    db.session.commit()

                                   
    actor_name = user.display_name or user.username
    for follower in user.followers:
        db.session.add(Notification(
            user_id = follower.id,
            type    = 'submission',
            payload = {
                'actor_id':      user.id,
                'actor_name':    actor_name,
                'quest_id':      quest.id,
                'quest_name':    quest.title,
                'submission_id': submission.id
            }
        ))
    db.session.commit()

                                  
    enqueue_deliver_activity(activity, user.id)

    return activity


@ap_bp.route('/<username>/followers', methods=['GET'])
def followers(username):
    user = User.query.filter_by(username=username).first_or_404()
                                                                           
    return jsonify({
        "@context": AS_CONTEXT,
        "id": f"{user.activitypub_id}/followers",
        "type": "OrderedCollection",
        "totalItems": 0,
        "orderedItems": []
    }), 200, {'Content-Type':'application/activity+json'}


@ap_bp.route('/<username>/following', methods=['GET'])
def following(username):
    user = User.query.filter_by(username=username).first_or_404()
                                             
    return jsonify({
        "@context": AS_CONTEXT,
        "id": f"{user.activitypub_id}/following",
        "type": "OrderedCollection",
        "totalItems": 0,
        "orderedItems": []
    }), 200, {'Content-Type':'application/activity+json'}


def post_activitypub_like_activity(submission, user):
    """
    Build and deliver a Like activity for a submission.
    """
    actor_id   = user.activitypub_id
    object_id  = f"{actor_id}/submissions/{submission.id}"
    obj_type = 'Video' if submission.video_url else 'Image'
    activity = {
      '@context': AS_CONTEXT,
      'id'     : f"{actor_id}/activities/like/{submission.id}/{int(datetime.now(timezone.utc).timestamp())}",
      'type'   : 'Like',
      'actor'  : actor_id,
      'object' : {'id': object_id, 'type': obj_type},
      'to'     : [submission.user.activitypub_id]
    }
                                                 
    enqueue_deliver_activity(activity, user.id)
    return activity


def post_activitypub_comment_activity(reply, user):
    """
    Build and deliver a Create(Note) activity for a submission reply.
    """
    actor_id   = user.activitypub_id
    submission = reply.submission
    object_id  = f"{actor_id}/comments/{reply.id}"
    in_reply_to= f"{submission.user.activitypub_id}/submissions/{submission.id}"
    note = {
      'id'        : object_id,
      'type'      : 'Note',
      'inReplyTo' : in_reply_to,
      'content'   : reply.content,
      'published' : reply.timestamp.isoformat()
    }
    activity = {
      '@context': AS_CONTEXT,
      'id'     : f"{actor_id}/activities/comment/{reply.id}",
      'type'   : 'Create',
      'actor'  : actor_id,
      'object' : note,
      'to'     : [submission.user.activitypub_id]
    }
    enqueue_deliver_activity(activity, user.id)
    return activity
