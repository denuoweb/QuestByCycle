from datetime import datetime, timezone

import pytest

from app import create_app, db
from app.models import Game, User, Quest, Badge
from app.models.user import UserQuest


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "MAIL_SERVER": None,
        }
    )
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
        from flask_login import login_user
        login_user(user)


def create_user_and_game():
    user = User(
        username="u",
        email="u@example.com",
        license_agreed=True,
        email_verified=True,
    )
    user.set_password("pw")
    db.session.add(user)
    db.session.commit()
    game = Game(
        title="G",
        admin_id=user.id,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc),
    )
    db.session.add(game)
    db.session.commit()
    return user, game


def test_leaderboard_partial_no_badges(client):
    user, game = create_user_and_game()
    quest = Quest(title="Q", game=game, points=1)
    db.session.add(quest)
    db.session.commit()
    uq = UserQuest(user_id=user.id, quest_id=quest.id, completions=1, points_awarded=1)
    db.session.add(uq)
    db.session.commit()
    login_as(client, user)
    resp = client.get(f"/leaderboard_partial?game_id={game.id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["has_badges"] is False


def test_user_profile_no_badges(client):
    user, game = create_user_and_game()
    login_as(client, user)
    resp = client.get(f"/profile/{user.id}?game_id={game.id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["has_badges"] is False
    assert data["user"]["badges"] == []


def test_user_profile_has_badges(client):
    user, game = create_user_and_game()
    badge = Badge(name="B", description="d", image="b.png", game=game)
    db.session.add(badge)
    db.session.commit()
    login_as(client, user)
    resp = client.get(f"/profile/{user.id}?game_id={game.id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["has_badges"] is True
