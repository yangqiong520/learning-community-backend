from flask import Blueprint, request, jsonify
from libs.db import db
from app.models.course import Course
from app.models.user import User
from libs.jwt_auth import token_required, role_required
from libs.response import success_response, error_response, not_found_response

courses_bp = Blueprint('courses', __name__)

@courses_bp.route('', methods=['POST'])
@token_required
def create_course():
    try:
        user = User.query.get(request.current_user_id)
        if user.role != User.ROLE_TEACHER:
            return error_response('仅教师可创建课程', 403)

        data = request.get_json()
        name = data.get('name')
        code = data.get('code')
        description = data.get('description')

        if not name:
            return error_response('课程名称不能为空')

        # 检查当前教师是否已创建同名课程
        existing_course = Course.query.filter_by(
            teacher_id=request.current_user_id,
            name=name,
            is_active=True
        ).first()

        if existing_course:
            # 找到同名课程，直接返回该课程的ID
            print(f"[INFO] 课程已存在，复用课程ID: {existing_course.id}, 名称: {name}")
            return success_response('课程已存在，直接使用', {
                'id': existing_course.id,
                'name': existing_course.name,
                'message': '该课程已存在，已为您复用'
            })

        # 未找到同名课程，创建新课程
        course = Course(
            name=name,
            code=code,
            teacher_id=request.current_user_id,
            description=description
        )
        db.session.add(course)
        db.session.commit()

        print(f"[OK] 新课程创建成功，课程ID: {course.id}, 名称: {name}")
        return success_response('课程创建成功', {'id': course.id})
    except Exception as e:
        db.session.rollback()
        return error_response(f'创建课程失败: {str(e)}')

@courses_bp.route('/<int:course_id>', methods=['PUT'])
@token_required
def update_course(course_id):
    try:
        user = User.query.get(request.current_user_id)
        if user.role != User.ROLE_TEACHER:
            return error_response('仅教师可修改课程', 403)
        
        course = Course.query.get(course_id)
        if not course:
            return not_found_response('课程不存在')
        
        if course.teacher_id != request.current_user_id:
            return error_response('无权限修改此课程', 403)
        
        data = request.get_json()
        name = data.get('name')
        code = data.get('code')
        description = data.get('description')
        is_active = data.get('is_active')
        
        if name:
            course.name = name
        if code is not None:
            course.code = code
        if description is not None:
            course.description = description
        if is_active is not None:
            course.is_active = is_active
        
        db.session.commit()
        
        return success_response('课程更新成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新课程失败: {str(e)}')

@courses_bp.route('/<int:course_id>', methods=['DELETE'])
@token_required
def delete_course(course_id):
    try:
        user = User.query.get(request.current_user_id)
        if user.role != User.ROLE_TEACHER:
            return error_response('仅教师可删除课程', 403)
        
        course = Course.query.get(course_id)
        if not course:
            return not_found_response('课程不存在')
        
        if course.teacher_id != request.current_user_id:
            return error_response('无权限删除此课程', 403)
        
        course.is_active = False
        db.session.commit()
        
        return success_response('课程删除成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除课程失败: {str(e)}')

@courses_bp.route('', methods=['GET'])
@token_required
def get_courses():
    try:
        user = User.query.get(request.current_user_id)
        
        if user.role == User.ROLE_TEACHER:
            courses = Course.query.filter_by(
                teacher_id=request.current_user_id,
                is_active=True
            ).order_by(Course.created_at.desc()).all()
        else:
            return error_response('仅教师可查看课程列表', 403)

        result = [course.to_dict() for course in courses]
        return success_response('获取课程列表成功', result)
    except Exception as e:
        return error_response(f'获取课程列表失败: {str(e)}')

@courses_bp.route('/<int:course_id>', methods=['GET'])
@token_required
def get_course(course_id):
    try:
        course = Course.query.get(course_id)
        if not course:
            return not_found_response('课程不存在')

        return success_response('获取课程成功', course.to_dict())
    except Exception as e:
        return error_response(f'获取课程失败: {str(e)}')
