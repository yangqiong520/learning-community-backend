from libs.db import db
from datetime import datetime
from app.models.file import File
from app.models.user import User


class TeachingPlan(db.Model):
    """教学计划模型"""
    __tablename__ = 'teaching_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    file_file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    image_file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    likes_count = db.Column(db.Integer, default=0, nullable=False)
    
    def to_dict(self, user_id=None):
        """转换为字典格式"""
        from app.models.like import Like

        file_file = File.query.get(self.file_file_id) if self.file_file_id else None
        image_file = File.query.get(self.image_file_id) if self.image_file_id else None
        uploader = User.query.get(self.uploader_id) if self.uploader_id else None

        is_liked = Like.query.filter_by(
            teaching_plan_id=self.id,
            user_id=user_id
        ).first() is not None if user_id else False

        result = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'file_id': file_file.id if file_file else None,
            'file_url': f'/api/v2/files/serve/{file_file.id}' if file_file else '',
            'image_file_id': image_file.id if image_file else None,
            'imgurl': f'/api/v2/files/serve-image/{image_file.id}' if image_file else '',
            'uploader': uploader.username if uploader else '',
            'time': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'like': is_liked
        }

        # 添加PDF文件信息
        if file_file and file_file.pdf_file_id:
            pdf_file = File.query.get(file_file.pdf_file_id)
            if pdf_file and pdf_file.is_active:
                result['pdf_file_id'] = pdf_file.id
                result['pdf_url'] = f'/api/v2/files/serve/{pdf_file.id}'

        return result
