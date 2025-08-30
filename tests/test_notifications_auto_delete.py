import pytest

from app import create_app, db
from app.models.user import User, Notification


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


def test_notifications_delete_with_user(app):
    u1 = User(username="n1", email="n1@example.com", license_agreed=True, email_verified=True)
    u2 = User(username="n2", email="n2@example.com", license_agreed=True, email_verified=True)
    db.session.add_all([u1, u2])
    db.session.commit()

    n1 = Notification(user_id=u1.id, type="t", payload={})
    n2 = Notification(user_id=u1.id, type="t", payload={})
    n3 = Notification(user_id=u2.id, type="t", payload={})
    db.session.add_all([n1, n2, n3])
    db.session.commit()

    assert Notification.query.filter_by(user_id=u1.id).count() == 2
    assert Notification.query.filter_by(user_id=u2.id).count() == 1

    u1.delete_user()

    assert Notification.query.filter_by(user_id=u1.id).count() == 0
    assert Notification.query.filter_by(user_id=u2.id).count() == 1

