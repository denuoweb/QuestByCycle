import pytest

from app import create_app, db
from app.models.user import User, ActivityStore


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "LOCAL_DOMAIN": "example.com",
    })
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    yield app
    db.session.remove()
    db.drop_all()
    ctx.pop()


def test_activitypub_activities_delete_with_user(app):
    # Create two users
    u1 = User(username="apdel1", email="apdel1@example.com", license_agreed=True, email_verified=True)
    u2 = User(username="apdel2", email="apdel2@example.com", license_agreed=True, email_verified=True)
    db.session.add_all([u1, u2])
    db.session.commit()

    # Add stored ActivityPub activities for both users
    a1 = ActivityStore(user_id=u1.id, json={"type": "Create", "id": "u1:1"})
    a2 = ActivityStore(user_id=u1.id, json={"type": "Create", "id": "u1:2"})
    a3 = ActivityStore(user_id=u2.id, json={"type": "Create", "id": "u2:1"})
    db.session.add_all([a1, a2, a3])
    db.session.commit()

    assert ActivityStore.query.filter_by(user_id=u1.id).count() == 2
    assert ActivityStore.query.filter_by(user_id=u2.id).count() == 1

    # Delete u1 and ensure their activities are removed
    u1.delete_user()

    assert ActivityStore.query.filter_by(user_id=u1.id).count() == 0
    assert ActivityStore.query.filter_by(user_id=u2.id).count() == 1

