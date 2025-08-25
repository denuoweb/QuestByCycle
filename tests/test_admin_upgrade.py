import pytest
from datetime import datetime, timezone, timedelta
from flask_login import login_user

from app import create_app, db
from app.models.user import User
@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "MAIL_SERVER": None,
    })
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    yield app
    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture
def client(app):
    return app.test_client()


def login_as(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
    with client.application.test_request_context():
        login_user(user)


def test_edit_profile_does_not_upgrade_admin(client):
    user = User(
        username="player",
        email="player@example.com",
        license_agreed=True,
        email_verified=True,
    )
    user.set_password("pw")
    db.session.add(user)
    db.session.commit()

    login_as(client, user)

    resp = client.post(
        f"/profile/{user.id}/edit",
        data={
            "display_name": "Player",
            "age_group": "adult",
            "interests": "cycling",
            "upgrade_to_admin": "y",
        },
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    assert resp.json["success"]

    db.session.refresh(user)
    assert not user.is_admin


def test_expired_admin_downgraded_on_request(client):
    user = User(
        username="admin1",
        email="admin1@example.com",
        license_agreed=True,
        email_verified=True,
        is_admin=True,
        admin_until=datetime.now(timezone.utc) - timedelta(days=1),
    )
    user.set_password("pw")
    db.session.add(user)
    db.session.commit()

    login_as(client, user)
    client.get(f"/profile/{user.id}")

    db.session.refresh(user)
    assert not user.is_admin

