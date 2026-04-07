"""
清空刚才创建的5条优秀作业数据
"""

from flask import Flask
from libs.db import db
from app.models.homework import ExcellentHomework
import sqlalchemy as sa

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/learning_community?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def clear_excellent_homeworks():
    """清空优秀作业数据"""
    with app.app_context():
        print("=" * 60)
        print("开始清空优秀作业数据")
        print("=" * 60)

        # 查看当前优秀作业数量
        count_before = db.session.query(ExcellentHomework).count()
        print(f"\n当前优秀作业数量: {count_before}")

        # 删除所有优秀作业
        print("\n删除优秀作业...")
        try:
            deleted_count = db.session.query(ExcellentHomework).delete()
            db.session.commit()
            print(f"[OK] 已删除 {deleted_count} 条优秀作业记录")
        except Exception as e:
            print(f"[ERROR] 删除优秀作业失败: {e}")
            db.session.rollback()
            return

        # 查看删除后的数量
        count_after = db.session.query(ExcellentHomework).count()
        print(f"\n删除后优秀作业数量: {count_after}")

        print("\n" + "=" * 60)
        print("[OK] 优秀作业数据清空完成！")
        print("=" * 60)

        # 显示统计
        print("\n当前数据统计：")
        from app.models.course import Course
        from app.models.homework import HomeworkType, Homework, HomeworkVersion

        print(f"  课程数量: {db.session.query(Course).count()}")
        print(f"  作业类型数量: {db.session.query(HomeworkType).count()}")
        print(f"  作业数量: {db.session.query(Homework).count()}")
        print(f"  作业版本数量: {db.session.query(HomeworkVersion).count()}")
        print(f"  优秀作业数量: {db.session.query(ExcellentHomework).count()}")

if __name__ == '__main__':
    print("=" * 60)
    print("优秀作业数据清空工具")
    print("=" * 60)
    print()
    print("[INFO] 此操作将清空所有优秀作业数据")
    print()
    confirm = input("确认清空吗？(输入 'yes' 确认): ")

    if confirm.lower() == 'yes':
        clear_excellent_homeworks()
    else:
        print("操作已取消")
