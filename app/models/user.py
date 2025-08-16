import jwt
from datetime import datetime
from time import time
from urllib.parse import urlparse

from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import ARRAY, TEXT

from app.constants import UTC
from . import db, user_badges, user_games, followers


class UserQuest(db.Model):
    """Model representing a user's progress on a quest."""
    __tablename__ = 'user_quests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    quest_id = db.Column(db.Integer, db.ForeignKey('quest.id'), nullable=False, index=True)
    __table_args__ = (
        db.UniqueConstraint('user_id', 'quest_id', name='uq_user_quest'),
    )
    completions = db.Column(db.Integer, default=0)
    points_awarded = db.Column(db.Integer, default=0)
    completed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )
    quest = db.relationship('Quest', back_populates='user_quests')


class User(UserMixin, db.Model):
    """Model representing an application user."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(512))
    is_admin = db.Column(db.Boolean, default=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))
    license_agreed = db.Column(db.Boolean, nullable=False)
    user_quests = db.relationship(
        'UserQuest', backref='user', lazy='dynamic',
        cascade='all, delete-orphan'
    )
    badges = db.relationship(
        'Badge', secondary=user_badges, lazy='subquery',
        backref=db.backref('users', lazy=True)
    )
    score = db.Column(db.Integer, default=0)
    participated_games = db.relationship(
        'Game', secondary='user_games', lazy='subquery',
        backref=db.backref('game_participants', lazy=True)
    )
    display_name = db.Column(db.String(100))
    profile_picture = db.Column(db.String(200))
    age_group = db.Column(db.String(50))
    timezone = db.Column(db.String(50), default="UTC", nullable=False)
    interests = db.Column(db.String(500))
    quest_likes = db.relationship(
        'QuestLike', backref='user', lazy='dynamic',
        cascade='all, delete-orphan'
    )
    email_verified = db.Column(db.Boolean, default=False)
    shoutboard_messages = db.relationship(
        'ShoutBoardMessage', backref='user', lazy='dynamic',
        cascade='all, delete-orphan'
    )
    quest_submissions = db.relationship(
        'QuestSubmission', backref='submitter', lazy='dynamic',
        cascade='all, delete-orphan'
    )

    riding_preferences = db.Column(
        db.JSON().with_variant(ARRAY(TEXT), 'postgresql'),
        nullable=True,
        default=list,
    )
    ride_description = db.Column(db.String(500), nullable=True)
    bike_picture = db.Column(db.String(200), nullable=True)
    bike_description = db.Column(db.String(500), nullable=True)
    upload_to_socials = db.Column(db.Boolean, default=True)
    upload_to_mastodon = db.Column(db.Boolean, default=False)
    storage_limit_gb = db.Column(db.Integer, nullable=True)
    data_retention_days = db.Column(db.Integer, default=0)
    show_carbon_game = db.Column(db.Boolean, default=True)
    onboarded = db.Column(db.Boolean, default=False, nullable=True)
    selected_game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=True)

    mastodon_id = db.Column(db.String(64), nullable=True)
    mastodon_username = db.Column(db.String(64), nullable=True)
    mastodon_instance = db.Column(db.String(128), nullable=True)
    mastodon_access_token = db.Column(db.String(512), nullable=True)

    activitypub_id = db.Column(db.String(256), nullable=True)
    public_key = db.Column(db.Text, nullable=True)
    private_key = db.Column(db.Text, nullable=True)

    following = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followee_id == id),
        backref='followers'
    )
    notifications = db.relationship('Notification', back_populates='user')

    def ensure_activitypub_actor(self):
        """Ensure this user has a valid local ActivityPub actor."""
        if self.mastodon_id and self.mastodon_instance:
            return

        local_domain = current_app.config['LOCAL_DOMAIN']
        parsed = urlparse(self.activitypub_id or '')
        needs_id = not parsed.netloc or parsed.netloc != local_domain
        needs_keys = not self.private_key or not self.public_key

        if needs_keys:
            from app.activitypub_utils import generate_activitypub_keys

            public_key, private_key = generate_activitypub_keys()
            self.public_key = public_key
            self.private_key = private_key

        if needs_id:
            self.activitypub_id = f"https://{local_domain}/users/{self.username}"

        if needs_id or needs_keys:
            db.session.commit()

    def generate_verification_token(self, expiration=320000):
        """Generate a JWT token for email verification."""
        token = jwt.encode(
            {'verify_email': self.id, 'exp': time() + expiration},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return token

    @staticmethod
    def verify_verification_token(token):
        """Verify a JWT email verification token and return the associated user."""
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            user_id = payload['verify_email']
        except jwt.exceptions.InvalidTokenError:
            return None
        return db.session.get(User, user_id)

    def generate_reset_token(self, expiration=320000):
        """Generate a JWT token for password reset."""
        token = jwt.encode(
            {'reset_password': self.id, 'exp': time() + expiration},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return token

    @staticmethod
    def verify_reset_token(token):
        """Verify a JWT password reset token and return the associated user."""
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            user_id = payload['reset_password']
        except jwt.exceptions.InvalidTokenError:
            return None
        return db.session.get(User, user_id)

    def set_password(self, password):
        """Set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check the user's password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def is_already_liking(self, quest):
        """Return True if the user already likes the given quest."""
        from .quest import QuestLike
        return QuestLike.query.filter_by(
            user_id=self.id, quest_id=quest.id
        ).count() > 0

    def get_participated_games(self):
        """Return a list of games the user has participated in."""
        return [{'id': game.id, 'title': game.title}
                for game in self.participated_games]

    def delete_user(self):
        """Delete the user and all associated records."""
        for user_quest in self.user_quests:
            db.session.delete(user_quest)
        for quest_like in self.quest_likes:
            db.session.delete(quest_like)
        for message in self.shoutboard_messages:
            db.session.delete(message)
        for submission in self.quest_submissions:
            db.session.delete(submission)

        self.participated_games.clear()

        ProfileWallMessage.query.filter_by(author_id=self.id).delete(synchronize_session=False)
        ProfileWallMessage.query.filter_by(user_id=self.id).delete(synchronize_session=False)

        db.session.delete(self)
        db.session.commit()

    def get_score_for_game(self, game_id):
        """Retrieve the user's total score for a specific game."""
        from .quest import Quest
        total_score = (
            db.session.query(db.func.sum(UserQuest.points_awarded))
            .join(Quest, UserQuest.quest_id == Quest.id)
            .filter(
                UserQuest.user_id == self.id,
                Quest.game_id == game_id
            )
            .scalar() or 0
        )
        return total_score

    def is_admin_for_game(self, game_id):
        """Return ``True`` if the user can administer the given game.

        A user is considered an admin for a game if they either created the
        game, were explicitly added as an admin, or have super admin rights.
        """
        from .game import Game

        game = db.session.get(Game, game_id)
        return bool(
            game
            and (
                self.is_super_admin
                or self in game.admins
                or game.admin_id == self.id
            )
        )

    @property
    def unread_notifications_count(self):
        from .notification import Notification
        return Notification.query.filter_by(
            user_id=self.id,
            is_read=False
        ).count()


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String, nullable=False)
    payload = db.Column(db.JSON, nullable=False)

    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user = db.relationship('User', back_populates='notifications')


class UserIP(db.Model):
    """Model representing a user's IP address log."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user = db.relationship('User', backref='ip_addresses')


class ActivityStore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    json = db.Column(db.JSON, nullable=False)
    published = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class ProfileWallMessage(db.Model):
    """Model representing a profile wall message."""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )
    author_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )
    parent_id = db.Column(
        db.Integer, db.ForeignKey('profile_wall_message.id', ondelete='CASCADE'),
        nullable=True
    )

    user = db.relationship(
        'User',
        foreign_keys=[user_id],
        backref=db.backref('profile_messages_received',
                           cascade='all, delete-orphan')
    )
    author = db.relationship(
        'User',
        foreign_keys=[author_id],
        backref=db.backref('profile_messages_sent',
                           cascade='all, delete-orphan')
    )
    replies = db.relationship(
        'ProfileWallMessage',
        backref=db.backref('parent', remote_side=[id]),
        cascade='all, delete-orphan'
    )


class PushSubscription(db.Model):
    """Web Push subscription details for a user."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    endpoint = db.Column(db.String, nullable=False)
    p256dh = db.Column(db.String, nullable=False)
    auth = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user = db.relationship('User', backref=db.backref('push_subscriptions', cascade='all, delete-orphan'))

