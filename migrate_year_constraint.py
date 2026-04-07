"""
修复年份表的唯一约束
删除旧的单一唯一约束，添加复合唯一约束 (year, teacher_id)
"""

from flask import Flask
from libs.db import db
import sqlalchemy as sa

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/learning_community?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def migrate():
    """迁移数据库"""
    with app.app_context():
        # 1. 删除旧的唯一约束
        print("正在删除旧的唯一约束...")
        try:
            db.session.execute(sa.text("ALTER TABLE years DROP INDEX year"))
            print("[OK] 删除旧约束成功")
        except Exception as e:
            print(f"  旧约束可能不存在: {e}")

        # 2. 添加新的复合唯一约束
        print("\n正在添加新的复合唯一约束 (year, teacher_id)...")
        try:
            db.session.execute(sa.text(
                "ALTER TABLE years ADD UNIQUE INDEX uq_year_teacher (year, teacher_id)"
            ))
            print("[OK] 添加新约束成功")
        except Exception as e:
            print(f"  添加约束失败: {e}")

        # 3. 提交
        db.session.commit()
        print("\n[OK] 数据库迁移完成！")

if __name__ == '__main__':
    print("=" * 60)
    print("年份表唯一约束迁移")
    print("=" * 60)
    migrate()
    print("=" * 60)
