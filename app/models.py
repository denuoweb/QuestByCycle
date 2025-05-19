# pylint: disable=too-few-public-methods, import-error, useless-super-delegation, broad-except

import random
import string
import jwt
from pytz import utc
from datetime import datetime
from time import time
from flask import current_app  # pylint: disable=import-error
from flask_sqlalchemy import SQLAlchemy  # pylint: disable=import-error
from flask_login import UserMixin  # pylint: disable=import-error
from werkzeug.security import generate_password_hash, check_password_hash  # pylint: disable=import-error
from sqlalchemy.exc import IntegrityError  # pylint: disable=import-error
from sqlalchemy.dialects.postgresql import ARRAY, TEXT
from sqlalchemy import DateTime 

db = SQLAlchemy()

# -----------------------------------------------------------------------------
# Association Tables
# -----------------------------------------------------------------------------
user_badges = db.Table('user_badges',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id'), primary_key=True)
)

user_games = db.Table('user_games',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('game_id', db.Integer, db.ForeignKey('game.id'), primary_key=True),
    db.Column('joined_at', db.DateTime(timezone=True), default=lambda: datetime.now(utc))
)

game_participants = db.Table('game_participants',
    db.Column('game_id', db.Integer, db.ForeignKey('game.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('followee_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class Badge(db.Model):
    """Model representing a badge."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    image = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(150), nullable=True)

    quests = db.relationship('Quest', backref='badge', lazy=True)


class UserQuest(db.Model):
    """Model representing a user's progress on a quest."""
    __tablename__ = 'user_quests'
    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    quest_id = db.Column(db.Integer, db.ForeignKey('quest.id'), nullable=False, index=True)
    __table_args__ = (
        db.UniqueConstraint('user_id', 'quest_id', name='uq_user_quest'),
    )
    completions = db.Column(db.Integer, default=0)
    points_awarded = db.Column(db.Integer, default=0)
    completed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(utc)
    )
    quest = db.relationship("Quest", back_populates="user_quests")


class User(UserMixin, db.Model):
    """Model representing an application user."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(512))
    is_admin = db.Column(db.Boolean, default=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(utc))
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
    riding_preferences = db.Column(ARRAY(TEXT), nullable=True, default=list)
    ride_description = db.Column(db.String(500), nullable=True)
    bike_picture = db.Column(db.String(200), nullable=True)
    bike_description = db.Column(db.String(500), nullable=True)
    upload_to_socials = db.Column(db.Boolean, default=True)
    upload_to_mastodon = db.Column(db.Boolean, default=True)
    show_carbon_game = db.Column(db.Boolean, default=True)
    onboarded = db.Column(db.Boolean, default=False, nullable=True)
    selected_game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=True)

    # Fields for linking a Mastodon account
    mastodon_id = db.Column(db.String(64), nullable=True)
    mastodon_username = db.Column(db.String(64), nullable=True)
    mastodon_instance = db.Column(db.String(128), nullable=True)
    mastodon_access_token = db.Column(db.String(512), nullable=True)
    
    # Fields for the local ActivityPub actor (native QuestByCycle account)
    activitypub_id = db.Column(db.String(256), nullable=True)
    public_key = db.Column(db.Text, nullable=True)
    private_key = db.Column(db.Text, nullable=True)

    following = db.relationship(
      'User', secondary=followers,
      primaryjoin=(followers.c.follower_id==id),
      secondaryjoin=(followers.c.followee_id==id),
      backref='followers'
    )
    notifications = db.relationship('Notification', back_populates='user')

    def ensure_activitypub_actor(self):
        """
        Ensure that the user has a local ActivityPub actor record.
        For Mastodon users, if they are linked, activitypub_id should already be set to their
        Mastodon actor URL.
        """
        if not self.activitypub_id or not self.private_key or not self.public_key:
            from app.activitypub_utils import generate_activitypub_keys
            public_key, private_key = generate_activitypub_keys()
            local_domain = current_app.config["LOCAL_DOMAIN"]
            actor_url = f"https://{local_domain}/users/{self.username}"
            self.activitypub_id = actor_url
            self.public_key = public_key
            self.private_key = private_key
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
        return User.query.get(user_id)

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
        return User.query.get(user_id)

    def set_password(self, password):
        """Set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check the user's password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def is_already_liking(self, quest):
        """Return True if the user already likes the given quest."""
        return QuestLike.query.filter_by(
            user_id=self.id, quest_id=quest.id
        ).count() > 0

    def get_participated_games(self):
        """Return a list of games the user has participated in."""
        return [{'id': game.id, 'title': game.title}
                for game in self.participated_games]

    def delete_user(self):
        """Delete the user and all associated records."""
        ProfileWallMessage.query.filter_by(
            author_id=self.id
        ).delete(synchronize_session=False)
        ProfileWallMessage.query.filter_by(
            user_id=self.id
        ).delete(synchronize_session=False)

        for user_quest in self.user_quests:
            db.session.delete(user_quest)

        for quest_like in self.quest_likes:
            db.session.delete(quest_like)

        for message in self.shoutboard_messages:
            db.session.delete(message)

        for submission in self.quest_submissions:
            db.session.delete(submission)

        self.participated_games.clear()

        db.session.delete(self)
        db.session.commit()

    def get_score_for_game(self, game_id):
        """
        Retrieve the user's total score for a specific game.
        
        This method calculates the sum of points awarded for all quests completed
        by the user within the specified game.
        """
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


    @property
    def unread_notifications_count(self):
        # import here to avoid circular self-import at module load time
        from app.models import Notification
        return Notification.query.filter_by(
            user_id=self.id,
            is_read=False
        ).count()

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String, nullable=False)  # e.g. 'follow', 'submission'
    payload = db.Column(db.JSON, nullable=False)     # the raw activity or summary
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(utc))

    user = db.relationship('User', back_populates='notifications')


