from datetime import datetime, timezone

import pytest

from app import create_app, db
from app.models import followers
from app.models.user import User, ProfileWallMessage


@pytest.fixture
def app():
    """Create and configure a new app instance for tests."""
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "MAIL_SERVER": None,
    })
    ctx = app.app_context()
    ctx.push()

    db.drop_all()
    db.create_all()

    yield app

    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture
def users(app):
    """Create two users for deletion tests."""
    u1 = User(
        username="deleteme",
        email="deleteme@example.com",
        license_agreed=True,
        email_verified=True,
    )
    u1.set_password("secret")
    u1.created_at = datetime.now(timezone.utc)

    u2 = User(
        username="other",
        email="other@example.com",
        license_agreed=True,
        email_verified=True,
    )
    u2.set_password("secret")
    u2.created_at = datetime.now(timezone.utc)

    db.session.add_all([u1, u2])
    db.session.commit()
    return u1, u2


def test_delete_user_removes_profile_messages(app, users):
    """Ensure deleting a user removes related profile wall messages."""
    u1, u2 = users

    msg1 = ProfileWallMessage(content="hi", user_id=u2.id, author_id=u1.id)
    msg2 = ProfileWallMessage(content="hello", user_id=u1.id, author_id=u2.id)
    db.session.add_all([msg1, msg2])
    db.session.commit()

    u1.delete_user()

    assert User.query.get(u1.id) is None
    assert ProfileWallMessage.query.filter_by(author_id=u1.id).count() == 0
    assert ProfileWallMessage.query.filter_by(user_id=u1.id).count() == 0
    assert User.query.get(u2.id) is not None


def test_delete_user_removes_followers(app, users):
    """Deleting a user should clear all follower relationships."""
    u1, u2 = users
    u1.following.append(u2)
    u2.following.append(u1)
    db.session.commit()

    assert db.session.execute(
        followers.select().where(
            (followers.c.follower_id == u1.id)
            | (followers.c.followee_id == u1.id)
        )
    ).fetchall()

    u1.delete_user()

    assert User.query.get(u1.id) is None
    remaining = db.session.execute(
        followers.select().where(
            (followers.c.follower_id == u1.id)
            | (followers.c.followee_id == u1.id)
        )
    ).fetchall()
    assert not remaining
