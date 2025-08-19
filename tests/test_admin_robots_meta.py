import pytest
from flask_login import login_user

from app import create_app, db
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


def login_as(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
    with client.application.test_request_context():
        login_user(user)


def test_admin_dashboard_has_noindex_meta(client):
    admin = User(
        username="admin",
        email="admin@example.com",
        is_admin=True,
        license_agreed=True,
        email_verified=True,
    )
    admin.set_password("pw")
    db.session.add(admin)
    db.session.commit()

    login_as(client, admin)
    resp = client.get("/admin/admin_dashboard")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert '<meta name="robots" content="noindex, nofollow">' in html
