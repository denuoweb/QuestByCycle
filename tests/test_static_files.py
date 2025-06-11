import pytest
from app import create_app


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False})
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.fixture
def client(app):
    return app.test_client()


def test_favicon_route(client):
    resp = client.get('/favicon.ico')
    assert resp.status_code == 200
    assert resp.mimetype in {
        'image/x-icon',
        'image/vnd.microsoft.icon',
        'image/png',
        'image/webp',
    }


def test_robots_route(client):
    resp = client.get('/robots.txt')
    assert resp.status_code == 200
    assert resp.mimetype == 'text/plain'
    assert b'User-agent' in resp.data
