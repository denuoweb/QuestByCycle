"""Helpers for encrypting and decrypting sensitive application data."""
from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app
from sqlalchemy import String, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.types import TypeDecorator

ENCRYPTED_PREFIX = "ENC::"

_GAME_SECRET_COLUMNS: tuple[str, ...] = (
    "twitter_api_key",
    "twitter_api_secret",
    "twitter_access_token",
    "twitter_access_token_secret",
    "facebook_app_id",
    "facebook_app_secret",
    "facebook_access_token",
    "facebook_page_id",
    "instagram_user_id",
    "instagram_access_token",
)


def _normalize_value(value: str | bytes | memoryview | None) -> str | None:
    """Return a string representation suitable for encryption logic."""
    if value is None:
        return None
    if isinstance(value, memoryview):
        value = value.tobytes()
    if isinstance(value, bytes):
        return value.decode()
    return str(value)


@lru_cache(maxsize=2)
def _fernet_for_key(key: str) -> Fernet:
    """Return a cached Fernet instance for the provided key."""
    key_bytes = key.encode() if isinstance(key, str) else key
    return Fernet(key_bytes)


def _get_fernet() -> Fernet:
    """Return the Fernet instance configured for the current application."""
    key = current_app.config.get("DATA_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("DATA_ENCRYPTION_KEY is not configured.")
    return _fernet_for_key(key)


def encrypt_value(value: str) -> str:
    """Encrypt and mark a string value."""
    token = _get_fernet().encrypt(value.encode()).decode()
    return f"{ENCRYPTED_PREFIX}{token}"


def decrypt_value(value: str) -> str:
    """Decrypt a value previously produced by :func:`encrypt_value`."""
    token = value.removeprefix(ENCRYPTED_PREFIX)
    return _get_fernet().decrypt(token.encode()).decode()


class EncryptedString(TypeDecorator):
    """SQLAlchemy type that transparently encrypts and decrypts string values."""

    impl = String
    cache_ok = True

    def __init__(self, length: int = 1024):
        self.length = length
        super().__init__()

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(String(self.length))

    def process_bind_param(self, value, dialect):
        normalized = _normalize_value(value)
        if normalized in (None, ""):
            return value
        return encrypt_value(normalized)

    def process_result_value(self, value, dialect):
        normalized = _normalize_value(value)
        if normalized in (None, ""):
            return normalized

        if normalized.startswith(ENCRYPTED_PREFIX):
            try:
                return decrypt_value(normalized)
            except InvalidToken:
                current_app.logger.error("Failed to decrypt encrypted value.")
                return None

        return normalized


def encrypt_game_secrets_if_needed() -> int:
    """Encrypt any plaintext social credentials currently stored on games.

    Returns
    -------
    int
        Number of games updated.
    """
    from app.models import db  # Imported lazily to avoid circular imports.

    column_sql = ", ".join(_GAME_SECRET_COLUMNS)
    updated_games = 0

    try:
        connection = db.session.connection()
        rows = connection.execute(
            text(f"SELECT id, {column_sql} FROM game")
        ).mappings()

        for row in rows:
            updates = {}
            for column in _GAME_SECRET_COLUMNS:
                raw_value = _normalize_value(row.get(column))
                if not raw_value or raw_value.startswith(ENCRYPTED_PREFIX):
                    continue
                updates[column] = encrypt_value(raw_value)

            if not updates:
                continue

            updates["id"] = row["id"]
            set_clause = ", ".join(f"{col} = :{col}" for col in updates if col != "id")
            connection.execute(
                text(f"UPDATE game SET {set_clause} WHERE id = :id"),
                updates,
            )
            updated_games += 1

        if updated_games:
            db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        current_app.logger.error("Failed to backfill encrypted game secrets: %s", exc)
        return 0

    return updated_games
