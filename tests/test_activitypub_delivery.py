import pytest
from unittest.mock import patch

from app import create_app, db
from app.models import User
from app.activitypub_utils import (
    deliver_activity,
    generate_activitypub_keys,
    sign_activitypub_request,
    create_activitypub_actor,
)


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "LOCAL_DOMAIN": "example.com",
    })
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    yield app
    db.session.remove()
    db.drop_all()
    ctx.pop()


def test_deliver_activity_skips_invalid_and_local(app):
    public, private = generate_activitypub_keys()
    user = User(
        username="sender",
        email="s@example.com",
        license_agreed=True,
        email_verified=True,
        activitypub_id="https://example.com/users/sender",
        public_key=public,
        private_key=private,
    )
    db.session.add(user)
    db.session.commit()

    activity = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "Create",
        "to": [
            "https:///users/bad",
            "https://example.com/users/local",
            "https://remote.test/users/remote",
        ],
    }

    with patch("app.activitypub_utils.requests.post") as mock_post:
        deliver_activity(activity, user)
        mock_post.assert_called_once()
        called_url = mock_post.call_args[0][0]
        assert called_url == "https://remote.test/users/remote/inbox"


def test_sign_request_returns_string(app):
    public, private = generate_activitypub_keys()
    user = User(
        username="header",
        email="header@example.com",
        license_agreed=True,
        email_verified=True,
        activitypub_id="https://example.com/users/header",
        public_key=public,
        private_key=private,
    )
    db.session.add(user)
    db.session.commit()

    headers = sign_activitypub_request(
        user,
        "POST",
        "https://remote.test/inbox",
        "{}",
    )
    assert isinstance(headers["Signature"], str)

def test_create_actor_uses_local_domain_when_server_name_blank(app):
    app.config["SERVER_NAME"] = ""
    user = User(
        username="fall",
        email="fall@example.com",
        license_agreed=True,
        email_verified=True,
    )
    db.session.add(user)
    db.session.commit()

    create_activitypub_actor(user)

    assert user.activitypub_id == "https://example.com/users/fall"


def test_ensure_actor_updates_missing_domain(app):
    user = User(
        username="old",
        email="old@example.com",
        license_agreed=True,
        email_verified=True,
        activitypub_id="https:///users/old",
    )
    db.session.add(user)
    db.session.commit()

    user.ensure_activitypub_actor()

    assert user.activitypub_id == "https://example.com/users/old"
    assert user.public_key and user.private_key
