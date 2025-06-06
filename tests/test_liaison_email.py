import pytest
from datetime import datetime, timedelta
from pytz import utc

from app import create_app, db
from app.models import Game, Quest, User, QuestSubmission
from app.utils import send_social_media_liaison_email


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


def test_liaison_email_respects_upload_to_socials(app, monkeypatch):
    captured = {}

    def fake_send_email(to, subject, html_content, inline_images=None):
        captured["html"] = html_content
        return True

    monkeypatch.setattr("app.utils.send_email", fake_send_email)

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
            social_media_liaison_email="liaison@example.com",
        )
        db.session.add(game)
        db.session.commit()

        quest = Quest(title="Quest 1", points=1, game=game)
        db.session.add(quest)
        db.session.commit()

        sharer = User(username="sharer", email="s@example.com", license_agreed=True, upload_to_socials=True)
        sharer.set_password("pw")
        nonsharer = User(username="private", email="p@example.com", license_agreed=True, upload_to_socials=False)
        nonsharer.set_password("pw")
        db.session.add_all([sharer, nonsharer])
        db.session.commit()

        sub1 = QuestSubmission(quest_id=quest.id, user_id=sharer.id, timestamp=datetime.now(utc))
        sub2 = QuestSubmission(quest_id=quest.id, user_id=nonsharer.id, timestamp=datetime.now(utc))
        db.session.add_all([sub1, sub2])
        db.session.commit()

        assert send_social_media_liaison_email(game.id)
        html = captured.get("html", "")
        assert "sharer" in html
        assert "private" not in html
