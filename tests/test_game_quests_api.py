import pytest
from app import create_app, db
from app.models.game import Game
from app.models.quest import Quest
from app.models.user import User


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
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


def create_game_with_quests():
    user = User(username="admin", email="a@example.com", license_agreed=True)
    db.session.add(user)
    db.session.flush()
    game = Game(title="G", description="d", admin_id=user.id, timezone="UTC")
    db.session.add(game)
    db.session.flush()
    q1 = Quest(
        title="A",
        description="d",
        game_id=game.id,
        points=1,
        enabled=True,
        is_sponsored=False,
        badge_option="none",
    )
    q2 = Quest(
        title="B",
        description="d",
        game_id=game.id,
        points=1,
        enabled=False,
        is_sponsored=False,
        badge_option="none",
    )
    db.session.add_all([q1, q2])
    db.session.commit()
    return game, q1, q2


def test_game_quests_endpoint(client):
    game, q1, q2 = create_game_with_quests()
    resp = client.get(f"/games/{game.id}/quests")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["quests"]) == 1
    assert data["quests"][0]["id"] == q1.id

    resp = client.get(f"/games/{game.id}/quests?include_disabled=true")
    data = resp.get_json()
    assert len(data["quests"]) == 2


def test_game_quests_invalid_param(client):
    game, *_ = create_game_with_quests()
    resp = client.get(f"/games/{game.id}/quests?include_disabled=maybe")
    assert resp.status_code == 400
