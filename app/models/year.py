from libs.db import db
from datetime import datetime

class Year(db.Model):
    """年份模型"""
    __tablename__ = 'years'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(50), nullable=False)  # 例如：2024学年度
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 添加复合唯一约束：同一教师下年份唯一
    __table_args__ = (
        db.UniqueConstraint('year', 'teacher_id', name='uq_year_teacher'),
    )

    # 关联关系
    teacher = db.relationship('User', backref='years')

    def to_dict(self):
        return {
            'id': self.id,
            'year': self.year,
            'name': self.name,
            'is_active': self.is_active,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher.username if self.teacher else '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<Year {self.name}>'
