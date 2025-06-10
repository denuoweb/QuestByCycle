import pytest
from flask import url_for

from app import create_app
from app.utils import public_media_url, allowed_image_file

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
    from app.utils import save_submission_video

    fake_video = BytesIO(b"not a real video")
    file = FileStorage(stream=fake_video, filename="bad.mp4", content_type="video/mp4")

    with pytest.raises(ValueError):
        save_submission_video(file)


def test_save_submission_video_no_ffmpeg(app, monkeypatch):
    """Video saving should bypass conversion if ffmpeg is unavailable."""
    from io import BytesIO
    from werkzeug.datastructures import FileStorage
    from app.utils import save_submission_video
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
    from app.utils import save_submission_image

    fake_file = BytesIO(b"{}")
    file = FileStorage(
        stream=fake_file,
        filename="bad.json",
        content_type="application/json",
    )

    with pytest.raises(ValueError):
        save_submission_image(file)


def test_allowed_image_file_heif():
    """HEIF and HEIC images should be recognized as valid."""
    assert allowed_image_file("photo.heif")
    assert allowed_image_file("image.HEIC")


def test_save_submission_image_too_large(app):
    """Images larger than the limit should be rejected."""
    from io import BytesIO
    from werkzeug.datastructures import FileStorage
    from app.utils import save_submission_image, MAX_IMAGE_BYTES

    big_data = BytesIO(b"0" * (MAX_IMAGE_BYTES + 1))
    file = FileStorage(stream=big_data, filename="big.jpg", content_type="image/jpeg")

    with pytest.raises(ValueError):
        save_submission_image(file)