class UserIP(db.Model):
    """Model representing a user's IP address log."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(utc))

    user = db.relationship('User', backref='ip_addresses')


class ActivityStore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    json = db.Column(db.JSON, nullable=False)
    published = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(utc), nullable=False)


class Quest(db.Model):
    """Model representing a quest."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140))
    description = db.Column(db.String(2000))
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    evidence_url = db.Column(db.String(500))
    enabled = db.Column(db.Boolean, default=True)
    is_sponsored = db.Column(db.Boolean, default=False, nullable=False)
    verification_type = db.Column(db.String(50))
    verification_comment = db.Column(db.String(1000), default="")
    game_id = db.Column(
        db.Integer, db.ForeignKey('game.id', ondelete='CASCADE')
    )
    game = db.relationship('Game', back_populates='quests')
    points = db.Column(db.Integer, default=0)
    tips = db.Column(db.String(2000), default='', nullable=True)
    completion_limit = db.Column(db.Integer, default=1)
    frequency = db.Column(db.String(50), nullable=True)
    user_quests = db.relationship(
        'UserQuest', back_populates='quest',
        cascade="all, delete", passive_deletes=True
    )
    category = db.Column(db.String(50), nullable=True)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=True)
    submissions = db.relationship(
        'QuestSubmission', back_populates='quest',
        cascade='all, delete-orphan'
    )
    likes = db.relationship(
        'QuestLike', backref='quest',
        cascade="all, delete-orphan"
    )
    badge_awarded = db.Column(db.Integer, default=1)

    def __repr__(self):
        return f'<Quest {self.id}>'


class QuestLike(db.Model):
    """Model representing a like on a quest."""
    __tablename__ = 'quest_likes'
    id = db.Column(db.Integer, primary_key=True)
    quest_id = db.Column(
        db.Integer, db.ForeignKey('quest.id', ondelete='CASCADE'),
        nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint('quest_id', 'user_id', name='_quest_user_uc'),
    )


