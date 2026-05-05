from libs.db import db
from datetime import datetime

class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    type = db.Column(db.Enum('direct', 'group'), nullable=False, comment='会话类型')
    name = db.Column(db.String(100), comment='会话名称（群聊必填，一对一为NULL）')
    avatar = db.Column(db.String(500), comment='会话头像URL')
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), comment='创建者ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    deleted_at = db.Column(db.DateTime, nullable=True, comment='软删除时间')

    participants = db.relationship('ConversationParticipant', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys=[creator_id])

    def to_dict(self, current_user_id=None):
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'avatar': self.avatar,
            'creator_id': self.creator_id,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'updated_at': self.updated_at.isoformat() + 'Z' if self.updated_at else None
        }
