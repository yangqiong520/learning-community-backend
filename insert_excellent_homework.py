import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from flask_cors import CORS
import yaml
from libs.db import db, DATABASE_URI
from app.models.file import File
from app.models.user import User
from app.models.course import Course
from app.models.homework import Homework, HomeworkType, HomeworkVersion, ExcellentHomework

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
db.init_app(app)

with app.app_context():
    print("=" * 60)
    print("开始插入优秀作业数据")
    print("=" * 60)
    
    # 文件路径
    docx_path = 'E:/nodejs-project/learning-community-backend/img/test_all.docx'
    pdf_path = 'E:/nodejs-project/learning-community-backend/img/test_all_two.pdf'
    
    if not os.path.exists(docx_path):
        print(f"[ERROR] DOCX文件不存在: {docx_path}")
        exit(1)
    
    if not os.path.exists(pdf_path):
        print(f"[ERROR] PDF文件不存在: {pdf_path}")
        exit(1)
    
    print(f"[OK] DOCX文件: {os.path.basename(docx_path)}")
    print(f"[OK] PDF文件: {os.path.basename(pdf_path)}")
    
    # 检查或创建必要的数据
    print("\n[INFO] 检查必要数据...")
    
    # 1. 检查用户
    users = User.query.all()
    if not users:
        print("[INFO] 没有用户，需要创建...")
        teacher = User(
            username='yolo',
            phone='17326500773',
            password='123456',
            role=User.ROLE_TEACHER,
            user_img=None
        )
        db.session.add(teacher)
        
        student = User(
            username='newuser',
            phone='15680692521',
            password='123456',
            role=User.ROLE_STUDENT,
            user_img=None
        )
        db.session.add(student)
        db.session.commit()
        
        print(f"[OK] 创建教师: {teacher.username} (ID: {teacher.id})")
        print(f"[OK] 创建学生: {student.username} (ID: {student.id})")
        
        users = User.query.all()
    else:
        print(f"[OK] 现有 {len(users)} 个用户")
    
    # 获取教师和学生
    teacher = None
    student = None
    for user in users:
        if user.role == User.ROLE_TEACHER and teacher is None:
            teacher = user
        if user.role == User.ROLE_STUDENT and student is None:
            student = user
    
    if not teacher:
        print("[ERROR] 没有教师用户")
        exit(1)
    
    if not student:
        print("[ERROR] 没有学生用户")
        exit(1)
    
    print(f"[OK] 教师: {teacher.username} (ID: {teacher.id})")
    print(f"[OK] 学生: {student.username} (ID: {student.id})")
    
    # 2. 检查课程
    course = Course.query.filter_by(name='数字特效').first()
    if not course:
        print("[INFO] 创建课程...")
        course = Course(
            name='数字特效',
            code='SE2024',
            teacher_id=teacher.id,
            description='数字特效课程'
        )
        db.session.add(course)
        db.session.commit()
        print(f"[OK] 创建课程: {course.name} (ID: {course.id})")
    else:
        print(f"[OK] 现有课程: {course.name} (ID: {course.id})")
    
    # 3. 检查作业类型
    homework_type = HomeworkType.query.filter_by(
        course_id=course.id,
        name='平时作业1'
    ).first()
    
    if not homework_type:
        print("[INFO] 创建作业类型...")
        homework_type = HomeworkType(
            course_id=course.id,
            name='平时作业1',
            content='完成数字特效的基础练习，制作一个简单的动画效果',
            teacher_id=teacher.id
        )
        db.session.add(homework_type)
        db.session.commit()
        print(f"[OK] 创建作业类型: {homework_type.name} (ID: {homework_type.id})")
    else:
        print(f"[OK] 现有作业类型: {homework_type.name} (ID: {homework_type.id})")
    
    print("\n[INFO] 开始创建作业记录...")
    
    # 4. 创建文件记录
    print("[INFO] 创建文件记录...")
    
    docx_file = File(
        filename='test_all.docx',
        original_filename='test_all.docx',
        file_type=File.FILE_TYPE_DOCUMENT,
        file_size=os.path.getsize(docx_path),
        file_path=docx_path,
        mime_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        uploader_id=student.id
    )
    db.session.add(docx_file)
    db.session.flush()
    print(f"[OK] DOCX文件: {docx_file.id}")
    
    pdf_file = File(
        filename='test_all_two.pdf',
        original_filename='test_all_two.pdf',
        file_type=File.FILE_TYPE_DOCUMENT,
        file_size=os.path.getsize(pdf_path),
        file_path=pdf_path,
        mime_type='application/pdf',
        uploader_id=student.id
    )
    db.session.add(pdf_file)
    db.session.flush()
    print(f"[OK] PDF文件: {pdf_file.id}")
    
    # 5. 创建或获取作业记录
    print("[INFO] 创建或获取作业记录...")
    
    homework = Homework.query.filter_by(
        student_id=student.id,
        homework_type_id=homework_type.id
    ).first()
    
    if homework:
        print(f"[OK] 使用现有作业: {homework.id}")
    else:
        print("[INFO] 创建作业记录...")
        homework = Homework(
            student_id=student.id,
            course_id=course.id,
            homework_type_id=homework_type.id,
            status=Homework.STATUS_SUBMITTED
        )
        db.session.add(homework)
        db.session.flush()
        print(f"[OK] 创建作业: {homework.id}")
    
    # 6. 创建作业版本
    print("[INFO] 创建作业版本...")
    
    # 获取当前最大版本号
    max_version = db.session.query(db.func.max(HomeworkVersion.version_number)).filter_by(
        homework_id=homework.id
    ).scalar() or 0
    
    version = HomeworkVersion(
        homework_id=homework.id,
        version_number=max_version + 1,
        file_file_id=docx_file.id,
        pdf_file_id=pdf_file.id,
        img_file_id=None,  # 可以根据需要添加封面图
        evaluation='优秀的作品，动画效果流畅，创意新颖',
        score='A+',
        is_redo=False
    )
    db.session.add(version)
    db.session.flush()
    print(f"[OK] 创建版本: {version.id}")
    
    # 7. 更新作业记录
    homework.current_version_id = version.id
    homework.status = Homework.STATUS_SUBMITTED
    db.session.commit()
    print(f"[OK] 更新作业状态: {homework.status}")
    
    # 8. 创建优秀作业标记
    print("[INFO] 创建优秀作业标记...")
    
    excellent = ExcellentHomework.query.filter_by(
        homework_version_id=version.id
    ).first()
    
    if not excellent:
        excellent = ExcellentHomework(
            homework_version_id=version.id,
            teacher_id=teacher.id,
            likes_count=0
        )
        db.session.add(excellent)
        db.session.commit()
        print(f"[OK] 创建优秀作业: {excellent.id}")
    else:
        print(f"[OK] 优秀作业已存在: {excellent.id}")
    
    # 9. 更新作业状态为优秀
    homework.status = Homework.STATUS_EXCELLENT
    db.session.commit()
    print(f"[OK] 更新作业状态: {homework.status}")
    
    print("\n" + "=" * 60)
    print("优秀作业数据插入成功！")
    print("=" * 60)
    print(f"\n学生: {student.username}")
    print(f"教师: {teacher.username}")
    print(f"课程: {course.name}")
    print(f"作业类型: {homework_type.name}")
    print(f"作业ID: {homework.id}")
    print(f"版本号: {version.version_number}")
    print(f"优秀作业ID: {excellent.id}")
    print(f"\n文件:")
    print(f"  DOCX: test_all.docx (ID: {docx_file.id})")
    print(f"  PDF: test_all_two.pdf (ID: {pdf_file.id})")
    print(f"")
    print("现在可以通过以下API查看优秀作业:")
    print(f"GET /api/v2/homeworks/excellent")
    print(f"")
    print("=" * 60)
