import pytest
from datetime import datetime, timedelta, timezone
from flask_login import login_user

from app import create_app, db
from app.models import Game, User


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


def create_admin(username):
    user = User(
        username=username,
        email=f"{username}@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    user.set_password("pw")
    db.session.add(user)
    db.session.commit()
    return user


def create_player(username):
    user = User(
        username=username,
        email=f"{username}@example.com",
        license_agreed=True,
        email_verified=True,
    )
    user.set_password("pw")
    db.session.add(user)
    db.session.commit()
    return user


def create_game(title, admin):
    game = Game(
        title=title,
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
        admin_id=admin.id,
        timezone="UTC",
    )
    game.admins.append(admin)
    db.session.add(game)
    db.session.commit()
    return game


def test_admin_sees_only_their_game_users(client):
    admin1 = create_admin("admin1")
    admin2 = create_admin("admin2")
    player1 = create_player("player1")
    player2 = create_player("player2")

    game1 = create_game("Game 1", admin1)
    game2 = create_game("Game 2", admin2)

    player1.participated_games.append(game1)
    player2.participated_games.append(game2)
    db.session.commit()

    login_as(client, admin1)

    resp = client.get(f"/admin/user_management/game/{game1.id}")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "player1@example.com" in html
    assert "player2@example.com" not in html

    resp = client.get(f"/admin/user_management/game/{game2.id}")
    assert resp.status_code == 302


def test_admin_cannot_delete_user(client):
    admin = create_admin("admin")
    player = create_player("player")
    game = create_game("Game", admin)
    player.participated_games.append(game)
    db.session.commit()

    login_as(client, admin)

    resp = client.post(f"/admin/delete_user/{player.id}")
    assert resp.status_code == 302
    assert User.query.get(player.id) is not None

