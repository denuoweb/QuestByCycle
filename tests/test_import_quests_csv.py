import io
import pytest
from datetime import datetime, timedelta
from datetime import timezone

from app import create_app, db
from app.models.game import Game
from app.models.quest import Quest
from app.models.user import User
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


def test_import_quests_from_csv(client, admin_user, tmp_path):
    game = create_game("Game", admin_user.id)
    game.admins.append(admin_user)
    db.session.add(game)
    db.session.commit()

    csv_content = (
        "badge_name,badge_description,category,title,description,tips,points,"
        "completion_limit,frequency,verification_type,badge_awarded\n"
        "Badge,Badge desc,Cat,Quest Title,Desc,Tips,10,1,weekly,photo,1\n"
    )

    data = {
        "quests_csv": (io.BytesIO(csv_content.encode("utf-8")), "quests.csv")
    }

    login_as(client, admin_user)
    resp = client.post(
        f"/quests/game/{game.id}/import_quests",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    assert resp.get_json()["success"] is True

    quests = Quest.query.filter_by(game_id=game.id).all()
    assert len(quests) == 1
    assert quests[0].title == "Quest Title"
    assert quests[0].points == 10

