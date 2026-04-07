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
from app.models.teaching_plan import TeachingPlan
from app.utils.office_converter import OfficeToPDFConverter
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
    image_path = 'E:\\nodejs-project\\learning-community-backend\\img\\test.png'
    doc_path = 'E:\\nodejs-project\\learning-community-backend\\img\\test_all.docx'

    if not os.path.exists(image_path):
        print(f"[ERROR] Image file not found: {image_path}")
        exit(1)

    if not os.path.exists(doc_path):
        print(f"[ERROR] Document file not found: {doc_path}")
        exit(1)

    user = User.query.first()
    if not user:
        print("[ERROR] No user found, please create user first")
        exit(1)

    print(f"[OK] Using user: {user.username} (ID: {user.id})")

    image_file_record = File(
        filename='test.png',
        original_filename='test.png',
        file_type=File.FILE_TYPE_IMAGE,
        file_size=os.path.getsize(image_path),
        file_path=image_path,
        mime_type='image/png',
        uploader_id=user.id
    )

    db.session.add(image_file_record)
    db.session.commit()

    # 刷新以获取生成的ID
    db.session.refresh(image_file_record)

    doc_file_record = File(
        filename='test_all.docx',
        original_filename='test_all.docx',
        file_type=File.FILE_TYPE_DOCUMENT,
        file_size=os.path.getsize(doc_path),
        file_path=doc_path,
        mime_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        uploader_id=user.id
    )

    db.session.add(doc_file_record)
    db.session.commit()

    # 刷新以获取生成的ID
    db.session.refresh(doc_file_record)

    print(f"[OK] Image file created: {image_file_record.id}")
    print(f"[OK] Document file created: {doc_file_record.id}")

    # 检测是否为Office文档，自动转换为PDF
    converter = OfficeToPDFConverter()
    if converter.is_office_document(doc_path) and converter.libreoffice_path:
        print(f"[Office Conversion] Starting conversion for: test_all.docx")
        try:
            pdf_output_dir = os.path.join('storage', 'pdfs')
            pdf_path = converter.convert_to_pdf(doc_path, pdf_output_dir)

            if pdf_path and os.path.exists(pdf_path):
                print(f"[Office Conversion] Conversion successful: {pdf_path}")
                
                # 创建PDF文件记录
                pdf_filename = os.path.basename(pdf_path)
                pdf_file_record = File(
                    filename=pdf_filename,
                    original_filename='test_all.pdf',
                    file_type=File.FILE_TYPE_DOCUMENT,
                    file_size=os.path.getsize(pdf_path),
                    file_path=pdf_path,
                    mime_type='application/pdf',
                    uploader_id=user.id
                )

                db.session.add(pdf_file_record)
                db.session.commit()

                # 关联PDF到原文件
                doc_file_record.pdf_file_id = pdf_file_record.id
                db.session.commit()

                print(f"[Office Conversion] PDF linked: doc_id={doc_file_record.id}, pdf_file_id={pdf_file_record.id}")
            else:
                print(f"[Office Conversion] Conversion failed: test_all.docx")
        except Exception as e:
            print(f"[Office Conversion] Error during conversion: {str(e)}")
            # 转换失败不影响数据创建
    else:
        print(f"[Office Conversion] Skipped - LibreOffice not installed or not an Office document")

    teaching_plan = TeachingPlan(
        title='Test Teaching Plan',
        content='This is a test teaching plan content',
        file_file_id=doc_file_record.id,
        image_file_id=image_file_record.id,
        uploader_id=user.id
    )

    db.session.add(teaching_plan)
    db.session.commit()

    print(f"[OK] Teaching plan created: {teaching_plan.id}")
    print("[OK] Completed!")
