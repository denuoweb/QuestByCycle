import random
import string
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.exc import IntegrityError

from app.constants import UTC
from . import db, game_admins


class Game(db.Model):
    """Model representing a game."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(1000))
    description2 = db.Column(db.String(4500))
    start_date = db.Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC)
    )
    end_date = db.Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC)
    )
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    admins = db.relationship(
        'User', secondary=game_admins,
        backref=db.backref('admin_games', lazy='dynamic')
    )
    quests = db.relationship(
        'Quest', back_populates='game',
        cascade='all, delete-orphan', lazy='dynamic'
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
    calendar_url = db.Column(db.String(500), nullable=True)
    custom_game_code = db.Column(db.String(20), unique=True, nullable=True)
    is_public = db.Column(db.Boolean, default=True)
    allow_joins = db.Column(db.Boolean, default=True)
    is_demo = db.Column(db.Boolean, default=False)
    social_media_liaison_email = db.Column(db.String(255), nullable=True)
    social_media_email_frequency = db.Column(db.String(50), default='weekly', nullable=True)
    last_social_media_email_sent = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=True)

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
        db.DateTime(timezone=True), index=True, default=lambda: datetime.now(UTC)
    )
    is_pinned = db.Column(db.Boolean, default=False)


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

