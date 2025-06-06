# tests/test_auth_extra.py

import pytest
from flask import url_for
from app import create_app, db
from app.models import User
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
def normal_user(app):
    u = User(username="norm", email="norm@e.com", email_verified=True, license_agreed=True)
    u.set_password("pw")
    u.created_at = datetime.now(utc)
    db.session.add(u)
    db.session.commit()
    return u

@pytest.fixture
def admin_user(app):
    u = User(username="admin", email="admin@e.com", email_verified=True, license_agreed=True, is_admin=True)
    u.set_password("pw")
    u.created_at = datetime.now(utc)
    db.session.add(u)
    db.session.commit()
    return u

def login_as(client, user):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

def test_login_redirect_if_authenticated_next_safe(client, normal_user):
    login_as(client, normal_user)
    resp = client.get("/auth/login?next=/profile", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")

def test_login_redirect_if_authenticated_next_unsafe(client, normal_user):
    login_as(client, normal_user)
    resp = client.get("/auth/login?next=http://evil.com", follow_redirects=False)
    assert resp.status_code == 302
    expected = url_for("main.index", show_login=1, next="http://evil.com", _external=False)
    assert resp.headers["Location"].endswith(expected)

def test_unverified_email_non_ajax(client, app, normal_user):
    # mark user as unverified
    normal_user.email_verified = False
    db.session.commit()
    data = {"email": normal_user.email, "password": "pw"}
    resp = client.post("/auth/login", data=data, follow_redirects=False)
    assert resp.status_code == 302
    # should log in successfully and redirect to index with join modal closed
    assert resp.headers["Location"].endswith(url_for("main.index", show_join_custom=0, _external=False))

def test_successful_login_redirects_to_quest(client, normal_user):
    data = {"email": normal_user.email, "password": "pw"}
    resp = client.post("/auth/login?quest_id=123", data=data, follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(url_for("main.index", show_join_custom=0, _external=False))

def test_successful_login_redirects_admin_dashboard(client, admin_user):
    data = {"email": admin_user.email, "password": "pw"}
    resp = client.post("/auth/login", data=data, follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(url_for("main.index", show_join_custom=0, _external=False))

@pytest.mark.parametrize("ajax", [False, True])
def test_login_exception_paths(client, normal_user, monkeypatch, ajax):
    # force an exception during login_user()
    from app.auth import login_user
    monkeypatch.setattr("app.auth.login_user", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    data = {"email": normal_user.email, "password": "pw"}
    headers = {"X-Requested-With": "XMLHttpRequest"} if ajax else {}
    resp = client.post("/auth/login", data=data, headers=headers, follow_redirects=False)
    assert resp.status_code == 302
    expected_prefix = url_for("main.index", _external=False)
    assert resp.headers["Location"].startswith(expected_prefix)
