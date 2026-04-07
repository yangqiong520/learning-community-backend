import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.db import db, DATABASE_URI
from flask import Flask
from app.models.year import Year
from app.models.user import User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def add_test_years():
    """
    添加测试年份
    """
    with app.app_context():
        # 获取或创建教师用户
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
        
        uploader_id = teacher.id
        
        # 创建几个测试年份
        test_years = [
            {'year': 2025, 'name': '2025学年度'},
            {'year': 2024, 'name': '2024学年度'},
            {'year': 2023, 'name': '2023学年度'},
        ]
        
        for year_data in test_years:
            # 检查年份是否已存在
            existing = Year.query.filter_by(year=year_data['year']).first()
            if existing:
                print(f"年份 {year_data['year']} 已存在，跳过")
                continue
            
            year = Year(
                year=year_data['year'],
                name=year_data['name'],
                teacher_id=uploader_id
            )
            db.session.add(year)
            db.session.commit()
            print(f"年份创建成功: {year.name} (ID: {year.id})")
        
        print("\n所有测试年份创建完成！")

if __name__ == '__main__':
    add_test_years()
