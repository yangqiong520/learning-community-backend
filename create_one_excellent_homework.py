"""
创建1条优秀作业测试数据
"""

from flask import Flask
from libs.db import db
from app.models.user import User
from app.models.course import Course
from app.models.homework import HomeworkType, Homework, HomeworkVersion, ExcellentHomework
from app.models.file import File
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/learning_community?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
db.init_app(app)

def create_excellent_homework():
    """创建1条优秀作业"""
    with app.app_context():
        print("=" * 60)
        print("开始创建1条优秀作业测试数据")
        print("=" * 60)

        # 1. 获取学生和教师
        print("\n[1/5] 查找学生和教师...")
        student = User.query.filter(User.role.in_([3, 4])).first()
        teacher = User.query.filter_by(role=3).first()

        if not student:
            student = User(
                username='test_student',
                phone='13800138888',
                password='123456',
                role=4
            )
            db.session.add(student)
            db.session.flush()
            print(f"[OK] 创建测试学生: ID={student.id}")
        else:
            print(f"[OK] 找到学生: ID={student.id}")

        if not teacher:
            print(f"[ERROR] 未找到教师用户")
            return
        else:
            print(f"[OK] 找到教师: ID={teacher.id}")

        # 2. 创建或获取课程
        print("\n[2/5] 创建/获取课程...")
        course = Course.query.filter_by(name='数字特效', teacher_id=teacher.id).first()
        if not course:
            course = Course(
                name='数字特效',
                teacher_id=teacher.id,
                description='数字特效课程'
            )
            db.session.add(course)
            db.session.flush()
            print(f"[OK] 创建课程: ID={course.id}")
        else:
            print(f"[OK] 找到课程: ID={course.id}")

        # 3. 创建或获取作业类型
        print("\n[3/5] 创建/获取作业类型...")
        homework_type = HomeworkType.query.filter_by(
            course_id=course.id,
            name='期末作业'
        ).first()

        if not homework_type:
            homework_type = HomeworkType(
                course_id=course.id,
                name='期末作业',
                content='数字特效期末作业',
                teacher_id=teacher.id
            )
            db.session.add(homework_type)
            db.session.flush()
            print(f"[OK] 创建作业类型: ID={homework_type.id}")
        else:
            print(f"[OK] 找到作业类型: ID={homework_type.id}")

        # 4. 创建或获取作业和作业版本
        print("\n[4/5] 创建/获取作业和作业版本...")
        docx_path = 'img/test_all.docx'

        # 检查文件
        if os.path.exists(docx_path):
            file_record = File.query.filter_by(original_filename='test_all.docx').first()
            if not file_record:
                file_record = File(
                    original_filename='test_all.docx',
                    filename='test_all.docx',
                    file_path=docx_path,
                    file_size=os.path.getsize(docx_path),
                    file_type='document',
                    uploader_id=student.id
                )
                db.session.add(file_record)
                db.session.flush()
            print(f"[OK] 文件准备: ID={file_record.id}")
        else:
            print(f"[ERROR] 文件不存在: {docx_path}")
            return

        # 创建作业
        homework = Homework.query.filter_by(
            student_id=student.id,
            course_id=course.id,
            homework_type_id=homework_type.id
        ).first()

        if not homework:
            homework = Homework(
                student_id=student.id,
                course_id=course.id,
                homework_type_id=homework_type.id,
                status='submitted'
            )
            db.session.add(homework)
            db.session.flush()
            print(f"[OK] 创建作业: ID={homework.id}")
        else:
            print(f"[OK] 找到作业: ID={homework.id}")

        # 创建或获取作业版本
        homework_version = HomeworkVersion.query.filter_by(
            homework_id=homework.id,
            version_number=1
        ).first()

        if not homework_version:
            homework_version = HomeworkVersion(
                homework_id=homework.id,
                version_number=1,
                file_file_id=file_record.id,
                evaluation='优秀',
                score='100',
                is_redo=False
            )
            db.session.add(homework_version)
            db.session.flush()
            print(f"[OK] 创建作业版本: ID={homework_version.id}")
        else:
            print(f"[OK] 找到作业版本: ID={homework_version.id}")

        # 5. 创建1条优秀作业
        print("\n[5/5] 创建优秀作业...")
        excellent = ExcellentHomework(
            homework_version_id=homework_version.id,
            teacher_id=teacher.id,
            likes_count=0
        )
        db.session.add(excellent)
        db.session.flush()
        print(f"[OK] 创建优秀作业: ID={excellent.id}, 作业版本ID={homework_version.id}")

        db.session.commit()

        print("\n" + "=" * 60)
        print("[OK] 优秀作业测试数据创建完成！")
        print("=" * 60)

        # 显示统计
        print("\n当前数据统计：")
        print(f"  优秀作业数量: {db.session.query(ExcellentHomework).count()}")

if __name__ == '__main__':
    print("=" * 60)
    print("优秀作业测试数据创建工具")
    print("=" * 60)
    print()
    print("[INFO] 此操作将创建：")
    print("  - 1条优秀作业记录（使用test_all.docx）")
    print()
    print("[INFO] 如果课程或作业类型已存在，将复用")
    print()
    confirm = input("确认创建吗？(输入 'yes' 确认): ")

    if confirm.lower() == 'yes':
        create_excellent_homework()
    else:
        print("操作已取消")
