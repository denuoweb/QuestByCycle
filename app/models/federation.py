"""Federation-related models: foreign actors and remote follower links.

This module defines lightweight SQLAlchemy models used by the ActivityPub
utilities to cache remote actors and map remote followers to local users.
"""
from __future__ import annotations

from datetime import datetime

from app.constants import UTC
from . import db


class ForeignActor(db.Model):
    """Cache for remote ActivityPub actors.

    Stores canonical actor URI, inbox URL, and the actor's public key PEM for
    signature verification. This avoids repeated remote fetches.
    """

    __tablename__ = "foreign_actor"

    id = db.Column(db.Integer, primary_key=True)
    actor_uri = db.Column(db.String(512), unique=True, nullable=False, index=True)
    canonical_uri = db.Column(db.String(512), nullable=True, index=True)
    inbox_url = db.Column(db.String(512), nullable=True)
    public_key_pem = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging convenience
        return (
            f"<ForeignActor id={self.id} actor_uri={self.actor_uri!r} "
            f"canonical_uri={self.canonical_uri!r}>"
        )


class RemoteFollower(db.Model):
    """A mapping of a local user being followed by a remote actor."""

    __tablename__ = "remote_follower"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    foreign_actor_id = db.Column(
        db.Integer, db.ForeignKey("foreign_actor.id", ondelete="CASCADE"), nullable=False, index=True
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "foreign_actor_id", name="uq_remote_follow"),
    )

    # ORM relationships for convenience and clearer queries. Keep DB-level
    # cascade via ondelete and mirror in ORM for in-session operations.
    user = db.relationship(
        "User",
        backref=db.backref("remote_followers", cascade="all, delete-orphan"),
        passive_deletes=True,
    )
    foreign_actor = db.relationship(
        "ForeignActor",
        backref=db.backref("remote_followers", cascade="all, delete-orphan"),
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging convenience
        return f"<RemoteFollower user_id={self.user_id} foreign_actor_id={self.foreign_actor_id}>"
