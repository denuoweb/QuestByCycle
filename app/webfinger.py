from flask import Blueprint, current_app, request, abort, Response, json
from app.models import db, User
from urllib.parse import unquote
import re

webfinger_bp = Blueprint('webfinger', __name__)

USERNAME_RE = re.compile(
    r'^[A-Za-z0-9_]+(?:[A-Za-z0-9_.-]*[A-Za-z0-9_])?$'
)

@webfinger_bp.route('/.well-known/webfinger', methods=['GET'])
def webfinger():
    raw = request.args.get('resource','')
    if not raw.startswith('acct:'):
        abort(400, "Invalid resource; must start with acct:")
    resource = unquote(raw)

    try:
        userpart, hostpart = resource[len('acct:'):].split('@', 1)
    except ValueError:
        abort(400, "Invalid acct format; expected acct:user@host")

    host = hostpart.lower().encode('idna').decode('ascii')
    if host != current_app.config['LOCAL_DOMAIN'].lower():
        abort(404)

    if not USERNAME_RE.match(userpart) or len(userpart) > 64:
        abort(400, "Invalid username syntax")

    user = User.query.filter(
        db.func.lower(User.username) == userpart.lower()
    ).first_or_404()

                                                           
    actor_url   = f"https://{host}/users/{user.username}"
    profile_url = actor_url

                                                           
    if user.profile_picture:
        avatar_url = f"https://{host}/static/{user.profile_picture}"
    else:
        avatar_url = f"https://{host}/static/images/default_profile_picture.png"

    jrd = {
        "subject": f"acct:{userpart}@{host}",
        "aliases": [
            actor_url
        ],
        "links": [
            {
                "rel":  "http://webfinger.net/rel/profile-page",
                "type": "text/html",
                "href": profile_url
            },
            {
                "rel":  "self",
                "type": "application/activity+json",
                "href": actor_url
            },
            {
                "rel":  "self",
                "type": 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
                "href": actor_url
            },
            {
                "rel":  "http://webfinger.net/rel/avatar",
                "type": "image/png",
                "href": avatar_url
            }
        ]
    }

    return Response(
        json.dumps(jrd),
        status=200,
        mimetype="application/jrd+json"
    )
