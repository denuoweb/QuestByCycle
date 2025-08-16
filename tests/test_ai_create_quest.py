from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from flask_login import login_user

from app import create_app, db
from app.models.game import Game
from app.models.user import User
from app.ai import create_quest


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
def admin_user(app):
    user = User(
        username="admin",
        email="admin@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    user.set_password("pw")
    user.created_at = datetime.now(timezone.utc)
    db.session.add(user)
    db.session.commit()
    return user


def create_game(title, admin_id):
    game = Game(
        title=title,
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
        admin_id=admin_id,
        timezone="UTC",
    )
    db.session.add(game)
    db.session.commit()
    return game


def test_create_quest_returns_error_on_commit_failure(app, admin_user):
    game = create_game("Game", admin_user.id)
    with app.test_request_context(
        "/ai/create_quest",
        method="POST",
        data={
            "title": "Quest",
            "description": "desc",
            "tips": "",
            "points": "100",
            "game_id": str(game.id),
            "completion_limit": "1",
            "frequency": "daily",
            "category": "",
            "verification_type": "photo",
            "badge_option": "none",
        },
    ):
        login_user(admin_user)
        with patch("app.ai.db.session.commit", side_effect=Exception("DB failure")):
            response, status = create_quest()
    assert status == 500
    data = response.get_json()
    assert data["success"] is False
