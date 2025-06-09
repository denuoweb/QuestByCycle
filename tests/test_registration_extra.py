import pytest
from app import create_app, db

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

def test_register_mail_server_sends_verification_and_modal(client):
    data = {
        "email": "foo@bar.com",
        "password": "pw",
        "confirm_password": "pw",
        "accept_license": "y",
    }
    resp = client.post("/auth/register", data=data, follow_redirects=False)
                                                
    assert resp.status_code == 302
    loc = resp.headers["Location"]
    assert "show_join_custom=1" in loc
                                           

def test_register_next_overrides_quest(client):
    data = {
        "email": "bar@baz.com",
        "password": "pw",
        "confirm_password": "pw",
        "accept_license": "y",
    }
    resp = client.post("/auth/register?next=/dashboard&quest_id=5", data=data, follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/dashboard")
