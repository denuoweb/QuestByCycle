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


def test_manifest_route(client):
    resp = client.get('/manifest.json')
    assert resp.status_code == 200
    assert resp.mimetype == 'application/json'
    data = resp.get_json()
    assert data.get('name') == 'QuestByCycle'
    assert 'window-controls-overlay' in data.get('display_override', [])
