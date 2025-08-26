from datetime import datetime, timedelta, timezone

import pytest
from flask_login import login_user

from app import create_app, db
from app.models import (
    Game,
    Quest,
    QuestSubmission,
    SubmissionLike,
    SubmissionReply,
    User,
)
from app.quests import delete_submission


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
def users(app):
    owner = User(
        username="owner",
        email="owner@example.com",
        license_agreed=True,
        email_verified=True,
    )
    owner.set_password("pw")
    owner.created_at = datetime.now(timezone.utc)

    other = User(
        username="other",
        email="other@example.com",
        license_agreed=True,
        email_verified=True,
    )
    other.set_password("pw")
    other.created_at = datetime.now(timezone.utc)

    db.session.add_all([owner, other])
    db.session.commit()
    return owner, other


def test_delete_submission_removes_related_records_and_media(app, users, monkeypatch):
    owner, other = users
    game = Game(
        title="G",
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
        admin_id=owner.id,
        timezone="UTC",
    )
    quest = Quest(title="Q", game=game)
    db.session.add_all([game, quest])
    db.session.commit()

    submission = QuestSubmission(
        quest_id=quest.id,
        user_id=owner.id,
        image_url="img",
        video_url="vid",
    )
    db.session.add(submission)
    db.session.commit()

    like = SubmissionLike(submission_id=submission.id, user_id=other.id)
    reply = SubmissionReply(submission_id=submission.id, user_id=other.id, content="hi")
    db.session.add_all([like, reply])
    db.session.commit()

    called = []

    def fake_delete(path):
        called.append(path)

    monkeypatch.setattr("app.quests.delete_media_file", fake_delete)

    with app.test_request_context():
        login_user(owner)
        response = delete_submission(submission.id)

    assert response.get_json()["success"] is True
    assert QuestSubmission.query.get(submission.id) is None
    assert SubmissionLike.query.count() == 0
    assert SubmissionReply.query.count() == 0
    assert called == ["img", "vid"]


def test_delete_submission_endpoint_accepts_post(app, users):
    owner, _ = users
    game = Game(
        title="G",
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
        admin_id=owner.id,
        timezone="UTC",
    )
    quest = Quest(title="Q", game=game)
    db.session.add_all([game, quest])
    db.session.commit()

    submission = QuestSubmission(quest_id=quest.id, user_id=owner.id)
    db.session.add(submission)
    db.session.commit()

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["_user_id"] = str(owner.id)
        resp = client.post(f"/quests/quest/delete_submission/{submission.id}")

    assert resp.status_code == 200
    assert resp.get_json()["success"] is True
    assert QuestSubmission.query.get(submission.id) is None
