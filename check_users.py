from flask import Flask
from libs.db import db
from app.models.user import User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learning_community.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    teachers = User.query.filter(User.role == 3).all()
    print('教师账号列表:')
    for u in teachers:
        print(f'  ID: {u.id}, 用户名: {u.username}, 手机号: {u.phone}')
    print()
    print('所有用户列表:')
    users = User.query.all()
    for u in users:
        role_name = '管理员' if u.role == 1 else '教师' if u.role == 3 else '学生' if u.role == 4 else '未知'
        print(f'  ID: {u.id}, 用户名: {u.username}, 手机号: {u.phone}, 角色: {role_name}')
