import pytest
from urllib.parse import urlparse, parse_qs

from app import create_app, db
from app.models.user import User
from app.models.game import Game
from datetime import datetime, timezone, timedelta


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        # MAIL_SERVER present or not does not affect verify_email route behavior
        "MAIL_SERVER": None,
    })
    ctx = app.app_context()
    ctx.push()

    db.drop_all()
    db.create_all()

    yield app

    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture
def client(app):
    return app.test_client()


def test_verify_email_from_base_url_opens_custom_modal(client):
    # Create an unverified user and generate a verification token
    u = User(
        username="newbie",
        email="newbie@example.com",
        license_agreed=True,
        email_verified=False,
        created_at=datetime.now(timezone.utc),
    )
    u.set_password("pw")
    db.session.add(u)
    db.session.commit()

    token = u.generate_verification_token()

    # Simulate clicking the e-mail verification link without game context
    resp = client.get(f"/auth/verify_email/{token}", follow_redirects=False)
    assert resp.status_code == 302

    loc = resp.headers["Location"]
    parsed = urlparse(loc)
    qs = parse_qs(parsed.query)

    # Should redirect to main.index with show_join_custom=1 so the modal opens
    assert parsed.path == "/"
    assert qs.get("show_join_custom") == ["1"]


def test_join_exact_custom_game_after_verify_opens_modal(client):
    # Prepare an admin user and a custom game that allows joins
    admin = User(
        username="admin",
        email="admin@example.com",
        license_agreed=True,
        email_verified=True,
        created_at=datetime.now(timezone.utc),
    )
    admin.set_password("secret")
    db.session.add(admin)
    db.session.commit()

    game = Game(
        title="Spring Ride",
        description="A test game",
        start_date=datetime.now(timezone.utc) - timedelta(days=1),
        end_date=datetime.now(timezone.utc) + timedelta(days=1),
        admin_id=admin.id,
        is_public=True,
        allow_joins=True,
        custom_game_code="ABC123",
    )
    db.session.add(game)
    db.session.commit()

    # New user verifies via email (no game context), gets logged in
    u = User(
        username="clicker",
        email="clicker@example.com",
        license_agreed=True,
        email_verified=False,
        created_at=datetime.now(timezone.utc),
    )
    u.set_password("pw")
    db.session.add(u)
    db.session.commit()

    token = u.generate_verification_token()
    resp = client.get(f"/auth/verify_email/{token}", follow_redirects=False)
    assert resp.status_code == 302

    # Now simulate selecting a game in the modal, which posts custom_game_code
    resp2 = client.post(
        "/games/join_custom_game",
        data={"custom_game_code": "ABC123"},
        follow_redirects=False,
    )
    assert resp2.status_code == 302

    loc2 = resp2.headers["Location"]
    parsed2 = urlparse(loc2)
    # Redirect should go to /<game_id>
    assert parsed2.path == f"/{game.id}"

    # Verify DB state: user is joined and selected_game_id is set
    user = db.session.get(User, u.id)
    assert game in user.participated_games
    assert user.selected_game_id == game.id

