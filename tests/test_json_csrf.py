import pytest
from datetime import datetime, timezone

from app import create_app, db
from app.models.user import User


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "DEBUG": False,
        "WTF_CSRF_ENABLED": True,
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


@pytest.fixture
def user(app):
    u = User(
        username="tester",
        email="tester@example.com",
        license_agreed=True,
        email_verified=True,
    )
    u.set_password("secret")
    u.created_at = datetime.now(timezone.utc)
    db.session.add(u)
    db.session.commit()
    return u


def _login(client, user):
    token = client.get("/refresh-csrf").get_json()["csrf_token"]
    resp = client.post(
        "/auth/login",
        data={"email": user.email, "password": "secret"},
        headers={"X-CSRFToken": token, "X-Requested-With": "XMLHttpRequest"},
    )
    assert resp.status_code == 200
    return client.get("/refresh-csrf").get_json()["csrf_token"]


def test_json_endpoint_requires_csrf_header(client, user):
    token = _login(client, user)

    resp = client.post(f"/profile/{user.id}/messages", json={"content": "hi"})
    assert resp.status_code == 400
    assert resp.get_json()["message"] == "CSRF token missing or incorrect"

    resp = client.post(
        f"/profile/{user.id}/messages",
        json={"content": "hello"},
        headers={"X-CSRFToken": token},
    )
    assert resp.status_code == 201
