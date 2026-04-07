"""
清空数据库中的课程和作业类型数据（完整版本）
"""

from flask import Flask
from libs.db import db
from app.models.course import Course
from app.models.homework import HomeworkType, Homework, HomeworkVersion
from app.models.homework import ExcellentHomework, ProblemHomework
import sqlalchemy as sa

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/learning_community?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def clear_data():
    """清空课程和作业类型数据（按照外键依赖顺序）"""
    with app.app_context():
        print("=" * 60)
        print("开始清空课程和作业类型数据")
        print("=" * 60)

        # 1. 清空优秀作业
        print("\n[1/6] 清空优秀作业表...")
        try:
            count = db.session.query(ExcellentHomework).count()
            db.session.query(ExcellentHomework).delete()
            db.session.commit()
            print(f"[OK] 已删除 {count} 个优秀作业记录")
        except Exception as e:
            print(f"[ERROR] 清空优秀作业表失败: {e}")
            db.session.rollback()

        # 2. 清空问题作业
        print("\n[2/6] 清空问题作业表...")
        try:
            count = db.session.query(ProblemHomework).count()
            db.session.query(ProblemHomework).delete()
            db.session.commit()
            print(f"[OK] 已删除 {count} 个问题作业记录")
        except Exception as e:
            print(f"[ERROR] 清空问题作业表失败: {e}")
            db.session.rollback()

        # 3. 清空作业版本
        print("\n[3/6] 清空作业版本表...")
        try:
            count = db.session.query(HomeworkVersion).count()
            db.session.query(HomeworkVersion).delete()
            db.session.commit()
            print(f"[OK] 已删除 {count} 个作业版本记录")
        except Exception as e:
            print(f"[ERROR] 清空作业版本表失败: {e}")
            db.session.rollback()

        # 4. 清空作业
        print("\n[4/6] 清空作业表...")
        try:
            count = db.session.query(Homework).count()
            db.session.query(Homework).delete()
            db.session.commit()
            print(f"[OK] 已删除 {count} 个作业记录")
        except Exception as e:
            print(f"[ERROR] 清空作业表失败: {e}")
            db.session.rollback()

        # 5. 清空作业类型
        print("\n[5/6] 清空作业类型表...")
        try:
            count = db.session.query(HomeworkType).count()
            db.session.query(HomeworkType).delete()
            db.session.commit()
            print(f"[OK] 已删除 {count} 个作业类型记录")
        except Exception as e:
            print(f"[ERROR] 清空作业类型表失败: {e}")
            db.session.rollback()

        # 6. 清空课程
        print("\n[6/6] 清空课程表...")
        try:
            count = db.session.query(Course).count()
            db.session.query(Course).delete()
            db.session.commit()
            print(f"[OK] 已删除 {count} 个课程记录")
        except Exception as e:
            print(f"[ERROR] 清空课程表失败: {e}")
            db.session.rollback()

        # 重置自增ID
        print("\n[7/7] 重置自增ID...")
        try:
            db.session.execute(sa.text("ALTER TABLE excellent_homeworks AUTO_INCREMENT = 1"))
            db.session.execute(sa.text("ALTER TABLE problem_homeworks AUTO_INCREMENT = 1"))
            db.session.execute(sa.text("ALTER TABLE homework_versions AUTO_INCREMENT = 1"))
            db.session.execute(sa.text("ALTER TABLE homeworks AUTO_INCREMENT = 1"))
            db.session.execute(sa.text("ALTER TABLE homework_types AUTO_INCREMENT = 1"))
            db.session.execute(sa.text("ALTER TABLE courses AUTO_INCREMENT = 1"))
            db.session.commit()
            print("[OK] 已重置所有表的自增ID")
        except Exception as e:
            print(f"[ERROR] 重置自增ID失败: {e}")
            db.session.rollback()

        print("\n" + "=" * 60)
        print("[OK] 课程和作业类型数据清空完成！")
        print("=" * 60)

        # 显示当前数据统计
        print("\n当前数据统计：")
        print(f"  课程数量: {db.session.query(Course).count()}")
        print(f"  作业类型数量: {db.session.query(HomeworkType).count()}")
        print(f"  作业数量: {db.session.query(Homework).count()}")
        print(f"  作业版本数量: {db.session.query(HomeworkVersion).count()}")
        print(f"  优秀作业数量: {db.session.query(ExcellentHomework).count()}")
        print(f"  问题作业数量: {db.session.query(ProblemHomework).count()}")

if __name__ == '__main__':
    print("=" * 60)
    print("课程和作业类型数据清空工具")
    print("=" * 60)
    print()
    print("[WARNING] 此操作将清空以下数据：")
    print("  - 所有课程")
    print("  - 所有作业类型")
    print("  - 所有作业")
    print("  - 所有作业版本")
    print("  - 所有优秀作业")
    print("  - 所有问题作业")
    print()
    confirm = input("确认清空吗？(输入 'yes' 确认): ")

    if confirm.lower() == 'yes':
        clear_data()
    else:
        print("操作已取消")
