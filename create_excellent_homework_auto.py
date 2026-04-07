"""
创建1条优秀作业测试数据（包含自动转换PDF和生成图片）
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

def create_excellent_homework():
    """创建1条优秀作业（包含自动转换）"""
    with app.app_context():
        print("=" * 60)
        print("开始创建1条优秀作业测试数据（包含自动转换）")
        print("=" * 60)

        # 初始化转换器
        office_converter = OfficeToPDFConverter()
        img_converter = PDFToImageConverter()

        # 1. 获取学生和教师
        print("\n[1/7] 查找学生和教师...")
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
        print("\n[2/7] 创建/获取课程...")
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
        print("\n[3/7] 创建/获取作业类型...")
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

        # 4. 上传原始文件（test_all.docx）
        print("\n[4/7] 上传原始Office文档...")
        docx_path = 'img/test_all.docx'
        
        if not os.path.exists(docx_path):
            print(f"[ERROR] 文件不存在: {docx_path}")
            return

        # 创建文件记录
        file_record = File(
            filename='test_all.docx',
            original_filename='test_all.docx',
            file_path=docx_path,
            file_size=os.path.getsize(docx_path),
            file_type='document',
            uploader_id=student.id
        )
        db.session.add(file_record)
        db.session.flush()
        print(f"[OK] 原始文件上传成功: ID={file_record.id}, 文件名={file_record.original_filename}")

        # 5. 自动转换为PDF
        print("\n[5/7] 自动转换为PDF...")
        pdf_file_id = None
        pdf_file_path = None

        if office_converter.libreoffice_path and File.is_office_document(docx_path):
            try:
                print(f"[PDF Conversion] 开始转换: {docx_path}")
                pdf_output_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs')
                os.makedirs(pdf_output_dir, exist_ok=True)
                
                pdf_path = office_converter.convert_to_pdf(docx_path, pdf_output_dir)
                
                if pdf_path and os.path.exists(pdf_path):
                    print(f"[PDF Conversion] PDF转换成功: {pdf_path}")
                    
                    # 创建PDF文件记录
                    pdf_file_record = File(
                        filename=os.path.basename(pdf_path),
                        original_filename='test_all.pdf',
                        file_path=pdf_path,
                        file_size=os.path.getsize(pdf_path),
                        file_type='document',
                        mime_type='application/pdf',
                        uploader_id=student.id
                    )
                    db.session.add(pdf_file_record)
                    db.session.flush()
                    
                    # 关联PDF到原文件
                    file_record.pdf_file_id = pdf_file_record.id
                    db.session.commit()
                    
                    pdf_file_id = pdf_file_record.id
                    pdf_file_path = pdf_path
                    print(f"[PDF Conversion] PDF文件记录创建成功: ID={pdf_file_record.id}")
                    
        # 6. 自动生成预览图片
        print("\n[6/7] 自动生成预览图片...")
        image_file_id = None
                    
        if img_converter.imagick_path:
            try:
                            print(f"[Image Generation] 开始生成预览图...")
                            image_output_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'images')
                            os.makedirs(image_output_dir, exist_ok=True)
                            
                            # 生成缩略图
                            image_path = img_converter.pdf_to_thumbnail(
                                pdf_path, 
                                image_output_dir, 
                                width=400, 
                                height=300
                            )
                            
                            if image_path and os.path.exists(image_path):
                                print(f"[Image Generation] 预览图生成成功: {image_path}")
                                
                                # 创建图片文件记录
                                image_file_record = File(
                                    filename=os.path.basename(image_path),
                                    original_filename='test_all_preview.jpg',
                                    file_path=image_path,
                                    file_size=os.path.getsize(image_path),
                                    file_type='image',
                                    mime_type='image/jpeg',
                                    uploader_id=student.id
                                )
                                db.session.add(image_file_record)
                                db.session.flush()
                                
                                # 关联图片到原文件
                                file_record.image_file_id = image_file_record.id
                                db.session.commit()
                                
                                image_file_id = image_file_record.id
                                print(f"[Image Generation] 预览图文件记录创建成功: ID={image_file_record.id}")
                            else:
                                print(f"[Image Generation] 预览图生成失败")
                        except Exception as e:
                            print(f"[Image Generation] 错误: {str(e)}")
                    else:
                        print(f"[Image Generation] ImageMagick未安装，跳过图片生成")
                else:
                    print(f"[PDF Conversion] PDF转换失败")
            except Exception as e:
                print(f"[PDF Conversion] 错误: {str(e)}")
        else:
            print(f"[PDF Conversion] LibreOffice未安装或不是Office文档，跳过PDF转换")

        # 7. 创建作业和作业版本
        print("\n[7/7] 创建作业和作业版本...")
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

        # 创建作业版本（关联PDF文件）
        homework_version = HomeworkVersion.query.filter_by(
            homework_id=homework.id,
            version_number=1
        ).first()

        if not homework_version:
            homework_version = HomeworkVersion(
                homework_id=homework.id,
                version_number=1,
                file_file_id=file_record.id,  # 使用原始文件
                pdf_file_id=pdf_file_id,  # 关联PDF文件
                img_file_id=image_file_id,  # 关联预览图片
                evaluation='优秀',
                score='100',
                is_redo=False
            )
            db.session.add(homework_version)
            db.session.flush()
            print(f"[OK] 创建作业版本: ID={homework_version.id}")
        else:
            print(f"[OK] 找到作业版本: ID={homework_version.id}")

        # 创建优秀作业
        print("\n[8/8] 创建优秀作业...")
        excellent = ExcellentHomework(
            homework_version_id=homework_version.id,
            teacher_id=teacher.id,
            likes_count=0
        )
        db.session.add(excellent)
        db.session.flush()
        print(f"[OK] 创建优秀作业: ID={excellent.id}")

        db.session.commit()

        print("\n" + "=" * 60)
        print("[OK] 优秀作业测试数据创建完成！")
        print("=" * 60)

        # 显示统计
        print("\n当前数据统计：")
        print(f"  优秀作业数量: {db.session.query(ExcellentHomework).count()}")
        from app.models.homework import HomeworkVersion
        print(f"  作业版本数量: {db.session.query(HomeworkVersion).count()}")
        print(f"  文件数量: {db.session.query(File).count()}")
        
        # 显示文件关联
        if pdf_file_id:
            print(f"\n  原始文件ID: {file_record.id}")
            print(f"  PDF文件ID: {pdf_file_id}")
        if image_file_id:
            print(f"  预览图ID: {image_file_id}")

if __name__ == '__main__':
    print("=" * 60)
    print("优秀作业测试数据创建工具（包含自动转换）")
    print("=" * 60)
    print()
    print("[INFO] 此操作将创建：")
    print("  - 1条优秀作业记录")
    print("  - 自动将 test_all.docx 转换为 PDF")
    print("  - 自动从 PDF 生成预览图片")
    print("  - 关联所有文件到作业版本")
    print()
    print("[INFO] 自动转换需要：")
    print("  - LibreOffice 安装在系统中")
    print("  - ImageMagick 安装在系统中")
    print()
    print("[INFO] 如果转换失败，不影响作业创建")
    print()
    confirm = input("确认创建吗？(输入 'yes' 确认): ")

    if confirm.lower() == 'yes':
        create_excellent_homework()
    else:
        print("操作已取消")
