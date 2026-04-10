from libs.db import db
from datetime import datetime
from app.models.like import Like
from app.models.file import File
from app.models.user import User

class Textbook(db.Model):
    __tablename__ = 'textbooks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    document_file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    image_file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    document_file = db.relationship('File', foreign_keys=[document_file_id])
    image_file = db.relationship('File', foreign_keys=[image_file_id])
    uploader = db.relationship('User', foreign_keys=[uploader_id])
    likes = db.relationship('Like', backref='textbook', cascade='all, delete-orphan')
    
    def to_dict(self, user_id=None):
        is_liked = False
        if user_id:
            is_liked = Like.query.filter_by(
                textbook_id=self.id,
                user_id=user_id
            ).first() is not None
        
        result = {
            'id': self.id,
            'document_file_id': self.document_file_id,
            'file_url': f'/api/v2/files/serve/{self.document_file_id}' if self.document_file_id else '',
            'image_file_id': self.image_file_id,
            'imgurl': f'/api/v2/files/serve-image/{self.image_file_id}' if self.image_file_id else '',
            'title': self.title,
            'content': self.content,
            'time': self.created_at.strftime('%Y-%m-%d') if self.created_at else None,
            'like': is_liked
        }
        
        # 避免直接使用 User 模型，延迟加载 uploader 信息
        uploader = 'Unknown'
        if self.uploader_id:
            from app.models.user import User
            uploader_user = User.query.get(self.uploader_id)
            uploader = uploader_user.username if uploader_user else 'Unknown'

        # 添加PDF文件信息
        if self.document_file and self.document_file.pdf_file_id:
            pdf_file = File.query.get(self.document_file.pdf_file_id)
            if pdf_file and pdf_file.is_active:
                result['pdf_file_id'] = pdf_file.id
                result['pdf_url'] = f'/api/v2/files/serve/{pdf_file.id}'

        return result
