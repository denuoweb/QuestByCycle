from datetime import datetime, timedelta, timezone

import pytest
from bs4 import BeautifulSoup
from flask_login import login_user

from app import create_app, db
from app.models.game import Game
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


def login_as(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
    with client.application.test_request_context():
        login_user(user)


def test_create_game_highlights_current_admin(client):
    admin = User(
        username="admin",
        email="admin@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    admin.set_password("pw")
    db.session.add(admin)
    db.session.commit()

    login_as(client, admin)
    resp = client.get("/games/create_game")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    soup = BeautifulSoup(html, "html.parser")
    selected = {int(opt["value"]) for opt in soup.select("#admins option[selected]")}
    assert selected == {admin.id}


def test_create_game_attaches_creator_and_selected_admins(client):
    creator = User(
        username="creator",
        email="creator@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    creator.set_password("pw")
    extra_admin = User(
        username="extra",
        email="extra@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    extra_admin.set_password("pw")
    db.session.add_all([creator, extra_admin])
    db.session.commit()

    login_as(client, creator)
    resp = client.post(
        "/games/create_game",
        data={
            "title": "Game",
            "description": "Desc",
            "description2": "Rules",
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
            "admins": [str(extra_admin.id)],
            "is_public": "y",
            "allow_joins": "y",
            "details": "",
            "awards": "",
            "beyond": "",
            "twitter_username": "",
            "twitter_api_key": "",
            "twitter_api_secret": "",
            "twitter_access_token": "",
            "twitter_access_token_secret": "",
            "facebook_app_id": "",
            "facebook_app_secret": "",
            "facebook_access_token": "",
            "facebook_page_id": "",
            "instagram_user_id": "",
            "instagram_access_token": "",
            "calendar_url": "",
            "logo_url": "",
            "social_media_liaison_email": "",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    game = Game.query.filter_by(title="Game").first()
    assert game is not None
    assert game.admin_id == creator.id
    admin_ids = {u.id for u in game.admins}
    assert admin_ids == {creator.id, extra_admin.id}


def test_update_game_highlights_existing_admins(client):
    admin1 = User(
        username="admin1",
        email="admin1@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    admin1.set_password("pw")
    admin2 = User(
        username="admin2",
        email="admin2@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    admin2.set_password("pw")
    db.session.add_all([admin1, admin2])
    db.session.commit()

    game = Game(
        title="Game",
        admin_id=admin1.id,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
    )
    game.admins.extend([admin1, admin2])
    db.session.add(game)
    db.session.commit()

    login_as(client, admin1)
    resp = client.get(f"/games/update_game/{game.id}")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    soup = BeautifulSoup(html, "html.parser")
    selected = {int(opt["value"]) for opt in soup.select("#admins option[selected]")}
    assert selected == {admin1.id, admin2.id}


def test_super_admin_hidden_from_admin_selection(client):
    super_admin = User(
        username="super",
        email="super@example.com",
        is_admin=True,
        is_super_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    super_admin.set_password("pw")
    other_admin = User(
        username="other",
        email="other@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    other_admin.set_password("pw")
    db.session.add_all([super_admin, other_admin])
    db.session.commit()

    login_as(client, super_admin)
    resp = client.get("/games/create_game")
    assert resp.status_code == 200
    soup = BeautifulSoup(resp.get_data(as_text=True), "html.parser")
    options = {int(opt["value"]) for opt in soup.select("#admins option")}
    assert super_admin.id not in options
    assert other_admin.id in options

    resp = client.post(
        "/games/create_game",
        data={
            "title": "Game",
            "description": "Desc",
            "description2": "Rules",
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
            "admins": [str(other_admin.id)],
            "is_public": "y",
            "allow_joins": "y",
            "details": "",
            "awards": "",
            "beyond": "",
            "twitter_username": "",
            "twitter_api_key": "",
            "twitter_api_secret": "",
            "twitter_access_token": "",
            "twitter_access_token_secret": "",
            "facebook_app_id": "",
            "facebook_app_secret": "",
            "facebook_access_token": "",
            "facebook_page_id": "",
            "instagram_user_id": "",
            "instagram_access_token": "",
            "calendar_url": "",
            "logo_url": "",
            "social_media_liaison_email": "",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    game = Game.query.filter_by(title="Game").first()
    assert game is not None
    admin_ids = {u.id for u in game.admins}
    assert super_admin.id not in admin_ids
    assert other_admin.id in admin_ids


def test_update_game_hides_super_admin(client):
    super_admin = User(
        username="super",
        email="super@example.com",
        is_admin=True,
        is_super_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    super_admin.set_password("pw")
    admin = User(
        username="admin",
        email="admin@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    admin.set_password("pw")
    db.session.add_all([super_admin, admin])
    db.session.commit()

    game = Game(
        title="Game",
        admin_id=super_admin.id,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
    )
    game.admins.extend([super_admin, admin])
    db.session.add(game)
    db.session.commit()

    login_as(client, admin)
    resp = client.get(f"/games/update_game/{game.id}")
    assert resp.status_code == 200
    soup = BeautifulSoup(resp.get_data(as_text=True), "html.parser")
    options = {int(opt["value"]) for opt in soup.select("#admins option")}
    assert super_admin.id not in options
    selected = {int(opt["value"]) for opt in soup.select("#admins option[selected]")}
    assert super_admin.id not in selected
    assert admin.id in selected
