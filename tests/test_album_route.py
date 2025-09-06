import pytest
from app import create_app


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })
    ctx = app.app_context()
    ctx.push()
    yield app
    ctx.pop()


@pytest.fixture
def client(app):
    return app.test_client()


def test_album_route_redirects(client):
    resp = client.get('/album/42')
    assert resp.status_code == 302
    assert '/42?album=1' in resp.headers['Location']

