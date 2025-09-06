import pytest
from datetime import datetime, timezone

from app import create_app, db
from app.models.game import Game
from app.models.quest import Quest, QuestSubmission
from app.models.user import User
from flask_login import login_user


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
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


def create_game(user):
    game = Game(
        title="G",
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc),
        timezone="UTC",
        admin_id=user.id,
    )
    game.admins.append(user)
    db.session.add(game)
    db.session.commit()
    return game


def test_quest_submissions_includes_quest_id(client):
    user = User(username="u", email="u@example.com", license_agreed=True, email_verified=True)
    user.set_password("pw")
    db.session.add(user)
    db.session.commit()

    login_as(client, user)

    game = create_game(user)
    quest = Quest(title="Q", game=game)
    db.session.add(quest)
    db.session.commit()

    sub = QuestSubmission(quest_id=quest.id, user_id=user.id)
    db.session.add(sub)
    db.session.commit()

    resp = client.get(f"/quests/quest/{quest.id}/submissions")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data and data[0]["quest_id"] == quest.id