class Game(db.Model):
    """Model representing a game."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(1000))
    description2 = db.Column(db.String(1000))
    start_date = db.Column(
        DateTime(timezone=True),           # ← make it timezone-aware
        nullable=False,
        default=lambda: datetime.now(utc)   # ← callable default at runtime
    )
    end_date = db.Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(utc)
    )
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quests = db.relationship(
        'Quest', back_populates='game',
        cascade="all, delete-orphan", lazy='dynamic'
    )
    participants = db.relationship(
        'User', secondary='game_participants', lazy='subquery',
        backref=db.backref('games', lazy=True)
    )
    game_goal = db.Column(db.Integer)
    details = db.Column(db.Text)
    awards = db.Column(db.Text)
    beyond = db.Column(db.Text)
    sponsors = db.relationship(
        'Sponsor', back_populates='game',
        cascade='all, delete-orphan'
    )
    leaderboard_image = db.Column(db.String(500), nullable=True)
    twitter_username = db.Column(db.String(500), nullable=True)
    twitter_api_key = db.Column(db.String(500), nullable=True)
    twitter_api_secret = db.Column(db.String(500), nullable=True)
    twitter_access_token = db.Column(db.String(500), nullable=True)
    twitter_access_token_secret = db.Column(db.String(500), nullable=True)
    facebook_app_id = db.Column(db.String(500), nullable=True)
    facebook_app_secret = db.Column(db.String(500), nullable=True)
    facebook_access_token = db.Column(db.String(500), nullable=True)
    facebook_page_id = db.Column(db.String(500), nullable=True)
    instagram_user_id = db.Column(db.String(500), nullable=True)
    instagram_access_token = db.Column(db.String(500), nullable=True)
    custom_game_code = db.Column(db.String(20), unique=True, nullable=True)
    is_public = db.Column(db.Boolean, default=True)
    allow_joins = db.Column(db.Boolean, default=True)
    is_demo = db.Column(db.Boolean, default=False)
    social_media_liaison_email = db.Column(db.String(255), nullable=True)  
    social_media_email_frequency = db.Column(db.String(50), default='weekly', nullable=True)  
    last_social_media_email_sent = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(utc), nullable=True)

    @staticmethod
    def generate_unique_code():
        """Generate a unique game code."""
        while True:
            code = ''.join(random.choices(
                string.ascii_letters + string.digits, k=5
            ))
            if not Game.query.filter_by(custom_game_code=code).first():
                return code

    def __init__(self, **kwargs):
        """Initialize a Game with a unique game code."""
        super().__init__(**kwargs)
        if not self.custom_game_code:
            self.custom_game_code = self.generate_unique_code()
        else:
            while True:
                try:
                    self.custom_game_code = self.generate_unique_code()
                    db.session.add(self)
                    db.session.commit()
                    break
                except IntegrityError:
                    db.session.rollback()

    @property
    def twitter_url(self):
        """Return the Twitter URL for the game."""
        if self.twitter_username:
            return f"https://twitter.com/{self.twitter_username}"
        return "https://twitter.com/QuestByCycle"

    @property
    def facebook_url(self):
        """Return the Facebook URL for the game."""
        if self.facebook_page_id:
            return f"https://facebook.com/{self.facebook_page_id}"
        return "https://facebook.com/QuestByCycle"

    @property
    def instagram_url(self):
        """Return the Instagram URL for the game."""
        if self.instagram_user_id:
            return f"https://instagram.com/{self.instagram_user_id}"
        return "https://instagram.com/QuestByCycle"


class ShoutBoardMessage(db.Model):
    """Model representing a message on the shout board."""
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(2000), nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )
    game_id = db.Column(
        db.Integer, db.ForeignKey('game.id', ondelete='CASCADE'),
        nullable=False
    )
    timestamp = db.Column(
        db.DateTime, index=True, default=lambda: datetime.now(utc)
    )
    is_pinned = db.Column(db.Boolean, default=False)


class QuestSubmission(db.Model):
    """Model representing a quest submission."""
    id = db.Column(db.Integer, primary_key=True)
    quest_id = db.Column(
        db.Integer, db.ForeignKey('quest.id', ondelete='CASCADE'),
        nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )
    image_url = db.Column(db.String(500), nullable=True)
    comment = db.Column(db.String(1000), nullable=True)
    timestamp = db.Column(
        db.DateTime, index=True, default=lambda: datetime.now(utc)
    )
    twitter_url = db.Column(db.String(1024), nullable=True)
    fb_url = db.Column(db.String(1024), nullable=True)
    instagram_url = db.Column(db.String(1024), nullable=True)

    quest = db.relationship(
        'Quest', back_populates='submissions'
    )
    user = db.relationship(
        'User', back_populates='quest_submissions', overlaps="submitter"
    )


class Sponsor(db.Model):
    """Model representing a sponsor for a game."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    website = db.Column(db.String(255), nullable=True)
    logo = db.Column(db.String(255), nullable=True)
    description = db.Column(db.String(1000), nullable=True)
    tier = db.Column(db.String(255), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)

    game = db.relationship('Game', back_populates='sponsors')


class ProfileWallMessage(db.Model):
    """Model representing a profile wall message."""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(
        db.DateTime, default=lambda: datetime.now(utc), index=True
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
                           cascade="all, delete-orphan")
    )
    author = db.relationship(
        'User',
        foreign_keys=[author_id],
        backref=db.backref('profile_messages_sent',
                           cascade="all, delete-orphan")
    )
    replies = db.relationship(
        'ProfileWallMessage',
        backref=db.backref('parent', remote_side=[id]),
        cascade="all, delete-orphan"
    )


class SubmissionLike(db.Model):
    """A like on a specific QuestSubmission."""
    __tablename__ = 'submission_likes'

    id            = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer,
        db.ForeignKey('quest_submission.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    user_id       = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    timestamp     = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(utc),
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint('submission_id', 'user_id',
                            name='uq_submission_user_like'),
    )

    # NO cascade here on the "many" side:
    submission = db.relationship(
        'QuestSubmission',
        back_populates='likes'
    )
    user       = db.relationship('User', backref='submission_likes')


class SubmissionReply(db.Model):
    """A user reply (comment) on a QuestSubmission."""
    __tablename__ = 'submission_replies'

    id            = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer,
        db.ForeignKey('quest_submission.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    user_id       = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    content       = db.Column(db.String(1000), nullable=False)
    timestamp     = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(utc),
        nullable=False,
        index=True
    )

    submission = db.relationship(
        'QuestSubmission',
        back_populates='replies'
    )
    user       = db.relationship('User', backref='submission_replies')


QuestSubmission.likes = db.relationship(
    'SubmissionLike',
    back_populates='submission',
    lazy='dynamic',
    cascade='all, delete-orphan',
    single_parent=True          # this tells SQLAlchemy this child belongs to exactly one parent
)


QuestSubmission.replies = db.relationship(
    'SubmissionReply',
    back_populates='submission',
    lazy='dynamic',
    cascade='all, delete-orphan',
    single_parent=True
)