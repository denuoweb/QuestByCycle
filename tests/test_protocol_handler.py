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


def test_protocol_handler_redirect(client):
    resp = client.get('/protocol-handler', query_string={'url': 'web+questbycycle:1'})
    assert resp.status_code == 302
    assert '/quests/quest/1' in resp.headers['Location']
