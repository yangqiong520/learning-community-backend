"""
验证年份表的数据库结构
"""

from flask import Flask
from libs.db import db
import sqlalchemy as sa

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/learning_community?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def check_constraints():
    """检查数据库约束"""
    with app.app_context():
        print("=" * 60)
        print("检查 years 表的索引和约束")
        print("=" * 60)

        # 查询所有索引
        result = db.session.execute(sa.text(
            "SHOW INDEX FROM years"
        ))

        print("\n当前索引列表：")
        print("-" * 60)
        for row in result:
            print(f"  索引名: {row[2]}, 列: {row[4]}, 唯一: {row[1]}")

        print("\n" + "=" * 60)

if __name__ == '__main__':
    check_constraints()
