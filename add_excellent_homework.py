import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.db import db, DATABASE_URI
from flask import Flask
from app.models.homework import Homework, HomeworkVersion, HomeworkType, ExcellentHomework
from app.models.user import User
from app.models.course import Course
from app.models.file import File
from app.utils.office_converter import OfficeToPDFConverter
from app.utils.pdf_to_image import PDFToImageConverter
import uuid
import shutil

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

UPLOAD_FOLDER = 'storage'
converter = OfficeToPDFConverter()
img_converter = PDFToImageConverter()

def upload_pdf(file_path, original_filename, uploader_id):
    """
    上传PDF文件
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return None
    
    file_ext = os.path.splitext(original_filename)[1].lower().lstrip('.')
    new_filename = f"{uuid.uuid4().hex}.{file_ext}"
    
    upload_path = os.path.join(UPLOAD_FOLDER, 'pdfs')
    os.makedirs(upload_path, exist_ok=True)
    
    dest_path = os.path.join(upload_path, new_filename)
    shutil.copy(file_path, dest_path)
    
    file_size = os.path.getsize(dest_path)
    
    file_record = File(
        filename=new_filename,
        original_filename=original_filename,
        file_type=File.FILE_TYPE_DOCUMENT,
        file_size=file_size,
        file_path=dest_path,
        mime_type='application/pdf',
        uploader_id=uploader_id
    )
    
    db.session.add(file_record)
    db.session.commit()
    
    print(f"PDF文件上传成功: {original_filename} -> ID: {file_record.id}")
    return file_record

def generate_pdf_preview(file_record, uploader_id):
    """
    为PDF文件生成预览图
    """
    if not img_converter.imagick_path:
        print(f"ImageMagick未安装，跳过预览图生成")
        return None
    
    try:
        print(f"[Image Generation] Starting preview image generation for PDF")
        image_output_dir = os.path.join(UPLOAD_FOLDER, 'images')
        os.makedirs(image_output_dir, exist_ok=True)
        
        image_path = img_converter.pdf_to_thumbnail(file_record.file_path, image_output_dir, width=400, height=300)
        
        if image_path and os.path.exists(image_path):
            print(f"[Image Generation] Preview image generated: {image_path}")
            
            image_filename = os.path.basename(image_path)
            image_file_record = File(
                filename=image_filename,
                original_filename=f"{os.path.splitext(file_record.original_filename)[0]}_preview.jpg",
                file_type=File.FILE_TYPE_IMAGE,
                file_size=os.path.getsize(image_path),
                file_path=image_path,
                mime_type='image/jpeg',
                uploader_id=uploader_id
            )
            
            db.session.add(image_file_record)
            db.session.commit()
            
            file_record.image_file_id = image_file_record.id
            db.session.commit()
            
            print(f"[Image Generation] Image linked: file_id={file_record.id}, image_file_id={image_file_record.id}")
            return image_file_record
        else:
            print(f"[Image Generation] Preview image generation failed")
            return None
    except Exception as e:
        print(f"[Image Generation] Error: {str(e)}")
        return None

def upload_office_document(file_path, original_filename, uploader_id):
    """
    上传Office文档并自动转换PDF和生成预览图
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return None, None, None
    
    file_ext = os.path.splitext(original_filename)[1].lower().lstrip('.')
    new_filename = f"{uuid.uuid4().hex}.{file_ext}"
    
    upload_path = os.path.join(UPLOAD_FOLDER, 'documents')
    os.makedirs(upload_path, exist_ok=True)
    
    dest_path = os.path.join(upload_path, new_filename)
    shutil.copy(file_path, dest_path)
    
    file_size = os.path.getsize(dest_path)
    
    file_record = File(
        filename=new_filename,
        original_filename=original_filename,
        file_type=File.FILE_TYPE_DOCUMENT,
        file_size=file_size,
        file_path=dest_path,
        mime_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        uploader_id=uploader_id
    )
    
    db.session.add(file_record)
    db.session.commit()
    
    pdf_file_record = None
    image_file_record = None
    
    # 转换为PDF
    if File.is_office_document(dest_path) and converter.libreoffice_path:
        try:
            print(f"[Office Conversion] Starting conversion for: {original_filename}")
            pdf_output_dir = os.path.join(UPLOAD_FOLDER, 'pdfs')
            os.makedirs(pdf_output_dir, exist_ok=True)
            pdf_path = converter.convert_to_pdf(dest_path, pdf_output_dir)
            
            if pdf_path and os.path.exists(pdf_path):
                print(f"[Office Conversion] Conversion successful: {pdf_path}")
                
                pdf_filename = os.path.basename(pdf_path)
                pdf_file_record = File(
                    filename=pdf_filename,
                    original_filename=os.path.splitext(original_filename)[0] + '.pdf',
                    file_type=File.FILE_TYPE_DOCUMENT,
                    file_size=os.path.getsize(pdf_path),
                    file_path=pdf_path,
                    mime_type='application/pdf',
                    uploader_id=uploader_id
                )
                
                db.session.add(pdf_file_record)
                db.session.commit()
                
                file_record.pdf_file_id = pdf_file_record.id
                db.session.commit()
                
                print(f"[Office Conversion] PDF linked: file_id={file_record.id}, pdf_file_id={pdf_file_record.id}")
                
                # 生成预览图
                if img_converter.imagick_path:
                    try:
                        print(f"[Image Generation] Starting preview image generation for: {pdf_filename}")
                        image_output_dir = os.path.join(UPLOAD_FOLDER, 'images')
                        os.makedirs(image_output_dir, exist_ok=True)
                        
                        image_path = img_converter.pdf_to_thumbnail(pdf_path, image_output_dir, width=400, height=300)
                        
                        if image_path and os.path.exists(image_path):
                            print(f"[Image Generation] Preview image generated: {image_path}")
                            
                            image_filename = os.path.basename(image_path)
                            image_file_record = File(
                                filename=image_filename,
                                original_filename=f"{os.path.splitext(original_filename)[0]}_preview.jpg",
                                file_type=File.FILE_TYPE_IMAGE,
                                file_size=os.path.getsize(image_path),
                                file_path=image_path,
                                mime_type='image/jpeg',
                                uploader_id=uploader_id
                            )
                            
                            db.session.add(image_file_record)
                            db.session.commit()
                            
                            file_record.image_file_id = image_file_record.id
                            db.session.commit()
                            
                            print(f"[Image Generation] Image linked: file_id={file_record.id}, image_file_id={image_file_record.id}")
                    except Exception as e:
                        print(f"[Image Generation] Error: {str(e)}")
        except Exception as e:
            print(f"[Office Conversion] Error: {str(e)}")
    
    print(f"文件上传成功: {original_filename} -> ID: {file_record.id}")
    return file_record, pdf_file_record, image_file_record

