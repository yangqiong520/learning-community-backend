"""
删除并重新创建优秀作业，确保每个优秀作业有独立的作业版本
"""

from flask import Flask
from libs.db import db
from app.models.user import User
from app.models.course import Course
from app.models.homework import HomeworkType, Homework, HomeworkVersion, ExcellentHomework
from app.models.file import File
from app.utils.office_converter import OfficeToPDFConverter
from app.utils.pdf_to_image import PDFToImageConverter
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/learning_community?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'storage'
db.init_app(app)

def recreate_excellent_homeworks():
    """重新创建优秀作业（每个都有独立的作业版本）"""
    with app.app_context():
        print("=" * 60)
        print("重新创建优秀作业（确保每个都有独立的作业版本）")
        print("=" * 60)

        # 删除所有优秀作业
        print("\n[1/10] 删除所有优秀作业...")
        count_before = db.session.query(ExcellentHomework).count()
        db.session.query(ExcellentHomework).delete()
        db.session.commit()
        print(f"[OK] 删除了 {count_before} 条优秀作业")

        # 删除所有作业版本
        print("\n[2/10] 删除所有作业版本...")
        db.session.query(HomeworkVersion).delete()
        db.session.commit()
        print(f"[OK] 删除了所有作业版本")

        # 删除所有作业
        print("\n[3/10] 删除所有作业...")
        db.session.query(Homework).delete()
        db.session.commit()
        print(f"[OK] 删除了所有作业")

        # 初始化转换器
        office_converter = OfficeToPDFConverter()
        img_converter = PDFToImageConverter()

        # 获取学生和教师
        print("\n[5/10] 获取学生和教师...")
        student = User.query.filter(User.role.in_([3, 4])).first()
        teacher = User.query.filter_by(role=3).first()
        print(f"[OK] 学生: {student.username if student else '无'}")
        print(f"[OK] 教师: {teacher.username if teacher else '无'}")

        # 获取课程和作业类型
        print("\n[6/10] 获取课程和作业类型...")
        course = Course.query.filter_by(name='数字特效', teacher_id=teacher.id).first()
        homework_type = HomeworkType.query.filter_by(
            course_id=course.id if course else 0,
            name='期末作业'
        ).first()

        if not course or not homework_type:
            print(f"[ERROR] 课程或作业类型不存在")
            return

        print(f"[OK] 课程: {course.name}")
        print(f"[OK] 作业类型: {homework_type.name}")

        # 创建两个优秀作业（test_all.docx 和 test_two.docx）
        print("\n[7/10] 创建第1个优秀作业（test_all.docx）...")
        create_excellent_homework(
            app,
            student,
            course,
            homework_type,
            'img/test_all.docx',
            office_converter,
            img_converter,
            db
        )

        print("\n[8/10] 创建第2个优秀作业（test_two.docx）...")
        create_excellent_homework(
            app,
            student,
            course,
            homework_type,
            'img/test_two.docx',
            office_converter,
            img_converter,
            db
        )

        print("\n" + "=" * 60)
        print("[OK] 优秀作业重新创建完成！")
        print("=" * 60)

        # 显示统计
        print("\n当前数据统计：")
        print(f"  优秀作业数量: {db.session.query(ExcellentHomework).count()}")
        print(f"  作业数量: {db.session.query(Homework).count()}")
        print(f"  作业版本数量: {db.session.query(HomeworkVersion).count()}")

