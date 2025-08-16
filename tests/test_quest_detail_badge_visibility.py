import pytest
from datetime import datetime, timedelta, timezone

from app import create_app, db
from app.models.game import Game
from app.models.quest import Quest
from app.models.user import User
from flask_login import login_user


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


@pytest.fixture
def user(app):
    user = User(
        username="player",
        email="player@example.com",
        license_agreed=True,
        email_verified=True,
    )
    user.set_password("pw")
    db.session.add(user)
    db.session.commit()
    return user


def login_as(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
    with client.application.test_request_context():
        login_user(user)


def create_game(admin_id):
    game = Game(
        title="Test Game",
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
        admin_id=admin_id,
        timezone="UTC",
    )
    db.session.add(game)
    db.session.commit()
    game.admins.append(db.session.get(User, admin_id))
    db.session.commit()
    return game


def test_quest_detail_badgeless_game(client, user):
    game = create_game(user.id)
    quest = Quest(title="Q", game=game, badge_option="none")
    db.session.add(quest)
    db.session.commit()

    login_as(client, user)
    resp = client.get(f"/quests/detail/{quest.id}/user_completion")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["quest"]["badge_option"] == "none"
