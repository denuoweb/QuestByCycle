                    
import pytest
from urllib.parse import urlparse, parse_qs

from app import create_app, db
from app.models.user import User
from flask import url_for
from datetime import datetime, timezone

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
def user_normal(app):
    """A normal, email-verified user with password 'secret'."""
    u = User(
        username="normal",
        email="normal@example.com",
        license_agreed=True,
        email_verified=True,
    )
    u.set_password("secret")
                                             
    u.created_at = datetime.now(timezone.utc)
    db.session.add(u)
    db.session.commit()
    return u

@pytest.fixture
def user_unverified(app):
    """A user who exists but has not verified their email."""
    u = User(
        username="unverified",
        email="unverified@example.com",
        license_agreed=True,
        email_verified=False,
    )
    u.set_password("secret")
    u.created_at = datetime.now(timezone.utc)
    db.session.add(u)
    db.session.commit()
    return u

def test_get_login_opens_modal(client):
    resp = client.get(
        "/auth/login?game_id=10&quest_id=20&next=/foo/bar",
        follow_redirects=False,
    )
                                                                                   
    assert resp.status_code == 302
    loc = resp.headers["Location"]
    parsed = urlparse(loc)
    params = parse_qs(parsed.query)

    from flask import url_for

                                                             
    with client.application.test_request_context():
        expected_path = url_for("main.index", game_id="10", quest_id="20")
    assert parsed.path == expected_path

                                                         
    assert params["show_login"] == ["0"]
    assert params["next"] == ["/foo/bar"]



@pytest.mark.parametrize("headers,status_code,error,show_forgot", [
    ({}, 302, None, None),                                  
    ({"X-Requested-With": "XMLHttpRequest"}, 400,
     "Please correct the errors in the login form.", False),
])
def test_post_missing_credentials(client, headers, status_code, error, show_forgot):
    resp = client.post("/auth/login", data={}, headers=headers, follow_redirects=False)
    assert resp.status_code == status_code
    if error:
        body = resp.get_json()
        assert not body["success"]
        assert body["error"] == error
        assert body["show_forgot"] is show_forgot

@pytest.mark.parametrize("ajax", [False, True])
def test_post_invalid_email(client, ajax):
    data = {"email": "doesnotexist@example.com", "password": "whatever"}
    headers = {"X-Requested-With": "XMLHttpRequest"} if ajax else {}
    resp = client.post("/auth/login", data=data, headers=headers, follow_redirects=False)
    if ajax:
        assert resp.status_code == 401
        body = resp.get_json()
        assert body["error"] == "Invalid email or password."
        assert body["show_forgot"] is True
    else:
                                                                          
        assert resp.status_code == 302
        from flask import url_for

                                                                          
        with client.application.test_request_context():
            expected = url_for("main.index", show_login=1)

                                                                      
        location = resp.headers["Location"]
        assert location.startswith(expected), f"Got {location}, expected to start with {expected}"


def test_unverified_email_flow(client, user_unverified, app):
                                                            
    app.config["MAIL_SERVER"] = "smtp.test"
    data = {"email": user_unverified.email, "password": "secret"}
               
    resp = client.post(
        "/auth/login",
        data=data,
        headers={"X-Requested-With": "XMLHttpRequest"},
        follow_redirects=False,
    )
    assert resp.status_code == 409
    body = resp.get_json()
    assert body["error"] == "Please verify your email. A new link has been sent."
    assert body["show_forgot"] is False

@pytest.mark.parametrize("ajax", [False, True])
def test_wrong_password(client, user_normal, ajax):
    data = {"email": user_normal.email, "password": "wrongpwd"}
    headers = {"X-Requested-With": "XMLHttpRequest"} if ajax else {}
    resp = client.post("/auth/login", data=data, headers=headers, follow_redirects=False)
    if ajax:
        assert resp.status_code == 401
        body = resp.get_json()
        assert body["error"] == "Invalid email or password."
    else:
        assert resp.status_code == 302

@pytest.mark.parametrize("ajax", [False, True])
def test_successful_login_defaults_to_index(client, user_normal, ajax):
    data = {"email": user_normal.email, "password": "secret", "remember_me": "y"}
    headers = {"X-Requested-With": "XMLHttpRequest"} if ajax else {}
    resp = client.post("/auth/login", data=data, headers=headers, follow_redirects=False)
    if ajax:
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
                                                             
        assert body["redirect"] == url_for("main.index", show_join_custom=0, _external=False)
    else:
        assert resp.status_code == 302
        expected = url_for("main.index", show_join_custom=0, _external=False)
        assert resp.headers["Location"].startswith(expected)

def test_successful_login_with_next_param(client, user_normal):
    data = {"email": user_normal.email, "password": "secret", "remember_me": "y"}
    resp = client.post("/auth/login?next=/profile", data=data, follow_redirects=False)
                                          
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/profile")
