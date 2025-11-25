from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import text

from app import create_app, db
from app.models.game import Game
from app.models.user import User
from app.utils.encryption import ENCRYPTED_PREFIX, encrypt_game_secrets_if_needed


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("DATA_ENCRYPTION_KEY", Fernet.generate_key().decode())
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


def _make_game(admin_user: User) -> Game:
    """Return a minimal game preloaded with social credentials for testing."""
    now = datetime.now(timezone.utc)
    return Game(
        title="Encrypted Game",
        description="desc",
        description2="rules",
        start_date=now,
        end_date=now + timedelta(days=1),
        timezone="UTC",
        admin_id=admin_user.id,
        twitter_api_key="api-key",
        twitter_api_secret="api-secret",
        twitter_access_token="access-token",
        twitter_access_token_secret="access-token-secret",
    )


def test_game_keys_are_encrypted_at_rest(admin_user):
    game = _make_game(admin_user)
    game.admins.append(admin_user)
    db.session.add(game)
    db.session.commit()

    stored_value = db.session.execute(
        text("SELECT twitter_api_key FROM game WHERE id = :id"),
        {"id": game.id},
    ).scalar_one()

    assert stored_value.startswith(ENCRYPTED_PREFIX)

    reloaded = db.session.get(Game, game.id)
    assert reloaded.twitter_api_key == "api-key"
    assert reloaded.twitter_api_secret == "api-secret"


def test_plaintext_keys_get_backfilled(admin_user):
    game = _make_game(admin_user)
    game.admins.append(admin_user)
    db.session.add(game)
    db.session.commit()

    db.session.execute(
        text("UPDATE game SET twitter_api_secret = 'legacy-secret' WHERE id = :id"),
        {"id": game.id},
    )
    db.session.commit()

    updated = encrypt_game_secrets_if_needed()
    assert updated == 1

    stored_value = db.session.execute(
        text("SELECT twitter_api_secret FROM game WHERE id = :id"),
        {"id": game.id},
    ).scalar_one()
    assert stored_value.startswith(ENCRYPTED_PREFIX)

    refreshed = db.session.get(Game, game.id)
    assert refreshed.twitter_api_secret == "legacy-secret"
