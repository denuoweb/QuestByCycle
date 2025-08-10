import pytest
from datetime import datetime, timezone, timedelta
from flask_login import login_user

from app import create_app, db
from app.models.user import User
from app.models.game import Game


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


def test_admin_dashboard_shows_only_associated_games(client):
    admin1 = User(
        username="admin1",
        email="admin1@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    admin1.set_password("pw")
    admin2 = User(
        username="admin2",
        email="admin2@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    admin2.set_password("pw")
    db.session.add_all([admin1, admin2])
    db.session.commit()

    game1 = Game(
        title="Game 1",
        admin_id=admin1.id,
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
    )
    game2 = Game(
        title="Game 2",
        admin_id=admin2.id,
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.session.add_all([game1, game2])
    db.session.commit()

    login_as(client, admin1)

    resp = client.get("/admin/admin_dashboard")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Game 1" in html
    assert "Game 2" not in html
