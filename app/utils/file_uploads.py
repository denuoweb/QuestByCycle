# File upload related helpers
from __future__ import annotations
import os
import shutil
import subprocess
import uuid
from urllib.parse import urlparse

from flask import current_app, url_for
from google.api_core.exceptions import GoogleAPIError
from google.cloud import storage
from PIL import ExifTags, Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}

ALLOWED_IMAGE_MIMETYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
}
ALLOWED_VIDEO_MIMETYPES = {"video/mp4", "video/webm", "video/quicktime"}

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_VIDEO_BYTES = 25 * 1024 * 1024
MAX_JSON_BYTES = 1 * 1024 * 1024
MAX_IMAGE_DIMENSION = 4096
MAX_VIDEO_WIDTH = 1920
MAX_VIDEO_HEIGHT = 1080
ALLOWED_JSON_EXTENSIONS = {"json"}


def _validate_upload_file(
    file_obj,
    allowed_extensions: set[str],
    max_bytes: int,
    size_error: str,
    *,
    allowed_mimetypes: set[str] | None = None,
) -> str:
    """Validate an uploaded file and return its extension.

    The file is checked for presence, size limits, allowed extensions and
    optionally MIME types.
    """

    if not file_obj or not getattr(file_obj, "filename", None):
        raise ValueError("Invalid file object passed.")

    file_obj.seek(0, os.SEEK_END)
    size = file_obj.tell()
    file_obj.seek(0)
    if size > max_bytes:
        raise ValueError(size_error)

    ext = file_obj.filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed_extensions:
        raise ValueError("File extension not allowed.")

    if allowed_mimetypes is not None:
        mimetype = getattr(file_obj, "mimetype", None)
        if mimetype not in allowed_mimetypes:
            raise ValueError("MIME type not allowed.")

    return ext


def _upload_to_gcs(local_path: str, remote_path: str, *, content_type: str | None = None) -> str | None:
    bucket_name = current_app.config.get("GCS_BUCKET")
    if not bucket_name:
        return None

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(remote_path)
    blob.upload_from_filename(local_path, content_type=content_type)

    storage_class = current_app.config.get("GCS_STORAGE_CLASS", "ARCHIVE")
    try:
        blob.update_storage_class(storage_class)
    except GoogleAPIError as exc:
        current_app.logger.warning(
            "Failed to set storage class for %s: %s", remote_path, exc
        )

    try:
        blob.make_public()
    except GoogleAPIError as exc:
        current_app.logger.warning(
            "Failed to make %s public: %s", remote_path, exc
        )

    base_url = current_app.config.get("GCS_BASE_URL") or f"https://storage.googleapis.com/{bucket_name}"
    return f"{base_url}/{remote_path}"


def _delete_from_gcs(remote_path: str) -> None:
    bucket_name = current_app.config.get("GCS_BUCKET")
    if not bucket_name:
        return

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(remote_path)
    try:
        blob.delete()
    except GoogleAPIError as exc:
        current_app.logger.warning(
            "Failed to delete %s from GCS: %s", remote_path, exc
        )


def _get_ffmpeg_bin() -> str | None:
    """Return the path to a usable ``ffmpeg`` binary."""
    configured = current_app.config.get("FFMPEG_PATH")
    if configured:
        if os.path.isabs(configured) and os.path.exists(configured):
            return configured
        resolved = shutil.which(configured)
        if resolved:
            return resolved

    return shutil.which("ffmpeg")


def allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def allowed_image_file(filename: str) -> bool:
    return allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS)


def allowed_video_file(filename: str) -> bool:
    return allowed_file(filename, ALLOWED_VIDEO_EXTENSIONS)


def correct_image_orientation(img: Image.Image) -> Image.Image:
    tag = next((t for t, v in ExifTags.TAGS.items() if v == "Orientation"), None)
    if not tag:
        return img
    try:
        exif = img._getexif()
        if exif:
            orientation = exif.get(tag)
            rotation = {3: 180, 6: -90, 8: 90}.get(orientation)
            if rotation:
                img = img.rotate(rotation, expand=True)
    except Exception as exc:
        current_app.logger.debug(
            "Failed to adjust image orientation: %s", exc
        )
    return img


