import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.db import db, DATABASE_URI
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def add_image_file_id_column():
    """
    为files表添加image_file_id字段
    """
    with app.app_context():
        try:
            # 使用db.session.execute
            # 检查字段是否已存在
            result = db.session.execute(db.text("SHOW COLUMNS FROM files LIKE 'image_file_id'"))
            if result.fetchone():
                print("image_file_id字段已存在，无需添加")
                return
            
            # 先添加字段（不添加外键约束）
            db.session.execute(db.text("ALTER TABLE files ADD COLUMN image_file_id INT NULL"))
            db.session.commit()
            print("成功添加image_file_id字段到files表")
            
            # 添加外键约束
            db.session.execute(db.text("ALTER TABLE files ADD CONSTRAINT fk_files_image_file_id FOREIGN KEY (image_file_id) REFERENCES files(id)"))
            db.session.commit()
            print("成功添加外键约束")
            
        except Exception as e:
            print(f"添加字段失败: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_image_file_id_column()