def create_excellent_homework(app, student, course, homework_type, docx_path, office_converter, img_converter, db):
    """创建单个优秀作业"""
    if not os.path.exists(docx_path):
        print(f"[ERROR] 文件不存在: {docx_path}")
        return

    filename = os.path.basename(docx_path)

    # 上传原始文件
    file_record = File(
        filename=filename,
        original_filename=filename,
        file_path=docx_path,
        file_size=os.path.getsize(docx_path),
        file_type='document',
        uploader_id=student.id
    )
    db.session.add(file_record)
    db.session.flush()
    print(f"[OK] 原始文件上传成功: ID={file_record.id}")

    # 转换为PDF
    pdf_file_id = None
    pdf_file_path = None

    if office_converter.libreoffice_path and File.is_office_document(docx_path):
        try:
            pdf_output_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs')
            os.makedirs(pdf_output_dir, exist_ok=True)
            
            pdf_path = office_converter.convert_to_pdf(docx_path, pdf_output_dir)
            
            if pdf_path and os.path.exists(pdf_path):
                print(f"[OK] PDF转换成功: {pdf_path}")
                
                pdf_file_record = File(
                    filename=os.path.basename(pdf_path),
                    original_filename=os.path.splitext(filename)[0] + '.pdf',
                    file_path=pdf_path,
                    file_size=os.path.getsize(pdf_path),
                    file_type='document',
                    mime_type='application/pdf',
                    uploader_id=student.id
                )
                db.session.add(pdf_file_record)
                db.session.flush()
                
                file_record.pdf_file_id = pdf_file_record.id
                db.session.commit()
                
                pdf_file_id = pdf_file_record.id
                pdf_file_path = pdf_path
                print(f"[OK] PDF文件记录创建成功: ID={pdf_file_record.id}")
        except Exception as e:
            print(f"[ERROR] PDF转换失败: {str(e)}")

    # 生成预览图片
    image_file_id = None
    
    if pdf_file_path and img_converter.imagick_path:
        try:
            image_output_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'images')
            os.makedirs(image_output_dir, exist_ok=True)
            
            image_path = img_converter.pdf_to_thumbnail(
                pdf_file_path,
                image_output_dir,
                width=400,
                height=300
            )
            
            if image_path and os.path.exists(image_path):
                print(f"[OK] 预览图生成成功: {image_path}")
                
                image_file_record = File(
                    filename=os.path.basename(image_path),
                    original_filename=os.path.splitext(filename)[0] + '_preview.jpg',
                    file_path=image_path,
                    file_size=os.path.getsize(image_path),
                    file_type='image',
                    mime_type='image/jpeg',
                    uploader_id=student.id
                )
                db.session.add(image_file_record)
                db.session.flush()
                
                file_record.image_file_id = image_file_record.id
                db.session.commit()
                
                image_file_id = image_file_record.id
                print(f"[OK] 预览图文件记录创建成功: ID={image_file_record.id}")
        except Exception as e:
            print(f"[ERROR] 预览图生成失败: {str(e)}")

    # 创建作业
    homework = Homework(
        student_id=student.id,
        course_id=course.id,
        homework_type_id=homework_type.id,
        status='submitted'
    )
    db.session.add(homework)
    db.session.flush()
    print(f"[OK] 作业创建成功: ID={homework.id}")

    # 创建作业版本（每个优秀作业独立的版本）
    homework_version = HomeworkVersion(
        homework_id=homework.id,
        version_number=1,
        file_file_id=file_record.id,
        pdf_file_id=pdf_file_id,
        img_file_id=image_file_id,
        evaluation='优秀',
        score='100',
        is_redo=False
    )
    db.session.add(homework_version)
    db.session.flush()
    print(f"[OK] 作业版本创建成功: ID={homework_version.id}")

    # 创建优秀作业
    excellent = ExcellentHomework(
        homework_version_id=homework_version.id,
        teacher_id=course.teacher_id,
        likes_count=0
    )
    db.session.add(excellent)
    db.session.flush()
    print(f"[OK] 优秀作业创建成功: ID={excellent.id}")

    db.session.commit()

if __name__ == '__main__':
    print("=" * 60)
    print("优秀作业重新创建工具")
    print("=" * 60)
    print()
    print("[INFO] 此操作将：")
    print("  - 删除所有现有优秀作业")
    print("  - 创建2条新的优秀作业")
    print("  - 每条都有独立的作业版本")
    print("  - 每条都包含PDF和预览图")
    print()
    confirm = input("确认重新创建吗？(输入 'yes' 确认): ")

    if confirm.lower() == 'yes':
        recreate_excellent_homeworks()
    else:
        print("操作已取消")
