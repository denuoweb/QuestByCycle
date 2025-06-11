from flask_sqlalchemy import SQLAlchemy
from app.constants import UTC
from datetime import datetime

db = SQLAlchemy()

user_badges = db.Table(
    'user_badges',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('badge_id', db.Integer, db.ForeignKey('badge.id'), primary_key=True),
)

user_games = db.Table(
    'user_games',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('game_id', db.Integer, db.ForeignKey('game.id'), primary_key=True),
    db.Column('joined_at', db.DateTime(timezone=True), default=lambda: datetime.now(UTC)),
)

game_participants = db.Table(
    'game_participants',
    db.Column('game_id', db.Integer, db.ForeignKey('game.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
)

game_admins = db.Table(
    'game_admins',
    db.Column('game_id', db.Integer, db.ForeignKey('game.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
)

followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('followee_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
)

from .badge import Badge
from .user import (
    User,
    UserQuest,
    Notification,
    UserIP,
    ActivityStore,
    ProfileWallMessage,
    PushSubscription,
)
from .quest import Quest, QuestLike, QuestSubmission, SubmissionLike, SubmissionReply
from .game import Game, ShoutBoardMessage, Sponsor

__all__ = [
    'db',
    'Badge',
    'UserQuest',
    'User',
    'Notification',
    'UserIP',
    'ActivityStore',
    'ProfileWallMessage',
    'PushSubscription',
    'Quest',
    'QuestLike',
    'QuestSubmission',
    'SubmissionLike',
    'SubmissionReply',
    'Game',
    'ShoutBoardMessage',
    'Sponsor',
    'user_badges',
    'user_games',
    'game_participants',
    'game_admins',
    'followers',
]

