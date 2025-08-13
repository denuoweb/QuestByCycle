import pytest
from urllib.parse import urlparse, parse_qs

from app import create_app, db
from tests.helpers import url_for_path
from app.models.user import User
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import SQLAlchemyError

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
def user_existing(app):
    u = User(
        username="existing",
        email="existing@example.com",
        license_agreed=True,
        email_verified=True,
    )
    u.set_password("secret")
    u.created_at = datetime.now(timezone.utc)
    db.session.add(u)
    db.session.commit()
    return u

                                                      

def test_register_get_shows_form(client):
    from flask import url_for

    resp = client.get("/auth/register", follow_redirects=False)
    assert resp.status_code == 302

    loc = resp.headers["Location"]
                                                   
    assert loc.startswith(url_for_path(client.application, "main.index"))

    qs = parse_qs(urlparse(loc).query)
    assert qs.get("show_register") == ["1"]

                                                               

def test_register_post_missing_data(client):
    resp = client.post("/auth/register", data={}, follow_redirects=False)
    assert resp.status_code == 302

    loc = resp.headers["Location"]
                                                         
    assert loc.startswith(url_for_path(client.application, "main.index"))
    qs = parse_qs(urlparse(loc).query)
    assert qs.get("show_register") == ["1"]

                                                        

def test_register_post_without_license(client):
    data = {
        "email": "newuser@example.com",
        "password": "password",
        "confirm_password": "password",
                                
    }
    resp = client.post("/auth/register", data=data, follow_redirects=False)
    assert resp.status_code == 302

    loc = resp.headers["Location"]
    assert loc.startswith(url_for_path(client.application, "main.index"))
    qs = parse_qs(urlparse(loc).query)
    assert qs.get("show_register") == ["1"]

                                                                   

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
                                                       
    assert loc.endswith('/auth/register')

                                                                      

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
                                                 
    assert url_for_path(client.application, "main.index") in loc
    assert "show_join_custom=1" in loc
                                           

                                               

def test_register_with_next_param(client):
    data = {
        "email": "nxt@example.com",
        "password": "safepwd",
        "confirm_password": "safepwd",
        "accept_license": "y",
    }
    resp = client.post(
        "/auth/register?next=/dashboard",
        data=data,
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/dashboard")

                                                                        

def test_register_with_game_id(client):

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
                                                           
    assert parsed.path == "/42"
    qs = parse_qs(parsed.query)
    assert qs.get("show_join_custom") == ["0"]


                                                               

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


def test_register_via_submit_photo_link_auto_joins_game(client, app):
    from app.models.game import Game
    from app.models.quest import Quest
    from app.models.user import User
    from app import db

    app.config["MAIL_SERVER"] = None

    admin = User(
        username="admin",
        email="admin@example.com",
        license_agreed=True,
        email_verified=True,
    )
    admin.set_password("secret")
    admin.created_at = datetime.now(timezone.utc)
    db.session.add(admin)
    db.session.commit()

    game = Game(
        title="Quest Game",
        description="Test",
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
        admin_id=admin.id,
    )
    db.session.add(game)
    db.session.commit()

    quest = Quest(
        title="Photo Quest",
        verification_type="photo",
        game_id=game.id,
        points=5,
    )
    db.session.add(quest)
    db.session.commit()

    data = {
        "email": "quester@example.com",
        "password": "questpwd",
        "confirm_password": "questpwd",
        "accept_license": "y",
    }

    resp = client.post(
        f"/auth/register?next=/quests/submit_photo/{quest.id}",
        data=data,
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith(f"/quests/submit_photo/{quest.id}")

    page = client.get(resp.headers["Location"], follow_redirects=True)
    assert page.status_code == 200

    user = User.query.filter_by(email=data["email"]).first()
    assert game in user.participated_games


def test_register_db_failure(client, monkeypatch):
    """
    If the database commit fails, the registration view should flash an error
    and redirect back into the registration modal (show_register=1).
    """
                                             
    monkeypatch.setattr(
        db.session,
        "commit",
        lambda: (_ for _ in ()).throw(SQLAlchemyError("fail")),
    )

    data = {
        "email": "err@example.com",
        "password": "errpwd",
        "confirm_password": "errpwd",
        "accept_license": "y",
    }
                                                                            
    resp = client.post("/auth/register", data=data, follow_redirects=False)
    assert resp.status_code == 302
    loc = resp.headers["Location"]

                                                        
    assert loc.startswith(url_for_path(client.application, "main.index"))
    assert "show_register=1" in loc

                                                                                    
                                                                      
