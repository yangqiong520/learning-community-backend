import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import flask
from flask import Flask, request
from flask_cors import CORS
import yaml
from libs.db import db, DATABASE_URI
from app.models.file import File
from app.utils.office_converter import OfficeToPDFConverter

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    converter = OfficeToPDFConverter()

    print("=" * 50)
    print("Office文档转PDF转换测试")
    print("=" * 50)

    # 检查LibreOffice是否安装
    if converter.libreoffice_path:
        print(f"[OK] LibreOffice found: {converter.libreoffice_path}")
    else:
        print("[ERROR] LibreOffice not found, please install LibreOffice")
        print("Download: https://www.libreoffice.org/download/")
        exit(1)

    print()

    # 查找测试的Office文档
    test_file = File.query.filter_by(id=100).first()

    if not test_file:
        print("[ERROR] Test file not found (ID: 100)")
        print("Please ensure there is test data in the database")
        exit(1)

    print(f"Test file: {test_file.original_filename}")
    print(f"File path: {test_file.file_path}")
    print(f"File type: {test_file.file_type}")
    print()

    # 检查文件是否存在
    if not os.path.exists(test_file.file_path):
        print(f"[ERROR] File not found: {test_file.file_path}")
        exit(1)

    # 检查是否为Office文档
    if not converter.is_office_document(test_file.file_path):
        print(f"[ERROR] This is not an Office document")
        exit(1)

    print("[OK] File validation passed")
    print()

    # 测试转换功能
    print("Starting conversion...")
    print("-" * 50)

    output_dir = os.path.join('storage', 'pdfs')

    try:
        pdf_path = converter.convert_to_pdf(test_file.file_path, output_dir)

        if pdf_path and os.path.exists(pdf_path):
            print(f"[OK] Conversion successful!")
            print(f"PDF path: {pdf_path}")
            print(f"PDF size: {os.path.getsize(pdf_path)} bytes")

            # 显示转换后的PDF文件信息
            pdf_filename = os.path.basename(pdf_path)
            print(f"PDF filename: {pdf_filename}")

            print()
            print("You can access the PDF via:")
            print(f"http://127.0.0.1:5000/api/v2/files/serve/{test_file.id}/preview")
        else:
            print("[ERROR] Conversion failed")

    except Exception as e:
        print(f"[ERROR] Error during conversion: {str(e)}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 50)
    print("Test completed")
    print("=" * 50)
