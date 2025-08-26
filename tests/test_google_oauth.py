import pytest
from app import create_app, db
from app.models.user import User
from tests.helpers import url_for_path
from requests_oauthlib import OAuth2Session
from urllib.parse import urlparse

@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "GOOGLE_CLIENT_ID": "cid",
        "GOOGLE_CLIENT_SECRET": "secret",
        "OAUTH_USE_PKCE": "false",
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


def test_google_login_redirect(client):
    resp = client.get("/auth/login/google", follow_redirects=False)
    assert resp.status_code == 302
    location_host = urlparse(resp.headers["Location"]).hostname
    assert location_host == "accounts.google.com"
    with client.session_transaction() as sess:
        assert "google_oauth_state" in sess


def test_google_callback_creates_user(client, monkeypatch):
    def fake_fetch_token(self, token_url, *args, **kwargs):
        return {"access_token": "tok"}

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "sub": "123",
                "email": "foo@example.com",
                "name": "Foo",
                "picture": "http://example.com/pic.jpg",
            }

    def fake_get(self, url, timeout):
        return FakeResp()

    monkeypatch.setattr(OAuth2Session, "fetch_token", fake_fetch_token)
    monkeypatch.setattr(OAuth2Session, "get", fake_get)

    with client.session_transaction() as sess:
        sess["google_oauth_state"] = "abc"

    resp = client.get("/auth/google/callback?state=abc&code=xyz", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(
        url_for_path(client.application, "main.index", _external=False)
    )
    user = User.query.filter_by(email="foo@example.com").first()
    assert user is not None
    assert user.google_id == "123"
    with client.session_transaction() as sess:
        assert sess.get("_user_id") == str(user.id)
