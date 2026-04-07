import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import flask
from flask import Flask, request
from flask_cors import CORS
import yaml
from libs.db import db, DATABASE_URI
from app.models.file import File
from app.models.user import User
from app.models.course import Course
from app.models.homework import Homework, HomeworkType, HomeworkVersion, ExcellentHomework
from datetime import datetime

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

app_config = config['app']

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 600
    }
})

db.init_app(app)

with app.app_context():
    db.create_all()
    
    doc_path = 'E:\\nodejs-project\\learning-community-backend\\img\\test_all.docx'
    pdf_path = 'E:\\nodejs-project\\learning-community-backend\\img\\test_all_two.pdf'
    image_path = 'E:\\nodejs-project\\learning-community-backend\\img\\test.png'

    if not os.path.exists(doc_path):
        print(f"[ERROR] Document file not found: {doc_path}")
        exit(1)

    if not os.path.exists(pdf_path):
        print(f"[ERROR] PDF file not found: {pdf_path}")
        exit(1)

    if not os.path.exists(image_path):
        print(f"[ERROR] Image file not found: {image_path}")
        exit(1)

    users = User.query.all()
    if not users:
        print("[INFO] No users found, creating test users...")
        
        teacher = User(
            username='yolo',
            phone='13800138000',
            password='123456',
            role=User.ROLE_TEACHER
        )
        db.session.add(teacher)
        
        student = User(
            username='newuser',
            phone='13800138001',
            password='123456',
            role=User.ROLE_STUDENT
        )
        db.session.add(student)
        
        db.session.commit()
        print("[OK] Test users created")
        users = User.query.all()
    else:
        print("[OK] Found existing users")

    teacher = None
    student = None
    
    for user in users:
        if user.role == User.ROLE_TEACHER:
            teacher = user
        elif user.role == User.ROLE_STUDENT:
            student = user

    if not teacher:
        print("[INFO] No teacher user found, creating...")
        teacher = User(
            username='yolo',
            phone='13800138000',
            password='123456',
            role=User.ROLE_TEACHER
        )
        db.session.add(teacher)
        db.session.commit()

    if not student:
        print("[INFO] No student user found, creating...")
        student = User(
            username='newuser',
            phone='13800138001',
            password='123456',
            role=User.ROLE_STUDENT
        )
        db.session.add(student)
        db.session.commit()

    print(f"[OK] Using teacher: {teacher.username} (ID: {teacher.id})")
    print(f"[OK] Using student: {student.username} (ID: {student.id})")

    course = Course.query.filter_by(name='数字特效').first()
    if not course:
        course = Course(
            name='数字特效',
            code='SE2024',
            teacher_id=teacher.id,
            description='数字特效课程'
        )
        db.session.add(course)
        db.session.commit()
        print(f"[OK] Course created: {course.name} (ID: {course.id})")
    else:
        print(f"[OK] Using existing course: {course.name} (ID: {course.id})")

    homework_type = HomeworkType.query.filter_by(
        course_id=course.id,
        name='平时作业1'
    ).first()
    if not homework_type:
        homework_type = HomeworkType(
            course_id=course.id,
            name='平时作业1',
            content='完成数字特效的基础练习，制作一个简单的动画效果',
            teacher_id=teacher.id
        )
        db.session.add(homework_type)
        db.session.commit()
        print(f"[OK] Homework type created: {homework_type.name} (ID: {homework_type.id})")
    else:
        print(f"[OK] Using existing homework type: {homework_type.name} (ID: {homework_type.id})")

    doc_file_record = File(
        filename='test_all.docx',
        original_filename='test_all.docx',
        file_type=File.FILE_TYPE_DOCUMENT,
        file_size=os.path.getsize(doc_path),
        file_path=doc_path,
        mime_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        uploader_id=student.id
    )
    db.session.add(doc_file_record)
    db.session.commit()
    db.session.refresh(doc_file_record)
    print(f"[OK] Document file created: {doc_file_record.id}")

    pdf_file_record = File(
        filename='test_all_two.pdf',
        original_filename='test_all_two.pdf',
        file_type=File.FILE_TYPE_DOCUMENT,
        file_size=os.path.getsize(pdf_path),
        file_path=pdf_path,
        mime_type='application/pdf',
        uploader_id=student.id
    )
    db.session.add(pdf_file_record)
    db.session.commit()
    db.session.refresh(pdf_file_record)
    print(f"[OK] PDF file created: {pdf_file_record.id}")

    image_file_record = File(
        filename='test.png',
        original_filename='test.png',
        file_type=File.FILE_TYPE_IMAGE,
        file_size=os.path.getsize(image_path),
        file_path=image_path,
        mime_type='image/png',
        uploader_id=student.id
    )
    db.session.add(image_file_record)
    db.session.commit()
    db.session.refresh(image_file_record)
    print(f"[OK] Image file created: {image_file_record.id}")

    homework = Homework.query.filter_by(
        student_id=student.id,
        homework_type_id=homework_type.id
    ).first()
    if not homework:
        homework = Homework(
            student_id=student.id,
            course_id=course.id,
            homework_type_id=homework_type.id,
            status=Homework.STATUS_SUBMITTED
        )
        db.session.add(homework)
        db.session.commit()
        print(f"[OK] Homework created: {homework.id}")
    else:
        print(f"[OK] Using existing homework: {homework.id}")

    homework_version = HomeworkVersion(
        homework_id=homework.id,
        version_number=1,
        file_file_id=doc_file_record.id,
        pdf_file_id=pdf_file_record.id,
        img_file_id=image_file_record.id,
        evaluation='优秀的作品，动画效果流畅，创意新颖',
        score='A',
        is_redo=False
    )
    db.session.add(homework_version)
    db.session.commit()
    db.session.refresh(homework_version)
    print(f"[OK] Homework version created: {homework_version.id}")

    homework.current_version_id = homework_version.id
    homework.status = Homework.STATUS_SUBMITTED
    db.session.commit()

    excellent_homework = ExcellentHomework.query.filter_by(
        homework_version_id=homework_version.id
    ).first()
    if not excellent_homework:
        excellent_homework = ExcellentHomework(
            homework_version_id=homework_version.id,
            teacher_id=teacher.id,
            likes_count=0
        )
        db.session.add(excellent_homework)
        db.session.commit()
        print(f"[OK] Excellent homework created: {excellent_homework.id}")
    else:
        print(f"[OK] Using existing excellent homework: {excellent_homework.id}")

    homework.status = Homework.STATUS_EXCELLENT
    db.session.commit()

    print("\n[SUCCESS] Excellent homework test data created successfully!")
    print(f"  - Student: {student.username}")
    print(f"  - Teacher: {teacher.username}")
    print(f"  - Course: {course.name}")
    print(f"  - Homework Type: {homework_type.name}")
    print(f"  - Homework ID: {homework.id}")
    print(f"  - Version ID: {homework_version.id}")
    print(f"  - Excellent Homework ID: {excellent_homework.id}")
