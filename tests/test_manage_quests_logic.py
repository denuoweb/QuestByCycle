import pytest
from datetime import datetime, timedelta
from datetime import timezone

from app import create_app, db
from app.models import Game, Quest, User
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
    user.created_at = datetime.now(timezone.utc)
    db.session.add(user)
    db.session.commit()
    return user


def login_as(client, user):
    """Log in the given user for testing purposes."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
                                                                    
                                                           
    with client.application.test_request_context():
        login_user(user)


def create_game(title, admin_id):
    game = Game(
        title=title,
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
        admin_id=admin_id,
    )
    return game


def test_get_quests_per_game(client, admin_user):
                                            
    game1 = create_game("Game 1", admin_user.id)
    game2 = create_game("Game 2", admin_user.id)
    game1.admins.append(admin_user)
    game2.admins.append(admin_user)
    db.session.add_all([game1, game2])
    db.session.commit()

    q1 = Quest(title="Quest 1", game=game1)
    q2 = Quest(title="Quest 2", game=game1)
    q3 = Quest(title="Quest 3", game=game2)
    db.session.add_all([q1, q2, q3])
    db.session.commit()

                                                       
    resp1 = client.get(f"/quests/game/{game1.id}/quests")
    assert resp1.status_code == 200
    data1 = resp1.get_json()
    ids1 = {q["id"] for q in data1["quests"]}
    assert ids1 == {q1.id, q2.id}

    resp2 = client.get(f"/quests/game/{game2.id}/quests")
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    ids2 = {q["id"] for q in data2["quests"]}
    assert ids2 == {q3.id}


def test_manage_page_requires_admin(client, admin_user):
    game = create_game("Game", admin_user.id)
    game.admins.append(admin_user)
    db.session.add(game)
    db.session.commit()

    login_as(client, admin_user)
    resp = client.get(f"/quests/{game.id}/manage_quests")
    assert resp.status_code == 200
    assert bytes(game.title, "utf-8") in resp.data