def save_image_file(
    image_file,
    subpath,
    *,
    allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
    allowed_mimetypes=ALLOWED_IMAGE_MIMETYPES,
    old_filename=None,
    output_ext=None,
):
    """Save ``image_file`` under ``static/<subpath>``."""
    ext = _validate_upload_file(
        image_file,
        allowed_extensions,
        MAX_IMAGE_BYTES,
        "Image exceeds 8 MB limit",
        allowed_mimetypes=allowed_mimetypes,
    )
    if output_ext:
        ext = output_ext.lstrip(".").lower()

    filename = secure_filename(f"{uuid.uuid4()}.{ext}")
    upload_dir = os.path.join(current_app.static_folder, subpath)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    image_file.save(file_path)

    try:
        with Image.open(file_path) as img:
            corrected = correct_image_orientation(img)
            width, height = corrected.size
            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                os.remove(file_path)
                raise ValueError("Image dimensions exceed 4096x4096 limit")
            if corrected is not img:
                corrected.save(file_path)
    except UnidentifiedImageError:
        os.remove(file_path)
        raise ValueError("Invalid image file")

    gcs_url = _upload_to_gcs(file_path, os.path.join(subpath, filename), content_type=image_file.mimetype)
    if old_filename:
        old_path = os.path.join(current_app.static_folder, old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)
        _delete_from_gcs(old_filename)

    if gcs_url:
        os.remove(file_path)
        return gcs_url

    return os.path.join(subpath, filename)


def save_json_file(json_file, subpath, *, old_filename=None):
    """Save ``json_file`` under ``static/<subpath>``."""
    _validate_upload_file(
        json_file,
        ALLOWED_JSON_EXTENSIONS,
        MAX_JSON_BYTES,
        "JSON exceeds 1 MB limit",
    )

    filename = secure_filename(f"{uuid.uuid4()}.json")
    upload_dir = os.path.join(current_app.static_folder, subpath)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    json_file.save(file_path)

    if old_filename:
        old_path = os.path.join(current_app.static_folder, old_filename)
        if os.path.exists(old_path):
            os.remove(old_path)

    return os.path.join(subpath, filename)


def save_leaderboard_image(image_file):
    try:
        return save_image_file(image_file, os.path.join("images", "leaderboard"))
    except Exception as e:
        raise ValueError(f"Failed to save image: {e}") from e


def save_game_logo(image_file, old_filename=None):
    try:
        return save_image_file(
            image_file,
            os.path.join("images", "game_logos"),
            old_filename=old_filename,
        )
    except Exception as e:
        raise ValueError(f"Failed to save image: {e}") from e


def create_smog_effect(image, smog_level):
    smog_overlay = Image.new("RGBA", image.size, (169, 169, 169, int(255 * smog_level)))
    return Image.alpha_composite(image.convert("RGBA"), smog_overlay)


def generate_smoggy_images(image_path, game_id):
    try:
        original_image = Image.open(image_path)
        for i in range(10):
            smog_level = i / 9.0
            smoggy_image = create_smog_effect(original_image, smog_level)
            dest = os.path.join(
                current_app.root_path,
                f"static/images/leaderboard/smoggy_skyline_{game_id}_{i}.png",
            )
            smoggy_image.save(dest)
    except Exception as e:
        raise ValueError(f"Failed to generate smoggy images: {e}")


def save_profile_picture(profile_picture_file, old_filename=None):
    uploads = current_app.config["UPLOAD_FOLDER"]
    return save_image_file(profile_picture_file, uploads, old_filename=old_filename)


def save_badge_image(image_file):
    try:
        return os.path.basename(
            save_image_file(
                image_file,
                os.path.join("images", "badge_images"),
                output_ext="png",
            )
        )
    except Exception as e:
        raise ValueError(f"Failed to save image: {e}") from e


def save_bicycle_picture(bicycle_picture_file, old_filename=None):
    subdir = os.path.join(current_app.config["UPLOAD_FOLDER"], "bicycle_pictures")
    return save_image_file(bicycle_picture_file, subdir, old_filename=old_filename)


def save_submission_image(submission_image_file):
    try:
        return save_image_file(submission_image_file, os.path.join("images", "verifications"))
    except Exception as e:
        current_app.logger.error(f"Failed to save image: {e}")
        raise


