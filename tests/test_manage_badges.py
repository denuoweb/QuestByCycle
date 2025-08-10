import io
from datetime import datetime, timedelta, timezone

import pytest
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


@pytest.fixture
def admin_user(app):
    user = User(
        username="admin",
        email="admin@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    user.set_password("pw")
    db.session.add(user)
    db.session.commit()
    return user


def login_as(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
    with client.application.test_request_context():
        login_user(user)


def create_game(title, admin):
    game = Game(
        title=title,
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
        admin_id=admin.id,
    )
    game.admins.append(admin)
    db.session.add(game)
    db.session.commit()
    return game


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\xda``\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_manage_badges_filters_by_game(client, admin_user):
    game1 = create_game("Game 1", admin_user)
    game2 = create_game("Game 2", admin_user)

    b1 = Badge(name="B1", description="d1", game_id=game1.id)
    b2 = Badge(name="B2", description="d2", game_id=game2.id)
    db.session.add_all([b1, b2])
    db.session.commit()

    login_as(client, admin_user)

    resp = client.get(f"/badges/manage_badges?game_id={game1.id}")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "B1" in html
    assert "B2" not in html

    data = {
        "name": "New Badge",
        "description": "Desc",
        "category": "none",
        "image": (io.BytesIO(PNG_BYTES), "badge.png"),
    }
    resp = client.post(
        f"/badges/manage_badges?game_id={game1.id}",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 302

    new_badge = Badge.query.filter_by(name="New Badge").first()
    assert new_badge is not None
    assert new_badge.game_id == game1.id
