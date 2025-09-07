import pytest
from datetime import datetime, timedelta, timezone

from app import create_app, db
from app.models.game import Game
from app.models.quest import Quest, QuestSubmission
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


def test_album_requires_code(client, app):
    with app.app_context():
        admin = User(username="admin", email="admin@example.com", license_agreed=True)
        admin.set_password("pw")
        db.session.add(admin)
        db.session.commit()

        game = Game(
            title="Game",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc) + timedelta(days=1),
            admin_id=admin.id,
        )
        db.session.add(game)
        db.session.commit()

        quest = Quest(title="Quest", points=1, game=game)
        db.session.add(quest)
        db.session.commit()

        submission = QuestSubmission(quest_id=quest.id, user_id=admin.id)
        db.session.add(submission)
        db.session.commit()

        gid = game.id
        code = game.album_code

    resp = client.get(f"/quests/quest/all_submissions?game_id={gid}")
    assert resp.status_code == 403

    resp = client.get(f"/quests/quest/all_submissions?game_id={gid}&album_code={code}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["submissions"]) == 1


def test_quest_submissions_requires_code(client, app):
    with app.app_context():
        admin = User(username="admin", email="admin@example.com", license_agreed=True)
        admin.set_password("pw")
        db.session.add(admin)
        db.session.commit()

        game = Game(
            title="Game",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc) + timedelta(days=1),
            admin_id=admin.id,
        )
        db.session.add(game)
        db.session.commit()

        quest = Quest(title="Quest", points=1, game=game)
        db.session.add(quest)
        db.session.commit()

        submission = QuestSubmission(quest_id=quest.id, user_id=admin.id)
        db.session.add(submission)
        db.session.commit()

        qid = quest.id
        code = game.album_code

    resp = client.get(f"/quests/quest/{qid}/submissions")
    assert resp.status_code == 403

    resp = client.get(f"/quests/quest/{qid}/submissions?album_code={code}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
