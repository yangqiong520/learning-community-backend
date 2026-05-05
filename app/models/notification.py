from libs.db import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='接收者ID')
    type = db.Column(db.Enum('message', 'assignment', 'system'), nullable=False, comment='通知类型')
    title = db.Column(db.String(100), nullable=False, comment='通知标题')
    content = db.Column(db.Text, comment='通知内容')
    conversation_id = db.Column(db.BigInteger, comment='关联会话ID')
    related_id = db.Column(db.BigInteger, comment='关联ID')
    is_read = db.Column(db.Boolean, default=False, comment='是否已读')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    user = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'content': self.content,
            'conversation_id': self.conversation_id,
            'related_id': self.related_id,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
