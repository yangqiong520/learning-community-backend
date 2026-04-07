import os
import shutil
import uuid
from app.models.file import File
from app.models.teaching_plan import TeachingPlan
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
    
    image_path = r'E:\nodejs-project\learning-community-backend\img\test.png'
    doc_path = r'E:\nodejs-project\learning-community-backend\img\teaching.pdf'
    
    if not os.path.exists(image_path):
        print(f"图片文件不存在: {image_path}")
        exit(1)
    
    if not os.path.exists(doc_path):
        print(f"文档文件不存在: {doc_path}")
        exit(1)
    
    print(f"上传图片: {os.path.basename(image_path)}")
    image_file = save_file_to_db(image_path, File.FILE_TYPE_IMAGE, user.id)
    print(f"图片文件ID: {image_file.id}")
    
    print(f"上传文档: {os.path.basename(doc_path)}")
    doc_file = save_file_to_db(doc_path, File.FILE_TYPE_DOCUMENT, user.id)
    print(f"文档文件ID: {doc_file.id}")
    
    content = extract_document_content_simple(doc_file.file_path)
    print(f"提取文档内容长度: {len(content)} 字符")
    
    teaching_plan = TeachingPlan(
        title="测试教学计划",
        content=content,
        file_file_id=doc_file.id,
        image_file_id=image_file.id,
        uploader_id=user.id
    )
    
    db.session.add(teaching_plan)
    db.session.commit()
    
    print(f"教学计划创建成功，ID: {teaching_plan.id}")
