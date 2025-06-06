import pytest
from flask import url_for

from app import create_app
from app.utils import public_media_url

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


def test_public_media_url_variants(app):
    # absolute URL should be returned as-is
    assert public_media_url("https://example.com/img.jpg") == "https://example.com/img.jpg"

    # already served from /static should be returned unchanged
    assert public_media_url("/static/images/foo.jpg") == "/static/images/foo.jpg"

    # stored with leading 'static/' prefix
    expect = url_for("static", filename="images/foo.jpg")
    assert public_media_url("static/images/foo.jpg") == expect

    # stored with leading slash only
    assert public_media_url("/images/foo.jpg") == expect

    # stored without slash or static prefix
    assert public_media_url("images/foo.jpg") == expect
