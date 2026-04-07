from libs.db import db
from datetime import datetime

class HomeworkType(db.Model):
    __tablename__ = 'homework_types'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        from app.models.course import Course
        course = Course.query.get(self.course_id) if self.course_id else None
        
        return {
            'id': self.id,
            'type_id': self.id,  # 添加 type_id 别名
            'type_name': self.name,  # 添加 type_name 别名
            'course_id': self.course_id,
            'course_name': course.name if course else '',  # 添加 course_name
            'name': self.name,
            'content': self.content,
            'teacher_id': self.teacher_id,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Homework(db.Model):
    __tablename__ = 'homeworks'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    homework_type_id = db.Column(db.Integer, db.ForeignKey('homework_types.id'), nullable=False)
    current_version_id = db.Column(db.Integer)
    status = db.Column(db.String(20), default='draft')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_RETURNED = 'returned'
    STATUS_EXCELLENT = 'excellent'
    STATUS_PROBLEM = 'problem'

    def to_dict(self, include_version=True):
        result = {
            'id': self.id,
            'student_id': self.student_id,
            'course_id': self.course_id,
            'homework_type_id': self.homework_type_id,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
        if include_version and self.current_version_id:
            from app.models.homework import HomeworkVersion
            version = HomeworkVersion.query.get(self.current_version_id)
            if version:
                result.update(version.to_dict())
        return result

class HomeworkVersion(db.Model):
    __tablename__ = 'homework_versions'

    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer, db.ForeignKey('homeworks.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    file_file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    pdf_file_id = db.Column(db.Integer, db.ForeignKey('files.id'))
    img_file_id = db.Column(db.Integer, db.ForeignKey('files.id'))
    evaluation = db.Column(db.Text)
    score = db.Column(db.String(50))
    is_redo = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        from app.models.file import File
        file = File.query.get(self.file_file_id) if self.file_file_id else None
        pdf_file = File.query.get(self.pdf_file_id) if self.pdf_file_id else None
        img_file = File.query.get(self.img_file_id) if self.img_file_id else None

        return {
            'id': self.id,
            'homework_id': self.homework_id,
            'version_number': self.version_number,
            'file_url': f'/api/v2/files/serve/{self.file_file_id}' if file else '',
            'pdf_url': f'/api/v2/files/serve/{self.pdf_file_id}' if pdf_file else '',
            'img_url': f'/api/v2/files/serve-image/{self.img_file_id}' if img_file else '',
            'evaluation': self.evaluation,
            'score': self.score,
            'is_redo': self.is_redo,
            'submitted_at': self.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if self.submitted_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class ExcellentHomework(db.Model):
    __tablename__ = 'excellent_homeworks'

    id = db.Column(db.Integer, primary_key=True)
    homework_version_id = db.Column(db.Integer, db.ForeignKey('homework_versions.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    likes_count = db.Column(db.Integer, default=0)

    def to_dict(self, user_id=None):
        from app.models.homework import HomeworkVersion, Homework
        from app.models.user import User
        from app.models.course import Course
        from app.models.file import File
        from app.models.homework_like import HomeworkLike

        version = HomeworkVersion.query.get(self.homework_version_id) if self.homework_version_id else None
        if not version:
            return None

        homework = Homework.query.get(version.homework_id) if version.homework_id else None
        if not homework:
            return None

        student = User.query.get(homework.student_id) if homework.student_id else None
        course = Course.query.get(homework.course_id) if homework.course_id else None
        homework_type = HomeworkType.query.get(homework.homework_type_id) if homework.homework_type_id else None

        file = File.query.get(version.file_file_id) if version.file_file_id else None
        pdf_file = File.query.get(version.pdf_file_id) if version.pdf_file_id else None

        is_liked = False
        if user_id:
            like = HomeworkLike.query.filter_by(
                user_id=user_id,
                excellent_homework_id=self.id,
                is_liked=True
            ).first()
            is_liked = like is not None

        # 优先使用 PDF，其次使用预览图，最后使用原始文件
        preview_url = pdf_file.file_path if pdf_file else None
        if not preview_url and version.img_file_id:
            img_file = File.query.get(version.img_file_id)
            preview_url = img_file.file_path if img_file else None
        if not preview_url:
            preview_url = file.file_path if file else ''

        return {
            'id': self.id,
            'title': f"{course.name if course else ''}的{homework_type.name if homework_type else ''}",
            'student_name': student.username if student else '',
            'student_id': homework.student_id,
            'content': preview_url,  # 优先使用 PDF 或预览图
            'file_url': f'/api/v2/files/serve/{version.file_file_id}' if file else '',
            'pdf_url': f'/api/v2/files/serve/{version.pdf_file_id}' if pdf_file else '',
            'img_url': f'/api/v2/files/serve-image/{version.img_file_id}' if version.img_file_id else '',
            'imgurl': f'/api/v2/files/serve-image/{version.img_file_id}' if version.img_file_id else '',
            'time': self.created_at.strftime('%Y.%m.%d') if self.created_at else None,
            'score': version.score,
            'like': is_liked,
            'likes_count': self.likes_count
        }

class ProblemHomework(db.Model):
    __tablename__ = 'problem_homeworks'

    id = db.Column(db.Integer, primary_key=True)
    homework_version_id = db.Column(db.Integer, db.ForeignKey('homework_versions.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        from app.models.homework import HomeworkVersion, Homework
        from app.models.user import User
        from app.models.course import Course
        from app.models.file import File

        version = HomeworkVersion.query.get(self.homework_version_id) if self.homework_version_id else None
        if not version:
            return None

        homework = Homework.query.get(version.homework_id) if version.homework_id else None
        if not homework:
            return None

        student = User.query.get(homework.student_id) if homework.student_id else None
        course = Course.query.get(homework.course_id) if homework.course_id else None
        homework_type = HomeworkType.query.get(homework.homework_type_id) if homework.homework_type_id else None

        file = File.query.get(version.file_file_id) if version.file_file_id else None
        pdf_file = File.query.get(version.pdf_file_id) if version.pdf_file_id else None

        return {
            'id': self.id,
            'homework_id': homework.id,
            'student_id': homework.student_id,
            'student_name': student.username if student else '',
            'course_name': course.name if course else '',
            'type_name': homework_type.name if homework_type else '',
            'version': version.version_number,
            'file_url': f'/api/v2/files/serve/{version.file_file_id}' if file else '',
            'pdf_url': f'/api/v2/files/serve/{version.pdf_file_id}' if pdf_file else '',
            'evaluation': version.evaluation,
            'score': version.score,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
