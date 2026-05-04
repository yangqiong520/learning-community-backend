from libs.db import db
from datetime import datetime
from app.models.like import Like
from app.models.file import File

class SmartResource(db.Model):
    __tablename__ = 'smart_resources'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    video_file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    thumbnail_file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    duration = db.Column(db.Integer, nullable=False, default=0)
    play_count = db.Column(db.Integer, nullable=False, default=0)
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    video_file = db.relationship('File', foreign_keys=[video_file_id])
    thumbnail_file = db.relationship('File', foreign_keys=[thumbnail_file_id])
    uploader = db.relationship('User', foreign_keys=[uploader_id])
    likes = db.relationship('Like', backref='smart_resource', cascade='all, delete-orphan')

    @staticmethod
    def format_play_count(count):
        if count >= 10000:
            return f'{count / 10000:.1f}万'
        return str(count)

    @staticmethod
    def format_duration(seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f'{hours:02d}:{minutes:02d}:{secs:02d}'

    def to_dict(self, user_id=None):
        is_liked = False
        if user_id:
            is_liked = Like.query.filter_by(
                smart_resource_id=self.id,
                user_id=user_id
            ).first() is not None

        return {
            'id': self.id,
            'video_url': f'/api/v2/files/serve-video/{self.video_file_id}' if self.video_file_id else '',
            'thumbnail_url': f'/api/v2/files/serve-image/{self.thumbnail_file_id}' if self.thumbnail_file_id else '',
            'play_count': self.format_play_count(self.play_count),
            'duration': self.format_duration(self.duration),
            'title': self.title,
            'uploader': self.uploader.username if self.uploader else 'Unknown',
            'time': self.created_at.strftime('%Y-%m-%d') if self.created_at else None,
            'is_liked': is_liked
        }
