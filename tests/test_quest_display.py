import pytest
from datetime import datetime, timedelta
from pytz import utc

from app import create_app, db
from app.models import Game, User, Quest, QuestSubmission, Badge
from app.main import _prepare_quests

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


def test_prepare_quests_hides_unbadged_empty(app):
    with app.app_context():
        admin = User(username="admin", email="admin@example.com", license_agreed=True)
        admin.set_password("pw")
        db.session.add(admin)
        db.session.commit()

        game = Game(
            title="Test Game",
            start_date=datetime.now(utc) - timedelta(days=1),
            end_date=datetime.now(utc) + timedelta(days=1),
            admin_id=admin.id,
        )
        db.session.add(game)
        db.session.commit()

        badge = Badge(name="B")
        db.session.add(badge)
        db.session.commit()

        q1 = Quest(title="q1", game=game)
        q2 = Quest(title="q2", game=game, badge_id=badge.id)
        db.session.add_all([q1, q2])
        db.session.commit()

        sub = QuestSubmission(quest_id=q2.id, user_id=admin.id)
        db.session.add(sub)
        db.session.commit()

        quests, _ = _prepare_quests(game, admin.id, [], datetime.now(utc))
        ids = [q.id for q in quests]
        assert q1.id not in ids
        assert q2.id in ids
