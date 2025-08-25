import pytest
from datetime import datetime, timedelta, timezone
from flask_login import login_user

from app import create_app, db
from app.models import Game, Badge, User


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


def test_admin_cannot_delete_other_games_badge(client):
    admin1 = create_admin("admin1")
    admin2 = create_admin("admin2")

    game1 = create_game("Game 1", admin1)
    game2 = create_game("Game 2", admin2)

    foreign_badge = Badge(name="B", description="desc", game_id=game2.id)
    own_badge = Badge(name="Own", description="desc", game_id=game1.id)
    db.session.add_all([foreign_badge, own_badge])
    db.session.commit()

    login_as(client, admin1)

    resp = client.delete(f"/badges/delete/{foreign_badge.id}")
    assert resp.status_code == 403
    assert Badge.query.get(foreign_badge.id) is not None

    resp = client.delete(f"/badges/delete/{own_badge.id}")
    assert resp.status_code == 200
    assert Badge.query.get(own_badge.id) is None
