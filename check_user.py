import os
import sys

# 确保从项目根目录运行
project_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_root)

sys.path.append(project_root)

from libs.db import db, DATABASE_URI
from flask import Flask
from app.models.user import User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def check_user():
    """
    检查用户信息
    """
    with app.app_context():
        # 按手机号查找
        user = User.query.filter_by(phone='15680692521').first()
        
        if not user:
            print("用户不存在！手机号: 15680692521")
            return
        
        print(f"用户信息：")
        print(f"  ID: {user.id}")
        print(f"  用户名: {user.username}")
        print(f"  手机号: {user.phone}")
        print(f"  角色: {user.role}")
        print(f"  用户图片: {user.user_img}")
        print(f"  创建时间: {user.created_at}")
        print(f"  密码哈希: {user.password}")

if __name__ == '__main__':
    check_user()
