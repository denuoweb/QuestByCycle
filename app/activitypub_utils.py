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
import rsa
import requests
from .utils import REQUEST_TIMEOUT
from datetime import datetime, timezone
from email.utils import formatdate
from urllib.parse import urlparse
from flask import Blueprint, current_app, request, abort, jsonify, url_for
from app.models import User, ActivityStore, QuestLike, db, Notification, QuestSubmission

                                     
ap_bp = Blueprint('activitypub', __name__)

                                                        
AS_CONTEXT = [
    "https://www.w3.org/ns/activitystreams",
    {
        "manuallyApprovesFollowers": "as:manuallyApprovesFollowers",
        "toot": "http://joinmastodon.org/ns#",
        "featured": {"@id": "toot:featured", "@type": "@id"}
    }
]


def discover_remote_inbox(actor_uri):
    """
    Given an actor URI (e.g. https://example.org/users/alice),
    perform WebFinger + actor fetch and return the declared inbox URL.
    Cache it on your Actor/ForeignActor model so you never repeat discovery.
    """
    from app.models import ForeignActor, db                                

                                             
    fa = ForeignActor.query.filter_by(actor_uri=actor_uri).first()
    if fa and fa.inbox_url:
        return fa.inbox_url

                  
    parsed = urlparse(actor_uri)
    webfinger_url = f"{parsed.scheme}://{parsed.netloc}/.well-known/webfinger"
    params = {'resource': f"acct:{parsed.path.strip('/')}"}
    wf = requests.get(webfinger_url, params=params, timeout=REQUEST_TIMEOUT)
    wf.raise_for_status()
    data = wf.json()
                                                                  
    self_link = next(
        link for link in data.get('links', [])
        if link.get('rel') == 'self'
           and link.get('type') == 'application/activity+json'
    )
    canonical_actor = self_link['href']

                           
    resp = requests.get(canonical_actor, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    actor_doc = resp.json()

                          
    inbox = actor_doc.get('inbox')\
         or actor_doc.get('endpoints', {}).get('inbox')
    if not inbox:
        raise ValueError("Remote actor did not declare an inbox endpoint")

                
    if not fa:
        fa = ForeignActor(actor_uri=actor_uri, canonical_uri=canonical_actor)
    fa.inbox_url = inbox
    db.session.add(fa)
    db.session.commit()
    return inbox


def sign_activitypub_request(actor, method, url, body):
    """
    Sign an HTTP request using the actor's private key (HTTP Signature draft).
    Returns headers dict for the outgoing request.
    """
    parsed = urlparse(url)
    path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
    date_header = formatdate(usegmt=True)
    signing_components = [
        f"(request-target): {method.lower()} {path}",
        f"host: {parsed.netloc}",
        f"date: {date_header}"
    ]
    signing_string = "\n".join(signing_components).encode('utf-8')
    priv = rsa.PrivateKey.load_pkcs1(actor.private_key.encode('utf-8'))
    signature = rsa.sign(signing_string, priv, 'SHA-256')
    sig_hex = signature.hex()
    key_id = f"{actor.activitypub_id}#main-key"
    signature_header = ", ".join([
        f'keyId="{key_id}"',
        'algorithm="rsa-sha256"',
        'headers="(request-target) host date"',
        f'signature="{sig_hex}"'
    ])
    return {
        'Date': date_header,
        'Host': parsed.netloc,
        'Signature': signature_header,
        'Content-Type': 'application/activity+json'
    }


def verify_http_signature(actor, headers, body):
    """
    Verify an incoming HTTP Signature as per the draft spec.
    Aborts 401 if invalid.
    """
    sig_header = headers.get('Signature')
    if not sig_header:
        abort(401, 'Missing Signature header')

                                         
    parts = dict(item.strip().split('=', 1) for item in sig_header.split(','))
    signature = bytes.fromhex(parts.get('signature', '').strip('"'))

                     
    pub = rsa.PublicKey.load_pkcs1(actor.public_key.encode('utf-8'))

                                    
    parsed = urlparse(request.url)
    path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
    request_target = f"{request.method.lower()} {path}"
    host = request.host                                 
    date = headers.get('Date')
    if not date:
        abort(401, 'Missing Date header')

    signing_components = [
        f"(request-target): {request_target}",
        f"host: {host}",
        f"date: {date}"
    ]
    signing_string = "\n".join(signing_components).encode('utf-8')

            
    try:
        rsa.verify(signing_string, signature, pub)
    except rsa.VerificationError:
        abort(401, 'Invalid HTTP Signature')



@ap_bp.route('/.well-known/webfinger', methods=['GET'])
def webfinger():
    """
    WebFinger discovery endpoint: responds to ?resource=acct:username@domain
    """
    resource = request.args.get('resource', '')
    if not resource.startswith('acct:'):
        return jsonify({'error': 'Invalid resource'}), 400
    acct = resource.split(':', 1)[1]
    try:
        username, domain = acct.split('@', 1)
    except ValueError:
        return jsonify({'error': 'Invalid acct format'}), 400
    if domain != current_app.config.get('LOCAL_DOMAIN'):
        return jsonify({'error': 'User not found'}), 404
    user = User.query.filter_by(username=username).first_or_404()
    actor_url = f"https://{domain}/users/{username}"
    resp = {
        'subject': resource,
        'links': [{
            'rel': 'self',
            'type': 'application/activity+json',
            'href': actor_url
        }]
    }
    return jsonify(resp), 200


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
                            
    user       = User.query.filter_by(username=username).first_or_404()
    activity   = request.get_json(force=True, silent=True) or {}
    typ        = activity.get('type')
    actor_uri  = activity.get('actor', '')
    actor_host = urlparse(actor_uri).netloc
    our_host   = request.host

                                                 
    if actor_host and actor_host != our_host:
        verify_http_signature(user, request.headers, request.get_data())
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

                                                   
            hdrs = sign_activitypub_request(
                user,
                'POST',
                remote_inbox,
                json.dumps(accept)
            )

                                                                       
            requests.post(
                remote_inbox,
                json=accept,
                headers=hdrs,
                timeout=REQUEST_TIMEOUT,
                verify=True,
            )
        except Exception as e:
            current_app.logger.error(
                "Auto-accept failed for %s: %s", actor_uri, e
            )

                                           
        if sender and sender not in user.followers:
            user.followers.append(sender)

                                                    
        if sender:
            name = sender.display_name or sender.username
            db.session.add(Notification(
                user_id = user.id,
                type    = 'follow',
                payload = {
                    'from_user_id':   sender.id,
                    'from_user_name': name
                }
            ))
            db.session.commit()

        return ('', 202)

                                        
    if typ == 'Create' and actor_host != our_host:
        obj = activity.get('object', {}) or {}
                                               

                                    
        if obj.get('type') == 'Note' and obj.get('inReplyTo'):
            in_to = obj['inReplyTo']
            if '/submissions/' in in_to:
                sid = int(in_to.rsplit('/',1)[1])
                                                
                from app.models import SubmissionReply
                reply = SubmissionReply(
                    submission_id=sid,
                    user_id=(sender.id if sender else None),
                    content=obj.get('content','')
                )
                db.session.add(reply)
                db.session.commit()
                                         
                sub = QuestSubmission.query.get(sid)
                if sub:
                    db.session.add(Notification(
                        user_id=sub.user_id,
                        type='submission_reply',
                        payload={
                          'submission_id': sid,
                          'reply_id'     : reply.id,
                          'actor_id'     : sender.id,
                          'actor_name'   : sender.display_name or sender.username,
                          'content'      : reply.content
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
            except ValueError:
                pass
        return ('', 202)

                                            
    if typ == 'Announce' and sender:
        obj_id = activity.get('object', {}).get('id', '')
        if '/submissions/' in obj_id:
            try:
                sid = int(obj_id.rsplit('/', 1)[1])
                sub = QuestSubmission.query.get(sid)
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
            except ValueError:
                pass
        return ('', 202)

                                                   
    if typ == 'Undo' and sender:
        obj = activity.get('object', {}) or {}
        if obj.get('type') == 'Like':
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
                except ValueError:
                    pass
            return ('', 202)
        if obj.get('type') == 'Follow' and obj.get('object') == user.activitypub_id:
            if sender in user.followers:
                user.followers.remove(sender)
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
        user.activitypub_id = actor_url
        user.public_key = public_pem
        user.private_key = private_pem
        db.session.commit()


def deliver_activity(activity, sender):
    """
    Send an ActivityPub activity to all recipients' inboxes.
    """
    recipients = activity.get('to', []) + activity.get('cc', [])
    local_domain = current_app.config.get('LOCAL_DOMAIN')
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

        inbox_url = recipient.rstrip('/') + '/inbox'
        try:
            headers = sign_activitypub_request(
                sender, 'POST', inbox_url, json.dumps(activity)
            )
            resp = requests.post(
                inbox_url,
                json=activity,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
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

                                  
    deliver_activity(activity, user)

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
      'to'     : [submission_attributed_actor := submission.user.activitypub_id]
    }
                                                 
    deliver_activity(activity, user)
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
    deliver_activity(activity, user)
    return activity