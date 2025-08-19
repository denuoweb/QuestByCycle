import pytest

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
def admin(app):
    user = User(
        username="admin",
        email="admin@example.com",
        license_agreed=True,
        email_verified=True,
    )
    user.set_password("pw")
    db.session.add(user)
    db.session.commit()
    return user


def test_generate_unique_code_retry_limit(app, admin, monkeypatch):
    db.session.add(Game(title="Existing", admin_id=admin.id, custom_game_code="ABCDE"))
    db.session.commit()
    monkeypatch.setattr("random.choices", lambda *args, **kwargs: list("ABCDE"))
    with pytest.raises(RuntimeError):
        Game.generate_unique_code(max_attempts=3)


def test_game_init_retry_limit(app, admin, monkeypatch):
    db.session.add(Game(title="Existing", admin_id=admin.id, custom_game_code="ABCDE"))
    db.session.commit()
    monkeypatch.setattr("random.choices", lambda *args, **kwargs: list("ABCDE"))
    with pytest.raises(RuntimeError):
        Game(title="New Game", admin_id=admin.id)

