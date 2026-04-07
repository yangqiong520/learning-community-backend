import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import flask
from flask import Flask
import yaml
from libs.db import db, DATABASE_URI
from app.models.file import File
from app.models.user import User

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

    # 获取测试的Office文档
    office_file = File.query.filter_by(id=100).first()

    if not office_file:
        print("[ERROR] Office file not found (ID: 100)")
        exit(1)

    print(f"Office file: {office_file.original_filename}")

    # 检查是否已有PDF关联
    if office_file.pdf_file_id:
        print(f"PDF already linked: {office_file.pdf_file_id}")
        pdf_file = File.query.get(office_file.pdf_file_id)
        if pdf_file:
            print(f"PDF file: {pdf_file.original_filename}")
        exit(0)

    # 获取第一个用户
    user = User.query.first()
    if not user:
        print("[ERROR] No user found")
        exit(1)

    print(f"Using user: {user.username} (ID: {user.id})")

    # 创建PDF文件记录
    pdf_path = os.path.join('storage', 'pdfs', 'test_all.pdf')

    if not os.path.exists(pdf_path):
        print(f"[ERROR] PDF file not found: {pdf_path}")
        exit(1)

    pdf_file = File(
        filename='test_all.pdf',
        original_filename='test_all.pdf',
        file_type=File.FILE_TYPE_DOCUMENT,
        file_size=os.path.getsize(pdf_path),
        file_path=pdf_path,
        mime_type='application/pdf',
        uploader_id=user.id
    )

    db.session.add(pdf_file)
    db.session.commit()

    print(f"PDF file created: {pdf_file.id}")

    # 关联PDF到Office文档
    office_file.pdf_file_id = pdf_file.id
    db.session.commit()

    print(f"PDF linked to office file: {office_file.pdf_file_id}")
    print()

    print("=" * 50)
    print("Database update completed!")
    print("=" * 50)
    print()
    print("Now you can test the API:")
    print(f"1. Get preview URL: GET http://127.0.0.1:5000/api/v2/files/100/preview")
    print(f"2. Convert office: POST http://127.0.0.1:5000/api/v2/files/100/convert-to-pdf")
    print(f"3. Access PDF: http://127.0.0.1:5000/api/v2/files/serve/{pdf_file.id}")