def save_submission_video(submission_video_file):
    """Save an uploaded video for quest verification."""
    try:
        ext = _validate_upload_file(
            submission_video_file,
            ALLOWED_VIDEO_EXTENSIONS,
            MAX_VIDEO_BYTES,
            "Video exceeds 25 MB limit",
            allowed_mimetypes=ALLOWED_VIDEO_MIMETYPES,
        )

        header = submission_video_file.read(512)
        submission_video_file.seek(0)
        ffmpeg_bin = _get_ffmpeg_bin()
        if not ffmpeg_bin and current_app.config.get("FFMPEG_PATH") in (None, "ffmpeg"):
            if header.isascii() and b"\x00" not in header:
                raise ValueError("Invalid or corrupted video file")
        tmp_dir = os.path.join(current_app.static_folder, "videos", "tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        orig_name = secure_filename(f"{uuid.uuid4()}_orig.{ext}")
        orig_path = os.path.join(tmp_dir, orig_name)
        current_app.logger.debug("Saving original upload to %s", orig_path)
        submission_video_file.save(orig_path)

        ffprobe_bin = shutil.which("ffprobe")
        if ffprobe_bin:
            probe_cmd = [
                ffprobe_bin,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=p=0",
                orig_path,
            ]
            try:
                probe = subprocess.run(
                    probe_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                dims = probe.stdout.decode().strip().split(",")
                if len(dims) == 2:
                    width, height = map(int, dims)
                    if width > MAX_VIDEO_WIDTH or height > MAX_VIDEO_HEIGHT:
                        os.remove(orig_path)
                        raise ValueError("Video dimensions exceed 1920x1080 limit")
            except subprocess.CalledProcessError as e:
                stderr_output = e.stderr.decode(errors="ignore") if e.stderr else ""
                current_app.logger.error("ffprobe failed: %s", stderr_output)
                os.remove(orig_path)
                raise ValueError("Invalid or corrupted video file") from e

        uploads_dir = os.path.join(current_app.static_folder, "videos", "verifications")
        os.makedirs(uploads_dir, exist_ok=True)

        if not ffmpeg_bin:
            current_app.logger.warning("ffmpeg not found, saving video without conversion")
            final_name = secure_filename(f"{uuid.uuid4()}.{ext}")
            final_path = os.path.join(uploads_dir, final_name)
            shutil.move(orig_path, final_path)
        else:
            final_name = secure_filename(f"{uuid.uuid4()}.mp4")
            final_path = os.path.join(uploads_dir, final_name)
            ffmpeg_cmd = [
                ffmpeg_bin,
                "-i",
                orig_path,
                "-vf",
                "scale='min(1280,iw)':-2",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "28",
                "-c:a",
                "aac",
                "-movflags",
                "faststart",
                "-y",
                final_path,
            ]
            current_app.logger.debug("Running ffmpeg command: %s", " ".join(ffmpeg_cmd))
            try:
                subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as e:
                stderr_output = e.stderr.decode(errors="ignore") if e.stderr else ""
                current_app.logger.error("ffmpeg failed: %s", stderr_output)
                os.remove(orig_path)
                current_app.logger.debug("Removed temporary upload %s", orig_path)
                raise ValueError("Invalid or corrupted video file") from e

            os.remove(orig_path)
            current_app.logger.debug("Removed temporary upload %s", orig_path)

            final_size = os.path.getsize(final_path)
            current_app.logger.debug("Compressed video size: %s bytes", final_size)
            if final_size > MAX_VIDEO_BYTES:
                os.remove(final_path)
                current_app.logger.debug("Compressed video exceeded max size and was deleted")
                raise ValueError("Video exceeds 25 MB limit after compression")

        gcs_url = _upload_to_gcs(final_path, os.path.join("videos", "verifications", final_name), content_type="video/mp4")
        if gcs_url:
            os.remove(final_path)
            return gcs_url

        return os.path.join("videos", "verifications", final_name)
    except Exception as e:
        current_app.logger.error(f"Failed to save video: {e}")
        raise


def public_media_url(path: str | None) -> str | None:
    """Return a validated public URL for media assets.

    Absolute URLs must include a scheme and host.  Relative paths are
    converted to a ``static`` endpoint URL.
    """
    if not path:
        return None

    if path.startswith("/static/"):
        return path

    if path.startswith(("http://", "https://")):
        parsed = urlparse(path)
        if parsed.netloc:
            return path
        return None

    filename = path.lstrip("/")
    filename = filename.removeprefix("static/")
    return url_for("static", filename=filename)


def delete_media_file(path: str | None) -> None:
    """Remove a locally stored or GCS-hosted media file."""
    if not path:
        return

    base_url = None
    bucket = current_app.config.get("GCS_BUCKET")
    gcs_base = current_app.config.get("GCS_BASE_URL")
    if bucket:
        base_url = gcs_base or f"https://storage.googleapis.com/{bucket}"

    if base_url and path.startswith(base_url + "/"):
        rel = path[len(base_url) + 1 :]
        _delete_from_gcs(rel)
        return

    local_path = path.lstrip("/")
    local_path = local_path.removeprefix("static/")
    full_path = os.path.join(current_app.static_folder, local_path)
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except OSError as exc:
            current_app.logger.warning("Failed to delete media file %s: %s", full_path, exc)


def save_sponsor_logo(image_file, old_filename=None):
    if not image_file or not image_file.filename:
        raise ValueError("Invalid file type or no file provided.")

    try:
        return save_image_file(
            image_file,
            os.path.join("images", "sponsors"),
            old_filename=old_filename,
        )
    except Exception as e:
        raise ValueError(f"Failed to save image: {e}") from e


def save_calendar_service_json(json_file, old_filename=None):
    if not json_file or not json_file.filename:
        raise ValueError("Invalid file type or no file provided.")

    try:
        return save_json_file(
            json_file,
            os.path.join("service_json"),
            old_filename=old_filename,
        )
    except Exception as e:
        raise ValueError(f"Failed to save file: {e}") from e
