import pytest
from datetime import datetime, timedelta, timezone

from app import create_app, db
from app.models.game import Game
from app.models.quest import Quest
from app.models.user import User, Notification


def login(client, user):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
    from flask_login import login_user
    with client.application.test_request_context():
        login_user(user)


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


def test_notification_created_on_completion(client, app):
    import app.quests as quests_module
    class _Naive(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.utcnow()

    quests_module.datetime = _Naive

    with app.app_context():
        user = User(username="u", email="u@example.com", license_agreed=True, email_verified=True)
        user.set_password("pw")
        db.session.add(user)
        db.session.commit()

        game = Game(
            title="G",
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow() + timedelta(days=1),
            admin_id=user.id,
        )
        game.admins.append(user)
        db.session.add(game)
        db.session.commit()

        quest = Quest(title="Q", game=game, verification_type="comment")
        db.session.add(quest)
        db.session.commit()

        login(client, user)
        resp = client.post(f"/quests/quest/{quest.id}/submit", data={"verificationComment": "done"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

        note = Notification.query.filter_by(user_id=user.id, type="quest_complete").first()
        assert note is not None
        assert note.payload["quest_id"] == quest.id
