import pytest
from flask import url_for

from app import create_app
from app.utils.file_uploads import public_media_url, allowed_image_file, delete_media_file
from app.utils import get_int_param

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
                                           
    assert public_media_url("https://example.com/img.jpg") == "https://example.com/img.jpg"

                                                              
    assert public_media_url("/static/images/foo.jpg") == "/static/images/foo.jpg"

                                          
    expect = url_for("static", filename="images/foo.jpg")
    assert public_media_url("static/images/foo.jpg") == expect

                                    
    assert public_media_url("/images/foo.jpg") == expect

                                           
    assert public_media_url("images/foo.jpg") == expect


def test_save_submission_video_invalid(app, tmp_path):
    """Uploading an invalid video should raise a ValueError."""
    from io import BytesIO
    from werkzeug.datastructures import FileStorage
    from app.utils.file_uploads import save_submission_video

    fake_video = BytesIO(b"not a real video")
    file = FileStorage(stream=fake_video, filename="bad.mp4", content_type="video/mp4")

    with pytest.raises(ValueError):
        save_submission_video(file)


def test_save_submission_video_no_ffmpeg(app, monkeypatch):
    """Video saving should bypass conversion if ffmpeg is unavailable."""
    from io import BytesIO
    from werkzeug.datastructures import FileStorage
    from app.utils.file_uploads import save_submission_video
    import shutil

    video_data = BytesIO(b"0" * 100)
    file = FileStorage(stream=video_data, filename="small.mp4", content_type="video/mp4")

    app.config["FFMPEG_PATH"] = "/nonexistent/ffmpeg"
    monkeypatch.setattr(shutil, "which", lambda x: None)

    path = save_submission_video(file)
    assert path.endswith(".mp4")


def test_save_submission_image_invalid_extension(app, tmp_path):
    """Uploading a non-image file should raise a ValueError."""
    from io import BytesIO
    from werkzeug.datastructures import FileStorage
    from app.utils.file_uploads import save_submission_image

    fake_file = BytesIO(b"{}")
    file = FileStorage(
        stream=fake_file,
        filename="bad.json",
        content_type="application/json",
    )

    with pytest.raises(ValueError):
        save_submission_image(file)


def test_allowed_image_file_heif():
    """HEIF and HEIC images should be rejected."""
    assert not allowed_image_file("photo.heif")
    assert not allowed_image_file("image.HEIC")


def test_save_submission_image_too_large(app):
    """Images larger than the limit should be rejected."""
    from io import BytesIO
    from werkzeug.datastructures import FileStorage
    from app.utils.file_uploads import save_submission_image, MAX_IMAGE_BYTES

    big_data = BytesIO(b"0" * (MAX_IMAGE_BYTES + 1))
    file = FileStorage(stream=big_data, filename="big.jpg", content_type="image/jpeg")

    with pytest.raises(ValueError):
        save_submission_image(file)


def test_get_int_param_parsing(app):
    """Ensure get_int_param converts values safely."""
    with app.test_request_context('/?a=1&b=&c=foo'):
        assert get_int_param('a') == 1
        assert get_int_param('b') is None
        assert get_int_param('c') is None
        assert get_int_param('missing', default=7) == 7


def test_delete_media_file_local(app, tmp_path):
    app.static_folder = tmp_path
    file_path = tmp_path / "images" / "verifications"
    file_path.mkdir(parents=True)
    img = file_path / "foo.png"
    img.write_bytes(b"1")

    delete_media_file("images/verifications/foo.png")
    assert not img.exists()


def test_delete_media_file_gcs(app, monkeypatch):
    called = {}

    def fake_delete(path):
        called["path"] = path

    monkeypatch.setattr("app.utils.file_uploads._delete_from_gcs", fake_delete)
    app.config["GCS_BUCKET"] = "bucket"
    url = "https://storage.googleapis.com/bucket/images/foo.png"

    delete_media_file(url)
    assert called.get("path") == "images/foo.png"
