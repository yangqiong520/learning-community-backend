from libs.db import db
from datetime import datetime

class ConversationParticipant(db.Model):
    __tablename__ = 'conversation_participants'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.BigInteger, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.Enum('owner', 'admin', 'member'), default='member', comment='角色')
    nickname = db.Column(db.String(50), comment='群昵称')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, comment='加入时间')
    last_read_message_id = db.Column(db.BigInteger, comment='最后阅读的消息ID')
    unread_count = db.Column(db.Integer, default=0, comment='未读消息数')
    mute_until = db.Column(db.DateTime, nullable=True, comment='免打扰到期时间')
    left_at = db.Column(db.DateTime, nullable=True, comment='退出群时间')

    user = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'role': self.role,
            'nickname': self.nickname,
            'joined_at': self.joined_at.strftime('%Y-%m-%d %H:%M:%S') if self.joined_at else None,
            'last_read_message_id': self.last_read_message_id,
            'unread_count': self.unread_count,
            'mute_until': self.mute_until.strftime('%Y-%m-%d %H:%M:%S') if self.mute_until else None,
            'left_at': self.left_at.strftime('%Y-%m-%d %H:%M:%S') if self.left_at else None
        }
