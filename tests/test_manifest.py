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
    assert 'file_handlers' in data


def test_launch_handler_is_object(client):
    resp = client.get('/manifest.json')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data.get('launch_handler'), dict)


def test_manifest_shortcuts(client, app):
    from app.models import db, Game, Quest, User
    from datetime import datetime, timezone, timedelta

    with app.app_context():
        user = User(username='u', email='u@example.com', license_agreed=True)
        user.set_password('pw')
        db.session.add(user)
        db.session.commit()

        game = Game(
            title='G',
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc) + timedelta(days=1),
            admin_id=user.id,
        )
        game.admins.append(user)
        db.session.add(game)
        db.session.commit()

        quest = Quest(title='Q', game=game)
        db.session.add(quest)
        db.session.commit()

        resp = client.get(f'/manifest.json?game_id={game.id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert any(
            sc.get('url', '').endswith(f'quest_shortcut={quest.id}')
            for sc in data.get('shortcuts', [])
        )
