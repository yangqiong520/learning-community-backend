from libs.db import db
from datetime import datetime

class MessageRead(db.Model):
    __tablename__ = 'message_reads'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    message_id = db.Column(db.BigInteger, db.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    read_at = db.Column(db.DateTime, default=datetime.utcnow, comment='阅读时间')

    user = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'user_id': self.user_id,
            'read_at': self.read_at.strftime('%Y-%m-%d %H:%M:%S') if self.read_at else None
        }
