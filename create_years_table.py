import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.db import db, DATABASE_URI
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def create_years_table():
    """
    创建years表
    """
    with app.app_context():
        try:
            # 使用原生SQL执行CREATE TABLE
            with db.engine.connect() as conn:
                # 检查表是否已存在
                result = conn.execute("SHOW TABLES LIKE 'years'")
                if result.fetchone():
                    print("years表已存在，无需创建")
                    return
                
                # 创建表
                conn.execute("""
                    CREATE TABLE years (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        year INT NOT NULL,
                        name VARCHAR(50) NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE NOT NULL,
                        teacher_id INT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        UNIQUE KEY unique_year (year),
                        FOREIGN KEY (teacher_id) REFERENCES users(id),
                        INDEX idx_teacher_id (teacher_id),
                        INDEX idx_year (year)
                    )
                """)
                conn.commit()
                print("成功创建years表")
        except Exception as e:
            print(f"创建表失败: {str(e)}")

if __name__ == '__main__':
    create_years_table()
