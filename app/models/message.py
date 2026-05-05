from libs.db import db
from datetime import datetime

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.BigInteger, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    sender_username = db.Column(db.String(50), nullable=False, comment='发送者用户名')
    sender_avatar = db.Column(db.String(500), comment='发送者头像')
    message_type = db.Column(db.Enum('text', 'image', 'file'), nullable=False, comment='消息类型')
    content = db.Column(db.Text, comment='文本消息内容')
    file_url = db.Column(db.String(500), comment='文件URL')
    file_name = db.Column(db.String(255), comment='文件名')
    file_size = db.Column(db.BigInteger, comment='文件大小')
    reply_to_id = db.Column(db.BigInteger, comment='回复的消息ID')
    is_read = db.Column(db.Boolean, default=False, comment='是否已读')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否已删除')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='发送时间')

    sender = db.relationship('User', foreign_keys=[sender_id])

    def to_dict(self, display_name=None):
        data = {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'sender_username': self.sender_username,
            'sender_avatar': self.sender_avatar,
            'message_type': self.message_type,
            'is_read': self.is_read,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }
        
        if display_name:
            data['display_name'] = display_name
        
        if self.message_type == 'text' and self.content:
            data['content'] = self.content
        
        if self.message_type in ['image', 'file'] and self.file_url:
            data['file_url'] = self.file_url
            data['file_name'] = self.file_name
            if self.file_size:
                data['file_size'] = self.file_size
        
        if self.reply_to_id:
            data['reply_to_id'] = self.reply_to_id
        
        return data
