from . import db

class Badge(db.Model):
    """Model representing a badge."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    image = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(150), nullable=True)

    quests = db.relationship('Quest', backref='badge', lazy=True)


