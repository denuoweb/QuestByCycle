import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app import create_app, db
from app.models.game import Game
from app.models.quest import Quest
from app.models.user import User
from app.models.badge import Badge
from app.quests import update_quest, delete_quest
from flask_login import login_user


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
    return game


def setup_quest(admin_user):
    game = create_game("Game", admin_user.id)
    game.admins.append(admin_user)
    db.session.add(game)
    db.session.commit()

    quest = Quest(title="Quest", game=game)
    db.session.add(quest)
    db.session.commit()
    return quest


def test_update_quest_returns_error_on_commit_failure(app, admin_user):
    quest = setup_quest(admin_user)
    with app.test_request_context(
        f"/quests/quest/{quest.id}/update",
        method="POST",
        json={
            "title": "New Title",
            "description": "",
            "tips": "",
            "category": "",
            "verification_type": "",
            "frequency": "",
            "badge_option": "none",
        },
    ):
        login_user(admin_user)
        with patch(
            "app.quests.db.session.commit", side_effect=Exception("DB failure")
        ):
            response, status = update_quest(quest.id)
    assert status == 500
    data = response.get_json()
    assert data["success"] is False


def test_update_quest_ignores_empty_numeric_fields(app, admin_user):
    quest = setup_quest(admin_user)
    quest.points = 5
    quest.completion_limit = 2
    quest.badge_awarded = 3
    db.session.commit()

    with app.test_request_context(
        f"/quests/quest/{quest.id}/update",
        method="POST",
        json={
            "title": "",
            "description": "",
            "tips": "",
            "points": "",
            "completion_limit": "",
            "badge_awarded": "",
            "category": "",
            "verification_type": "",
            "frequency": "",
            "badge_option": "none",
        },
    ):
        login_user(admin_user)
        response = update_quest(quest.id)

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert quest.points == 5
    assert quest.completion_limit == 2
    assert quest.badge_awarded == 3


def test_update_quest_rejects_badge_from_other_game(app, admin_user):
    quest = setup_quest(admin_user)
    other_game = create_game("Other", admin_user.id)
    other_game.admins.append(admin_user)
    db.session.add(other_game)
    db.session.commit()
    other_badge = Badge(name="B", description="d", game_id=other_game.id)
    db.session.add(other_badge)
    db.session.commit()

    with app.test_request_context(
        f"/quests/quest/{quest.id}/update",
        method="POST",
        json={
            "title": "",
            "description": "",
            "tips": "",
            "points": "",
            "completion_limit": "",
            "badge_awarded": "",
            "category": "",
            "verification_type": "",
            "frequency": "",
            "badge_option": "individual",
            "badge_id": other_badge.id,
        },
    ):
        login_user(admin_user)
        response, status = update_quest(quest.id)

    assert status == 400
    data = response.get_json()
    assert data["success"] is False
    assert quest.badge_id is None


def test_update_quest_requires_game_admin(app, admin_user):
    quest = setup_quest(admin_user)
    other_admin = User(
        username="other",
        email="other@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    other_admin.set_password("pw")
    db.session.add(other_admin)
    db.session.commit()

    with app.test_request_context(
        f"/quests/quest/{quest.id}/update",
        method="POST",
        json={
            "title": "",
            "description": "",
            "tips": "",
            "points": "",
            "completion_limit": "",
            "badge_awarded": "",
            "category": "",
            "verification_type": "",
            "frequency": "",
            "badge_option": "none",
        },
    ):
        login_user(other_admin)
        response, status = update_quest(quest.id)

    assert status == 403
    data = response.get_json()
    assert data["success"] is False


def test_delete_quest_returns_error_on_commit_failure(app, admin_user):
    quest = setup_quest(admin_user)
    with app.test_request_context(
        f"/quests/quest/{quest.id}/delete", method="DELETE"
    ):
        login_user(admin_user)
        with patch(
            "app.quests.db.session.commit", side_effect=Exception("DB failure")
        ):
            response, status = delete_quest(quest.id)
    assert status == 500
    data = response.get_json()
    assert data["success"] is False
