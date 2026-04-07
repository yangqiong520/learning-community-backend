"""
检查优秀作业的文件关联情况
"""

from flask import Flask
from libs.db import db
from app.models.homework import ExcellentHomework, HomeworkVersion
from app.models.file import File

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/learning_community?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def check_excellent_homeworks():
    """检查优秀作业的文件关联"""
    with app.app_context():
        print("=" * 60)
        print("检查优秀作业文件关联")
        print("=" * 60)

        excellent_homeworks = ExcellentHomework.query.all()
        print(f"\n找到 {len(excellent_homeworks)} 条优秀作业\n")

        for i, excellent in enumerate(excellent_homeworks, 1):
            print(f"优秀作业 {i}: ID={excellent.id}")
            
            # 获取作业版本
            version = HomeworkVersion.query.get(excellent.homework_version_id)
            if not version:
                print(f"  [ERROR] 作业版本不存在")
                continue
            
            print(f"  作业版本: ID={version.id}")
            print(f"  file_file_id: {version.file_file_id}")
            print(f"  pdf_file_id: {version.pdf_file_id}")
            print(f"  img_file_id: {version.img_file_id}")
            
            # 获取文件
            file = File.query.get(version.file_file_id) if version.file_file_id else None
            pdf_file = File.query.get(version.pdf_file_id) if version.pdf_file_id else None
            img_file = File.query.get(version.img_file_id) if version.img_file_id else None
            
            print(f"  原始文件: {file.original_filename if file else '无'}")
            print(f"  PDF文件: {pdf_file.original_filename if pdf_file else '无'}")
            print(f"  预览图: {img_file.original_filename if img_file else '无'}")
            
            # 测试 to_dict 方法
            data = excellent.to_dict(user_id=1)
            print(f"\n  to_dict 返回：")
            print(f"    content: {data.get('content')}")
            print(f"    file_url: {data.get('file_url')}")
            print(f"    pdf_url: {data.get('pdf_url')}")
            print(f"    img_url: {data.get('img_url')}")
            print(f"    imgurl: {data.get('imgurl')}")
            print()

if __name__ == '__main__':
    check_excellent_homeworks()
