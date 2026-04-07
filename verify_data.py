import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.db import db, DATABASE_URI
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

from app.models.user import User
from app.models.regulation import Regulation
from app.models.file import File

with app.app_context():
    regs = Regulation.query.all()
    print("Regulations:")
    for r in regs[-3:]:
        print(f"  ID: {r.id}, Title: {r.title}, DocID: {r.document_file_id}, ImgID: {r.image_file_id}")
    
    print("\nFiles (latest):")
    files = File.query.order_by(File.id.desc()).limit(5).all()
    for f in files:
        print(f"  ID: {f.id}, Filename: {f.filename}, Type: {f.file_type}, Original: {f.original_filename}")
    
    # 验证 Regulation 的 to_dict 返回
    print("\nRegulation to_dict (ID=7):")
    reg = Regulation.query.get(7)
    if reg:
        data = reg.to_dict()
        print(f"  ID: {data.get('id')}")
        print(f"  Title: {data.get('title')}")
        print(f"  file_url: {data.get('file_url')}")
        print(f"  imgurl: {data.get('imgurl')}")
        print(f"  pdf_url: {data.get('pdf_url')}")
