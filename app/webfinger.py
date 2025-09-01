from flask import Blueprint, current_app, request, abort, Response, json
from app.models import db
from app.models.user import User
from urllib.parse import unquote, urlparse
import string

webfinger_bp = Blueprint('webfinger', __name__)

ALLOWED_USERNAME_CHARS = set(string.ascii_letters + string.digits + '_.-')
BOUNDARY_USERNAME_CHARS = set(string.ascii_letters + string.digits + '_')


def valid_username(name: str) -> bool:
    """Return True if ``name`` is a syntactically valid username."""
    if not name or len(name) > 64:
        return False
    if name[0] not in BOUNDARY_USERNAME_CHARS or name[-1] not in BOUNDARY_USERNAME_CHARS:
        return False
    return all(c in ALLOWED_USERNAME_CHARS for c in name)

@webfinger_bp.route('/.well-known/webfinger', methods=['GET'])
def webfinger():
    """Return a JRD document for ActivityPub WebFinger discovery.

    Supports both ``acct:user@host`` resources and the common practice of
    passing an HTTPS actor URL as the ``resource`` parameter.
    """
    raw = request.args.get('resource', '')
    resource = unquote(raw)

    host_cfg = (current_app.config['LOCAL_DOMAIN'] or '').lower()
    if resource.startswith('acct:'):
        # Standard acct:user@host form
        try:
            userpart, hostpart = resource[len('acct:'):].split('@', 1)
        except ValueError:
            abort(400, "Invalid acct format; expected acct:user@host")

        host = hostpart.lower().encode('idna').decode('ascii')
        if host != host_cfg:
            abort(404)

        if not valid_username(userpart):
            abort(400, "Invalid username syntax")
        username = userpart
    else:
        # Support resource being the actor URL (https://host/users/username)
        parsed = urlparse(resource)
        if parsed.scheme not in {'http', 'https'}:
            abort(400, "Invalid resource; expected acct: or https:// actor URL")
        host = parsed.netloc.lower()
        if host != host_cfg:
            abort(404)
        parts = [p for p in parsed.path.split('/') if p]
        if len(parts) < 2 or parts[0] != 'users':
            abort(400, "Unsupported actor URL; expected /users/<username>")
        username = parts[1]
        if not valid_username(username):
            abort(400, "Invalid username syntax")

    user = User.query.filter(
        db.func.lower(User.username) == username.lower()
    ).first_or_404()

                                                           
    actor_url   = f"https://{host}/users/{user.username}"
    profile_url = actor_url

                                                           
    if user.profile_picture:
        avatar_url = f"https://{host}/static/{user.profile_picture}"
    else:
        avatar_url = f"https://{host}/static/{current_app.config['PLACEHOLDER_IMAGE']}"

    jrd = {
        # Subject SHOULD be acct: form even when resource was an HTTPS URL
        "subject": f"acct:{user.username}@{host}",
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
