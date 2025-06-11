import pytest
from datetime import datetime, timezone
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
    db.drop_all()
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
    u = User(username="test", email="test@example.com", email_verified=True, license_agreed=True)
    u.set_password("secret")
    u.created_at = datetime.now(timezone.utc)
    db.session.add(u)
    db.session.commit()
    return u

def login(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)

def test_logout_clears_session(client, user):
    login(client, user)
    resp = client.get("/auth/logout", follow_redirects=False)
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert "_user_id" not in sess
