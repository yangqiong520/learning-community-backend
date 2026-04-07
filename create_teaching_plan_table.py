from flask import Flask
from libs.db import db, DATABASE_URI

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

app = create_app()
with app.app_context():
    print("创建教学计划表...")
    
    # 创建教学计划表
    db.create_all()
    
    print("教学计划表创建完成！")
    print("教学计划表结构：TeachingPlan")
