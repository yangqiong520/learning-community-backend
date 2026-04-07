"""
创建5条相同的优秀作业测试数据（修复版）
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

def create_excellent_homeworks():
    """创建5条相同的优秀作业"""
    with app.app_context():
        print("=" * 60)
        print("开始创建5条优秀作业测试数据")
        print("=" * 60)

        # 1. 获取学生和教师
        print("\n[1/6] 查找学生和教师...")
        student = User.query.filter(User.role.in_([3, 4])).first()  # 教师或学生
        teacher = User.query.filter_by(role=3).first()  # 教师

        if not student:
            # 创建测试学生
            student = User(
                username='test_student',
                phone='13800138888',
                password='123456',
                role=4  # 学生
            )
            db.session.add(student)
            db.session.flush()
            print(f"[OK] 创建测试学生: ID={student.id}, 用户名={student.username}")
        else:
            print(f"[OK] 找到学生: ID={student.id}, 用户名={student.username}, 角色={student.role}")

        if not teacher:
            print(f"[ERROR] 未找到教师用户，请先创建教师用户")
            return
        else:
            print(f"[OK] 找到教师: ID={teacher.id}, 用户名={teacher.username}")

        # 2. 创建课程
        print("\n[2/6] 创建测试课程...")
        course = Course(
            name='数字特效',
            teacher_id=teacher.id,
            description='数字特效课程'
        )
        db.session.add(course)
        db.session.flush()
        print(f"[OK] 创建课程: ID={course.id}, 名称={course.name}")

        # 3. 创建作业类型
        print("\n[3/6] 创建作业类型...")
        homework_type = HomeworkType(
            course_id=course.id,
            name='期末作业',
            content='数字特效期末作业',
            teacher_id=teacher.id
        )
        db.session.add(homework_type)
        db.session.flush()
        print(f"[OK] 创建作业类型: ID={homework_type.id}, 名称={homework_type.name}")

        # 4. 上传文件
        print("\n[4/6] 上传测试文件...")
        docx_path = 'img/test_all.docx'
        if os.path.exists(docx_path):
            # 创建文件记录
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
            print(f"[OK] 文件上传成功: ID={file_record.id}, 文件名={file_record.original_filename}")
        else:
            print(f"[ERROR] 文件不存在: {docx_path}")
            return

        # 5. 创建作业和作业版本
        print("\n[5/6] 创建作业和作业版本...")
        homework = Homework(
            student_id=student.id,
            course_id=course.id,
            homework_type_id=homework_type.id,
            status='submitted'
        )
        db.session.add(homework)
        db.session.flush()

        # 创建作业版本
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
        print(f"[OK] 创建作业: ID={homework.id}")
        print(f"[OK] 创建作业版本: ID={homework_version.id}")

        # 6. 创建5条优秀作业
        print("\n[6/6] 创建5条优秀作业...")
        for i in range(5):
            excellent = ExcellentHomework(
                homework_version_id=homework_version.id,
                teacher_id=teacher.id,
                likes_count=0
            )
            db.session.add(excellent)
            print(f"[{i+1}/5] 创建优秀作业: ID={excellent.id}, 作业版本ID={homework_version.id}")

        db.session.commit()

        print("\n" + "=" * 60)
        print("[OK] 优秀作业测试数据创建完成！")
        print("=" * 60)

        # 显示统计
        print("\n当前数据统计：")
        print(f"  学生数量: {db.session.query(User).filter(User.role == 4).count()}")
        print(f"  教师数量: {db.session.query(User).filter(User.role == 3).count()}")
        print(f"  课程数量: {db.session.query(Course).count()}")
        print(f"  作业类型数量: {db.session.query(HomeworkType).count()}")
        print(f"  作业数量: {db.session.query(Homework).count()}")
        print(f"  作业版本数量: {db.session.query(HomeworkVersion).count()}")
        print(f"  优秀作业数量: {db.session.query(ExcellentHomework).count()}")
        print(f"  文件数量: {db.session.query(File).count()}")

if __name__ == '__main__':
    print("=" * 60)
    print("优秀作业测试数据创建工具")
    print("=" * 60)
    print()
    print("[INFO] 此操作将创建：")
    print("  - 1个测试课程（如果不存在）")
    print("  - 1个作业类型（如果不存在）")
    print("  - 1个作业（使用test_all.docx）")
    print("  - 5条优秀作业记录（都关联到同一个作业版本）")
    print()
    print("[INFO] 这将模拟：")
    print("  - 学生提交作业")
    print("  - 教师批改为'优秀'")
    print("  - 教师发布为优秀作业（重复5次，生成5条记录）")
    print()
    confirm = input("确认创建吗？(输入 'yes' 确认): ")

    if confirm.lower() == 'yes':
        create_excellent_homeworks()
    else:
        print("操作已取消")
