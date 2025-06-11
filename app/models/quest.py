from datetime import datetime

from app.constants import UTC
from . import db


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
        cascade='all, delete', passive_deletes=True
    )
    category = db.Column(db.String(50), nullable=True)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=True)
    submissions = db.relationship(
        'QuestSubmission', back_populates='quest',
        cascade='all, delete-orphan'
    )
    likes = db.relationship(
        'QuestLike', backref='quest',
        cascade='all, delete-orphan'
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
    video_url = db.Column(db.String(500), nullable=True)
    comment = db.Column(db.String(1000), nullable=True)
    timestamp = db.Column(
        db.DateTime(timezone=True), index=True, default=lambda: datetime.now(UTC)
    )
    twitter_url = db.Column(db.String(1024), nullable=True)
    fb_url = db.Column(db.String(1024), nullable=True)
    instagram_url = db.Column(db.String(1024), nullable=True)

    quest = db.relationship(
        'Quest', back_populates='submissions'
    )
    user = db.relationship(
        'User', back_populates='quest_submissions', overlaps='submitter'
    )


class SubmissionLike(db.Model):
    """A like on a specific QuestSubmission."""
    __tablename__ = 'submission_likes'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer,
        db.ForeignKey('quest_submission.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    timestamp = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint('submission_id', 'user_id',
                            name='uq_submission_user_like'),
    )

    submission = db.relationship(
        'QuestSubmission',
        back_populates='likes'
    )
    user = db.relationship('User', backref='submission_likes')


class SubmissionReply(db.Model):
    """A user reply (comment) on a QuestSubmission."""
    __tablename__ = 'submission_replies'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(
        db.Integer,
        db.ForeignKey('quest_submission.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    content = db.Column(db.String(1000), nullable=False)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True
    )

    submission = db.relationship(
        'QuestSubmission',
        back_populates='replies'
    )
    user = db.relationship('User', backref='submission_replies')


QuestSubmission.likes = db.relationship(
    'SubmissionLike',
    back_populates='submission',
    lazy='dynamic',
    cascade='all, delete-orphan',
    single_parent=True
)

QuestSubmission.replies = db.relationship(
    'SubmissionReply',
    back_populates='submission',
    lazy='dynamic',
    cascade='all, delete-orphan',
    single_parent=True
)

