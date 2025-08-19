import pytest
from app import create_app, db
from app.models.user import User


@pytest.fixture
def app():
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
def client(app):
    return app.test_client()


def login(client):
    user = User(
        username="u",
        email="u@example.com",
        license_agreed=True,
        email_verified=True,
    )
    user.set_password("x")
    db.session.add(user)
    db.session.commit()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
    return user


def test_profile_update_validation(client):
    user = login(client)
    resp = client.post(f"/profile/{user.id}/update", json={"age_group": "child"})
    assert resp.status_code == 400


def test_profile_update_success(client):
    user = login(client)
    resp = client.post(
        f"/profile/{user.id}/update",
        json={"display_name": "Cycler", "age_group": "adult"},
    )
    assert resp.status_code == 200
    assert User.query.get(user.id).display_name == "Cycler"
