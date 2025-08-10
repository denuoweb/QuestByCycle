import pytest
from datetime import datetime, timezone, timedelta
from flask_login import login_user

from app import create_app, db
from app.models.user import User
from app.models.game import Game
from app.constants import ADMIN_STORAGE_GB, ADMIN_RETENTION_DAYS


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


def test_user_upgrade_creates_isolated_admin(client):
    user = User(
        username="player",
        email="player@example.com",
        license_agreed=True,
        email_verified=True,
    )
    user.set_password("pw")
    other_admin = User(
        username="admin2",
        email="admin2@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    other_admin.set_password("pw")
    db.session.add_all([user, other_admin])
    db.session.commit()

    game2 = Game(
        title="Game 2",
        admin_id=other_admin.id,
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.session.add(game2)
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
    assert user.is_admin
    assert user.storage_limit_gb == ADMIN_STORAGE_GB
    assert user.data_retention_days == ADMIN_RETENTION_DAYS

    game1 = Game(
        title="Game 1",
        admin_id=user.id,
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.session.add(game1)
    db.session.commit()

    resp = client.get("/admin/admin_dashboard")
    html = resp.get_data(as_text=True)
    assert "Game 1" in html
    assert "Game 2" not in html

