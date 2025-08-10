from datetime import datetime, timedelta, timezone

import pytest
from bs4 import BeautifulSoup
from flask_login import login_user

from app import create_app, db
from app.models.game import Game
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


def test_create_game_highlights_current_admin(client):
    admin = User(
        username="admin",
        email="admin@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    admin.set_password("pw")
    db.session.add(admin)
    db.session.commit()

    login_as(client, admin)
    resp = client.get("/games/create_game")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    soup = BeautifulSoup(html, "html.parser")
    selected = {int(opt["value"]) for opt in soup.select("#admins option[selected]")}
    assert selected == {admin.id}


def test_update_game_highlights_existing_admins(client):
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

    game = Game(
        title="Game",
        admin_id=admin1.id,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
    )
    game.admins.extend([admin1, admin2])
    db.session.add(game)
    db.session.commit()

    login_as(client, admin1)
    resp = client.get(f"/games/update_game/{game.id}")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    soup = BeautifulSoup(html, "html.parser")
    selected = {int(opt["value"]) for opt in soup.select("#admins option[selected]")}
    assert selected == {admin1.id, admin2.id}
