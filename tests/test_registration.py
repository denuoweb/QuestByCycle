import pytest
from urllib.parse import urlparse, parse_qs

from app import create_app, db
from app.models import User
from flask import url_for
from datetime import datetime
from pytz import utc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

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

    # ensure clean slate
    try:
        db.drop_all()
    except Exception:
        pass
    db.create_all()

    yield app

    db.session.remove()
    try:
        db.drop_all()
    except Exception:
        pass
    ctx.pop()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def user_existing(app):
    u = User(
        username="existing",
        email="existing@example.com",
        license_agreed=True,
        email_verified=True,
    )
    u.set_password("secret")
    u.created_at = datetime.now(utc)
    db.session.add(u)
    db.session.commit()
    return u

# 1. GET should render registration modal via redirect

def test_register_get_shows_form(client):
    from urllib.parse import parse_qs, urlparse
    from flask import url_for

    resp = client.get("/auth/register", follow_redirects=False)
    assert resp.status_code == 302

    loc = resp.headers["Location"]
    # Should start with absolute URL for main.index
    assert loc.startswith(url_for("main.index"))

    qs = parse_qs(urlparse(loc).query)
    assert qs.get("show_register") == ["1"]

# 2. POST missing all data: should redirect back into the modal

def test_register_post_missing_data(client):
    from urllib.parse import urlparse, parse_qs
    from flask import url_for

    # Missing payload should redirect back into the modal
    resp = client.post("/auth/register", data={}, follow_redirects=False)
    assert resp.status_code == 302

    loc = resp.headers["Location"]
    # Redirect must go to main.index with show_register=1
    assert loc.startswith(url_for("main.index"))
    qs = parse_qs(urlparse(loc).query)
    assert qs.get("show_register") == ["1"]

# 3. POST without accepting license: should show warning

def test_register_post_without_license(client):
    from urllib.parse import urlparse, parse_qs
    from flask import url_for

    data = {
        "email": "newuser@example.com",
        "password": "password",
        "confirm_password": "password",
        # accept_license omitted
    }
    resp = client.post("/auth/register", data=data, follow_redirects=False)
    assert resp.status_code == 302

    loc = resp.headers["Location"]
    assert loc.startswith(url_for("main.index"))
    qs = parse_qs(urlparse(loc).query)
    assert qs.get("show_register") == ["1"]

# 4. POST with existing email: redirect back to register with flash

def test_register_existing_email(client, user_existing):
    data = {
        "email": user_existing.email,
        "password": "secret",
        "confirm_password": "secret",
        "accept_license": "y",
    }
    resp = client.post("/auth/register", data=data, follow_redirects=False)
    assert resp.status_code == 302
    loc = resp.headers["Location"]
    # Should redirect back to the registration endpoint
    assert loc.endswith('/auth/register')

# 5. POST valid registration without next/game/quest: default redirect

def test_register_success_default(client):
    data = {
        "email": "fresh@example.com",
        "password": "s3cr3t",
        "confirm_password": "s3cr3t",
        "accept_license": "y",
    }
    resp = client.post("/auth/register", data=data, follow_redirects=False)
    assert resp.status_code == 302
    loc = resp.headers["Location"]
    # Should redirect to index opening join modal
    assert url_for("main.index") in loc
    assert "show_join_custom=1" in loc
    assert "show_login=0" in loc

# 6. POST with next parameter: redirect to next

def test_register_with_next_param(client):
    data = {
        "email": "nxt@example.com",
        "password": "safepwd",
        "confirm_password": "safepwd",
        "accept_license": "y",
    }
    resp = client.post("/auth/register?next=/dashboard", data=data, follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/dashboard")

# 7. POST with game_id parameter: redirect into join custom with game_id

def test_register_with_game_id(client):
    from urllib.parse import urlparse, parse_qs

    data = {
        "email": "gamer@example.com",
        "password": "pw12345",
        "confirm_password": "pw12345",
        "accept_license": "y",
    }
    resp = client.post("/auth/register?game_id=42", data=data, follow_redirects=False)
    assert resp.status_code == 302
    loc = resp.headers["Location"]

    parsed = urlparse(loc)
    # Should route to /<game_id> with join modal parameters
    assert parsed.path == "/42"
    qs = parse_qs(parsed.query)
    assert qs.get("show_join_custom") == ["0"]
    assert qs.get("show_login") == ["0"]


# 8. POST with quest_id parameter: redirect to quest submission

def test_register_with_quest_id(client):
    data = {
        "email": "quester@example.com",
        "password": "questpwd",
        "confirm_password": "questpwd",
        "accept_license": "y",
    }
    resp = client.post("/auth/register?quest_id=99", data=data, follow_redirects=False)
    assert resp.status_code == 302
    loc = resp.headers["Location"]
    assert "/quests/submit_photo/" in loc or "/quests/submit_photo?quest_id=99" in loc

# 9. Simulate database commit failure: returns form with error flash

def test_register_db_failure(client, monkeypatch):
    """
    If the database commit fails, the registration view should flash an error
    and redirect back into the registration modal (show_register=1).
    """
    # Make db.session.commit() raise an error
    monkeypatch.setattr(db.session, "commit", lambda: (_ for _ in ()).throw(SQLAlchemyError("fail")))

    data = {
        "email": "err@example.com",
        "password": "errpwd",
        "confirm_password": "errpwd",
        "accept_license": "y",
    }
    # POST without following redirects so we can inspect the Location header
    resp = client.post("/auth/register", data=data, follow_redirects=False)
    assert resp.status_code == 302
    loc = resp.headers["Location"]

    # Should redirect to main.index with show_register=1
    from flask import url_for
    assert loc.startswith(url_for("main.index"))
    assert "show_register=1" in loc

    # We won't follow the redirect (avoid loop), just ensure the redirect is correct
    # Flash behavior is tested by other cases in integration/UI tests.
