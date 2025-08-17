import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()

@pytest.fixture
def client(app):
    return app.test_client()


def test_resize_image_webp(client):
    resp = client.get(
        "/resize_image?path=images/default_badge.png&width=50",
        headers={"Accept": "image/webp"},
    )
    assert resp.status_code == 200
    assert resp.mimetype == "image/webp"


def test_resize_image_jpeg(client):
    resp = client.get(
        "/resize_image?path=images/default_badge.png&width=50",
        headers={"Accept": "image/png"},
    )
    assert resp.status_code == 200
    assert resp.mimetype == "image/jpeg"


def test_resize_image_avif(client):
    resp = client.get(
        "/resize_image?path=images/default_badge.png&width=50",
        headers={"Accept": "image/avif"},
    )
    assert resp.status_code == 200
    assert resp.mimetype == "image/avif"

