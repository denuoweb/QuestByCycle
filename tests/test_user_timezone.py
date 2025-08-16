import pytest

from app import create_app, db
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


@pytest.fixture
def user(app):
    u = User(
        username="normal",
        email="normal@example.com",
        license_agreed=True,
        email_verified=True,
    )
    u.set_password("secret")
    db.session.add(u)
    db.session.commit()
    return u


def login(client, user):
    return client.post(
        "/auth/login",
        data={"email": user.email, "password": "secret"},
        follow_redirects=True,
    )


def test_timezone_endpoint_updates_user(client, user):
    login(client, user)
    resp = client.post(
        f"/profile/{user.id}/timezone",
        json={"timezone": "America/Chicago"},
    )
    assert resp.status_code == 200
    assert db.session.get(User, user.id).timezone == "America/Chicago"