def add_multiple_excellent_homeworks(file_paths):
    """
    批量添加优秀作业
    """
    with app.app_context():
        # 获取或创建测试用户
        teacher = User.query.filter_by(username='admin').first()
        if not teacher:
            teacher = User(
                username='admin',
                password='admin123',
                phone='13800138000',
                role=User.ROLE_TEACHER,
                user_img=None
            )
            db.session.add(teacher)
            db.session.commit()
            print(f"教师用户创建成功: {teacher.username} (ID: {teacher.id})")
        
        # 创建学生用户
        student = User.query.filter_by(username='student1').first()
        if not student:
            student = User(
                username='student1',
                password='student123',
                phone='13800138001',
                role=User.ROLE_STUDENT,
                user_img=None
            )
            db.session.add(student)
            db.session.commit()
            print(f"学生用户创建成功: {student.username} (ID: {student.id})")
        
        # 创建课程
        course = Course.query.filter_by(name='数字特效').first()
        if not course:
            course = Course(
                name='数字特效',
                code='SE2024',
                description='数字特效课程',
                teacher_id=teacher.id
            )
            db.session.add(course)
            db.session.commit()
            print(f"课程创建成功: {course.name} (ID: {course.id})")
        
        # 创建作业类型
        homework_type = HomeworkType.query.filter_by(name='期末作业').first()
        if not homework_type:
            homework_type = HomeworkType(
                name='期末作业',
                content='完成一个完整的数字特效作品',
                course_id=course.id,
                teacher_id=teacher.id
            )
            db.session.add(homework_type)
            db.session.commit()
            print(f"作业类型创建成功: {homework_type.name} (ID: {homework_type.id})")
        
        # 批量上传文件
        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"文件不存在，跳过: {file_path}")
                continue
            
            # 判断文件类型
            original_filename = os.path.basename(file_path)
            file_ext = os.path.splitext(original_filename)[1].lower()
            
            if file_ext == '.pdf':
                # PDF文件直接上传
                file_record = upload_pdf(file_path, original_filename, teacher.id)
                if not file_record:
                    print(f"文件上传失败: {original_filename}")
                    continue
                
                pdf_file_record = None
                image_file_record = generate_pdf_preview(file_record, teacher.id)
            elif file_ext in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
                # Office文档上传并转换
                file_record, pdf_file_record, image_file_record = upload_office_document(file_path, original_filename, teacher.id)
                if not file_record:
                    print(f"文件上传失败: {original_filename}")
                    continue
            else:
                print(f"不支持的文件类型: {file_ext}")
                continue
            
            # 创建作业
            homework = Homework(
                student_id=student.id,
                course_id=course.id,
                homework_type_id=homework_type.id,
                status=Homework.STATUS_EXCELLENT
            )
            db.session.add(homework)
            db.session.commit()
            print(f"作业创建成功 (ID: {homework.id})")
            
            # 创建作业版本
            homework_version = HomeworkVersion(
                homework_id=homework.id,
                version_number=1,
                file_file_id=file_record.id,
                pdf_file_id=pdf_file_record.id if pdf_file_record else None,
                img_file_id=image_file_record.id if image_file_record else None,
                score='A',
                evaluation='优秀的作品，特效处理非常出色',
                is_redo=False
            )
            db.session.add(homework_version)
            db.session.commit()
            print(f"作业版本创建成功 (ID: {homework_version.id})")
            
            # 更新作业的当前版本ID
            homework.current_version_id = homework_version.id
            db.session.commit()
            
            # 创建优秀作业
            excellent_homework = ExcellentHomework(
                homework_version_id=homework_version.id,
                teacher_id=teacher.id,
                likes_count=0
            )
            db.session.add(excellent_homework)
            db.session.commit()
            print(f"优秀作业创建成功 (ID: {excellent_homework.id})")
            print(f"---")
        
        print("\n所有优秀作业创建完成！")

if __name__ == '__main__':
    # 添加两个文件
    add_multiple_excellent_homeworks([
        r'E:\nodejs-project\learning-community-backend\img\teaching.pdf',
        r'E:\nodejs-project\learning-community-backend\img\test_two.docx'
    ])
