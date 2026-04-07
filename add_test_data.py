import os
import sys
import shutil
import uuid

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.db import db, DATABASE_URI
from flask import Flask
from app.utils.office_converter import OfficeToPDFConverter
from app.utils.pdf_to_image import PDFToImageConverter

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

converter = OfficeToPDFConverter()
img_converter = PDFToImageConverter()
from app.models.file import File
from app.models.user import User
from app.models.regulation import Regulation
from app.models.training_program import TrainingProgram
from app.models.teaching_plan import TeachingPlan
from app.models.textbook import Textbook
from app.models.courseware import Courseware

UPLOAD_FOLDER = 'storage'

def create_file_record(file_path, original_filename, file_type, uploader_id):
    """
    创建文件记录
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return None
    
    file_ext = os.path.splitext(original_filename)[1].lower().lstrip('.')
    new_filename = f"{uuid.uuid4().hex}.{file_ext}"
    
    # 确定保存路径
    if file_type == File.FILE_TYPE_IMAGE:
        upload_path = os.path.join(UPLOAD_FOLDER, 'images')
    elif file_type == File.FILE_TYPE_DOCUMENT:
        upload_path = os.path.join(UPLOAD_FOLDER, 'documents')
    else:
        upload_path = os.path.join(UPLOAD_FOLDER, 'others')
    
    # 确保目录存在
    os.makedirs(upload_path, exist_ok=True)
    
    dest_path = os.path.join(upload_path, new_filename)
    shutil.copy(file_path, dest_path)
    
    file_size = os.path.getsize(dest_path)
    
    # 检测MIME类型
    mime_type = 'application/octet-stream'
    if file_type == File.FILE_TYPE_IMAGE:
        mime_type = 'image/png' if file_ext == 'png' else 'image/jpeg'
    elif file_type == File.FILE_TYPE_DOCUMENT:
        if file_ext == 'pdf':
            mime_type = 'application/pdf'
        elif file_ext in ['doc', 'docx']:
            mime_type = 'application/msword'
        elif file_ext == 'docx':
            mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    
    file_record = File(
        filename=new_filename,
        original_filename=original_filename,
        file_type=file_type,
        file_size=file_size,
        file_path=dest_path,
        mime_type=mime_type,
        uploader_id=uploader_id
    )
    
    db.session.add(file_record)
    db.session.commit()
    
    # 检测是否为Office文档，自动转换为PDF
    if File.is_office_document(dest_path) and converter.libreoffice_path:
        try:
            print(f"[Office Conversion] Starting conversion for: {original_filename}")
            pdf_output_dir = os.path.join(UPLOAD_FOLDER, 'pdfs')
            os.makedirs(pdf_output_dir, exist_ok=True)
            pdf_path = converter.convert_to_pdf(dest_path, pdf_output_dir)
            
            if pdf_path and os.path.exists(pdf_path):
                print(f"[Office Conversion] Conversion successful: {pdf_path}")
                
                # 创建PDF文件记录
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
                
                # 关联PDF到原文件
                file_record.pdf_file_id = pdf_file_record.id
                db.session.commit()
                
                print(f"[Office Conversion] PDF linked: file_id={file_record.id}, pdf_file_id={pdf_file_record.id}")
                
                # 自动从PDF生成预览图片
                if img_converter.imagick_path:
                    try:
                        print(f"[Image Generation] Starting preview image generation for: {pdf_filename}")
                        image_output_dir = os.path.join(UPLOAD_FOLDER, 'images')
                        os.makedirs(image_output_dir, exist_ok=True)
                        
                        # 生成缩略图（更适合预览）
                        image_path = img_converter.pdf_to_thumbnail(pdf_path, image_output_dir, width=400, height=300)
                        
                        if image_path and os.path.exists(image_path):
                            print(f"[Image Generation] Preview image generated: {image_path}")
                            
                            # 创建图片文件记录
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
                            
                            # 关联图片到原文件
                            file_record.image_file_id = image_file_record.id
                            db.session.commit()
                            
                            print(f"[Image Generation] Image linked: file_id={file_record.id}, image_file_id={image_file_record.id}")
                        else:
                            print(f"[Image Generation] Preview image generation failed for: {pdf_filename}")
                    except Exception as e:
                        print(f"[Image Generation] Error during image generation: {str(e)}")
                        # 图片生成失败不影响上传，只记录日志
                else:
                    print(f"[Image Generation] ImageMagick not found, skipping preview image generation")
            else:
                print(f"[Office Conversion] Conversion failed: {original_filename}")
        except Exception as e:
            print(f"[Office Conversion] Error during conversion: {str(e)}")
    
    print(f"文件记录创建成功: {original_filename} -> ID: {file_record.id}")
    return file_record

def add_test_data():
    """
    添加测试数据
    """
    with app.app_context():
        # 获取或创建测试用户
        user = User.query.filter_by(username='admin').first()
        if not user:
            user = User(
                username='admin',
                password='admin123',
                phone='13800138000',
                role=User.ROLE_TEACHER,
                user_img=None
            )
            db.session.add(user)
            db.session.commit()
            print(f"测试用户创建成功: {user.username} (ID: {user.id})")
        
        uploader_id = user.id
        
        # 图片文件路径
        image_path = r'E:\nodejs-project\learning-community-backend\img\test.png'
        # 文档文件路径
        document_path = r'E:\nodejs-project\learning-community-backend\img\test_two.docx'
        
        # 创建文件记录
        image_file = create_file_record(image_path, 'test.png', File.FILE_TYPE_IMAGE, uploader_id)
        document_file = create_file_record(document_path, 'test_two.docx', File.FILE_TYPE_DOCUMENT, uploader_id)
        
        if not image_file or not document_file:
            print("文件记录创建失败，无法继续")
            return
        
        # 添加相关制度
        regulation = Regulation(
            title='测试相关制度',
            content='这是一个测试相关制度的内容',
            document_file_id=document_file.id,
            image_file_id=image_file.id,
            uploader_id=uploader_id
        )
        db.session.add(regulation)
        db.session.commit()
        print(f"相关制度创建成功 (ID: {regulation.id})")
        
        # 添加培养方案
        training_program = TrainingProgram(
            title='测试培养方案',
            content='这是一个测试培养方案的内容',
            document_file_id=document_file.id,
            image_file_id=image_file.id,
            uploader_id=uploader_id
        )
        db.session.add(training_program)
        db.session.commit()
        print(f"培养方案创建成功 (ID: {training_program.id})")
        
        # 添加教学计划
        teaching_plan = TeachingPlan(
            title='测试教学计划',
            content='这是一个测试教学计划的内容',
            file_file_id=document_file.id,
            image_file_id=image_file.id,
            uploader_id=uploader_id
        )
        db.session.add(teaching_plan)
        db.session.commit()
        print(f"教学计划创建成功 (ID: {teaching_plan.id})")
        
        # 添加教材库
        textbook = Textbook(
            title='测试教材',
            content='这是一个测试教材的内容',
            document_file_id=document_file.id,
            image_file_id=image_file.id,
            uploader_id=uploader_id
        )
        db.session.add(textbook)
        db.session.commit()
        print(f"教材库创建成功 (ID: {textbook.id})")
        
        # 添加教案课件库
        courseware = Courseware(
            title='测试教案课件',
            content='这是一个测试教案课件的内容',
            document_file_id=document_file.id,
            image_file_id=image_file.id,
            uploader_id=uploader_id
        )
        db.session.add(courseware)
        db.session.commit()
        print(f"教案课件库创建成功 (ID: {courseware.id})")
        
        print("\n所有测试数据创建完成！")

if __name__ == '__main__':
    add_test_data()
