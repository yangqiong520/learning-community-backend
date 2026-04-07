from libs.db import db
from datetime import datetime

class HomeworkLike(db.Model):
    __tablename__ = 'homework_likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    excellent_homework_id = db.Column(db.Integer, db.ForeignKey('excellent_homeworks.id'), nullable=True)
    is_liked = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'excellent_homework_id', name='unique_homework_like'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'excellent_homework_id': self.excellent_homework_id,
            'is_liked': self.is_liked,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
