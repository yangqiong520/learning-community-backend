from libs.db import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    role = db.Column(db.Integer, nullable=False, default=3)
    user_img = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    ROLE_SUPER_ADMIN = 1
    ROLE_ADMIN = 2
    ROLE_TEACHER = 3
    ROLE_STUDENT = 4
    
    ROLE_NAMES = {
        ROLE_SUPER_ADMIN: '超级管理员',
        ROLE_ADMIN: '管理员',
        ROLE_TEACHER: '教师',
        ROLE_STUDENT: '学生'
    }
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'phone': self.phone,
            'role_id': self.role,
            'user_img': self.user_img or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
    
    def has_permission(self, target_role):
        return self.role <= target_role