from datetime import datetime, timedelta, timezone

import pytest
from bs4 import BeautifulSoup

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
def client(app):
    return app.test_client()


def test_open_games_listing(client):
    now = datetime.now(timezone.utc)
    admin = User(
        username="admin",
        email="admin@example.com",
        license_agreed=True,
        email_verified=True,
    )
    admin.set_password("pw")
    db.session.add(admin)
    db.session.commit()

    upcoming_game = Game(
        title="Upcoming Game",
        admin_id=admin.id,
        custom_game_code="UPCOM",
        is_public=True,
        allow_joins=False,
        start_date=now + timedelta(days=1),
        end_date=now + timedelta(days=10),
    )
    ongoing_open = Game(
        title="Ongoing Open Game",
        admin_id=admin.id,
        custom_game_code="OPEN1",
        is_public=True,
        allow_joins=True,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=10),
    )
    ongoing_closed = Game(
        title="Ongoing Closed Game",
        admin_id=admin.id,
        custom_game_code="CLOSE",
        is_public=True,
        allow_joins=False,
        start_date=now - timedelta(days=1),
        end_date=now + timedelta(days=10),
    )
    db.session.add_all([upcoming_game, ongoing_open, ongoing_closed])
    db.session.commit()

    resp = client.get(f"/?game_id={ongoing_open.id}")
    assert resp.status_code == 200
    soup = BeautifulSoup(resp.get_data(as_text=True), "html.parser")
    titles = [li.get_text(strip=True) for li in soup.select("#customGameList li")]
    assert any("Upcoming Game" in t for t in titles)
    assert any("Ongoing Open Game" in t for t in titles)
    assert all("Ongoing Closed Game" not in t for t in titles)
