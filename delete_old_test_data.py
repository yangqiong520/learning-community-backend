import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.db import db, DATABASE_URI
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def delete_old_test_data():
    """
    删除没有转换PDF的旧测试数据
    """
    with app.app_context():
        from app.models.regulation import Regulation
        from app.models.training_program import TrainingProgram
        from app.models.teaching_plan import TeachingPlan
        from app.models.textbook import Textbook
        from app.models.courseware import Courseware
        from app.models.file import File
        from app.models.like import Like
        
        # 删除相关制度 (ID: 1)
        regulation = Regulation.query.get(1)
        if regulation:
            print(f"删除相关制度 (ID: {regulation.id}): {regulation.title}")
            # 删除相关的点赞记录
            Like.query.filter_by(regulation_id=regulation.id).delete()
            db.session.delete(regulation)
        
        # 删除培养方案 (ID: 1)
        training_program = TrainingProgram.query.get(1)
        if training_program:
            print(f"删除培养方案 (ID: {training_program.id}): {training_program.title}")
            # 删除相关的点赞记录
            Like.query.filter_by(training_program_id=training_program.id).delete()
            db.session.delete(training_program)
        
        # 删除教学计划 (ID: 1)
        teaching_plan = TeachingPlan.query.get(1)
        if teaching_plan:
            print(f"删除教学计划 (ID: {teaching_plan.id}): {teaching_plan.title}")
            # 删除相关的点赞记录
            Like.query.filter_by(teaching_plan_id=teaching_plan.id).delete()
            db.session.delete(teaching_plan)
        
        # 删除教材库 (ID: 1)
        textbook = Textbook.query.get(1)
        if textbook:
            print(f"删除教材库 (ID: {textbook.id}): {textbook.title}")
            # 删除相关的点赞记录
            Like.query.filter_by(textbook_id=textbook.id).delete()
            db.session.delete(textbook)
        
        # 删除教案课件库 (ID: 1)
        courseware = Courseware.query.get(1)
        if courseware:
            print(f"删除教案课件库 (ID: {courseware.id}): {courseware.title}")
            # 删除相关的点赞记录
            Like.query.filter_by(courseware_id=courseware.id).delete()
            db.session.delete(courseware)
        
        # 删除旧的文件记录 (ID: 9, 10)
        for file_id in [9, 10]:
            file = File.query.get(file_id)
            if file:
                print(f"删除文件记录 (ID: {file.id}): {file.original_filename}")
                # 删除关联的PDF文件
                if file.pdf_file_id:
                    pdf_file = File.query.get(file.pdf_file_id)
                    if pdf_file:
                        # 删除PDF文件
                        if os.path.exists(pdf_file.file_path):
                            os.remove(pdf_file.file_path)
                            print(f"  删除PDF文件: {pdf_file.file_path}")
                        db.session.delete(pdf_file)
                        print(f"  删除PDF文件记录 (ID: {pdf_file.id})")
                
                # 删除原文件
                if os.path.exists(file.file_path):
                    os.remove(file.file_path)
                    print(f"  删除文件: {file.file_path}")
                db.session.delete(file)
        
        db.session.commit()
        print("\n旧测试数据删除完成！")

if __name__ == '__main__':
    delete_old_test_data()
