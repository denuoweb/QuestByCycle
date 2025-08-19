import pytest
from unittest.mock import patch
from app import create_app, db
from app.models.user import User, PushSubscription

@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "VAPID_PUBLIC_KEY": "testkey",
        "VAPID_PRIVATE_KEY": "privkey",
        "VAPID_ADMIN_EMAIL": "tester@example.com",
    })
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    yield app
    db.session.remove()
    ctx.pop()

@pytest.fixture
def client(app):
    return app.test_client()


def login(client):
    user = User(
        username="u",
        email="u@example.com",
        password_hash="x",
        license_agreed=True,
    )
    db.session.add(user)
    db.session.commit()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True

    from flask_login import login_user
    with client.application.test_request_context():
        login_user(user)
    return user


def test_public_key(client):
    login(client)
    resp = client.get("/push/public_key")
    assert resp.status_code == 200
    assert resp.get_json()["public_key"] == "testkey"


def test_subscribe_and_send(client):
    login(client)
    sub = {"endpoint": "https://example.com", "keys": {"p256dh": "a", "auth": "b"}}
    resp = client.post("/push/subscribe", json={"subscription": sub})
    assert resp.status_code == 200
    assert PushSubscription.query.count() == 1
    with patch("app.push.webpush") as wp:
        resp = client.post("/push/send", json={"title": "t", "body": "b"})
        assert resp.status_code == 200
        assert wp.called


def test_subscribe_rejects_bad_payload(client):
    login(client)
    resp = client.post(
        "/push/subscribe",
        json={"subscription": {"endpoint": "", "keys": {"p256dh": "", "auth": ""}}},
    )
    assert resp.status_code == 400
    assert PushSubscription.query.count() == 0
