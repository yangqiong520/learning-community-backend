import os
import shutil
import uuid
from app.models.file import File
from app.models.training_program import TrainingProgram
from app.models.user import User
from libs.db import db
from app.utils.simple_document_extractor import extract_document_content_simple
import yaml
from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

app_config = config['app']
db_config = config['database']

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?charset={db_config['charset']}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

CORS(app)

db.init_app(app)

UPLOAD_FOLDER = 'storage'

def detect_file_type(filename):
    if not filename or '.' not in filename:
        return File.FILE_TYPE_OTHER

    ext = os.path.splitext(filename)[1].lower().lstrip('.')

    for file_type, extensions in File.FILE_EXTENSIONS.items():
        if ext in extensions:
            return file_type

    return File.FILE_TYPE_OTHER

def save_file_to_db(source_path, file_type, uploader_id):
    filename = os.path.basename(source_path)
    file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
    new_filename = f"{uuid.uuid4().hex}.{file_ext}"

    if file_type == File.FILE_TYPE_IMAGE:
        upload_path = os.path.join(UPLOAD_FOLDER, 'images')
    elif file_type == File.FILE_TYPE_DOCUMENT:
        upload_path = os.path.join(UPLOAD_FOLDER, 'documents')
    else:
        upload_path = os.path.join(UPLOAD_FOLDER, 'others')

    os.makedirs(upload_path, exist_ok=True)
    dest_path = os.path.join(upload_path, new_filename)
    
    shutil.copy2(source_path, dest_path)
    file_size = os.path.getsize(dest_path)

    file_record = File(
        filename=new_filename,
        original_filename=filename,
        file_type=file_type,
        file_size=file_size,
        file_path=dest_path,
        mime_type=None,
        uploader_id=uploader_id
    )

    db.session.add(file_record)
    db.session.commit()
    
    return file_record

with app.app_context():
    user = User.query.first()
    if not user:
        print("未找到用户，请先创建用户")
        exit(1)
    
    img_dir = r'E:\nodejs-project\learning-community-backend\img'
    
    files_data = [
        {
            'title': '数字媒体艺术培训方案',
            'image': os.path.join(img_dir, 'teach_test.png'),
            'document': os.path.join(img_dir, 'teaching.pdf')
        },
        {
            'title': '现代教育技术培训',
            'image': os.path.join(img_dir, 'test.png'),
            'document': os.path.join(img_dir, 'test_three.pdf')
        },
        {
            'title': '创新教学方法研究',
            'image': os.path.join(img_dir, 'traning_test.png'),
            'document': os.path.join(img_dir, 'test_two.docx')
        },
        {
            'title': '教师专业发展计划',
            'image': os.path.join(img_dir, 'teach_test.png'),
            'document': os.path.join(img_dir, 'traning_two.pdf')
        },
        {
            'title': '教育信息化建设方案',
            'image': os.path.join(img_dir, 'test.png'),
            'document': os.path.join(img_dir, 'teaching.pdf')
        }
    ]
    
    for i, data in enumerate(files_data, 1):
        print(f"\n[{i}/5] 处理: {data['title']}")
        
        if not os.path.exists(data['image']):
            print(f"  警告: 图片文件不存在 - {data['image']}")
            continue
        
        if not os.path.exists(data['document']):
            print(f"  警告: 文档文件不存在 - {data['document']}")
            continue
        
        image_file = save_file_to_db(data['image'], File.FILE_TYPE_IMAGE, user.id)
        print(f"  图片文件ID: {image_file.id}")
        
        doc_file = save_file_to_db(data['document'], File.FILE_TYPE_DOCUMENT, user.id)
        print(f"  文档文件ID: {doc_file.id}")
        
        try:
            content = extract_document_content_simple(doc_file.file_path)
            print(f"  文档内容长度: {len(content)} 字符")
        except Exception as e:
            print(f"  文档内容提取失败: {e}")
            content = f"文档内容提取失败: {str(e)}"
        
        training_program = TrainingProgram(
            title=data['title'],
            content=content,
            document_file_id=doc_file.id,
            image_file_id=image_file.id,
            uploader_id=user.id
        )
        
        db.session.add(training_program)
        db.session.commit()
        
        print(f"  [OK] 培养方案创建成功，ID: {training_program.id}")
    
    print("\n=== 完成 ===")
    print(f"成功创建 {len(files_data)} 条培养方案数据")
