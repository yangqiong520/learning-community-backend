from flask import Blueprint, request, jsonify
from libs.db import db
from app.models.year import Year
from app.models.user import User
from libs.jwt_auth import token_required
from libs.response import success_response, error_response, not_found_response

years_bp = Blueprint('years', __name__)

@years_bp.route('', methods=['GET'])
@token_required
def get_years():
    """
    获取年份列表
    超级管理员和管理员可以看到所有年份
    其他角色只能看到自己创建的年份
    """
    try:
        user = User.query.get(request.current_user_id)

        # 超级管理员和管理员可以看到所有年份（包括重复的）
        if user.role in [User.ROLE_SUPER_ADMIN, User.ROLE_ADMIN]:
            years = Year.query.filter_by(is_active=True).order_by(Year.year.desc()).all()
        else:
            # 教师和学生只能看到自己创建的年份
            years = Year.query.filter_by(
                teacher_id=request.current_user_id,
                is_active=True
            ).order_by(Year.year.desc()).all()

        result = [year.to_dict() for year in years]
        return success_response('获取年份列表成功', result)
    except Exception as e:
        return error_response(f'获取年份列表失败: {str(e)}')

@years_bp.route('', methods=['POST'])
@token_required
def create_year():
    """
    创建年份
    仅教师和管理员可以创建
    每个教师可以创建自己的年份，不同教师的年份相互独立
    """
    try:
        user = User.query.get(request.current_user_id)

        # 只有教师和管理员可以创建年份
        if user.role not in [User.ROLE_SUPER_ADMIN, User.ROLE_ADMIN, User.ROLE_TEACHER]:
            return error_response('只有教师和管理员可以创建年份', 403)

        data = request.get_json()
        year = data.get('year')
        name = data.get('name')

        if not year:
            return error_response('年份不能为空')
        if not name:
            return error_response('年份名称不能为空')

        # 检查当前教师是否已创建该年份
        existing_year = Year.query.filter_by(
            year=year,
            teacher_id=request.current_user_id
        ).first()

        if existing_year:
            # 如果年份已存在，检查是否已激活
            if existing_year.is_active:
                # 返回 409，提示用户该年份已存在
                return error_response(f'您已创建过该年份（ID: {existing_year.id}）', 409)
            else:
                # 如果已软删除，重新激活
                existing_year.is_active = True
                existing_year.name = name
                db.session.commit()
                return success_response('创建年份成功', existing_year.to_dict())

        # 如果不存在，创建新年份
        new_year = Year(
            year=year,
            name=name,
            teacher_id=request.current_user_id
        )

        db.session.add(new_year)
        db.session.commit()

        return success_response('创建年份成功', new_year.to_dict())
    except Exception as e:
        db.session.rollback()
        return error_response(f'创建年份失败: {str(e)}')

@years_bp.route('/<int:year_id>', methods=['PUT'])
@token_required
def update_year(year_id):
    """
    更新年份
    只有创建者或管理员可以更新
    """
    try:
        year = Year.query.get(year_id)
        if not year:
            return not_found_response('年份不存在')
        
        user = User.query.get(request.current_user_id)
        
        # 只有创建者、管理员或超级管理员可以更新
        if year.teacher_id != request.current_user_id and user.role not in [User.ROLE_SUPER_ADMIN, User.ROLE_ADMIN]:
            return error_response('无权限更新此年份', 403)
        
        data = request.get_json()
        name = data.get('name')
        is_active = data.get('is_active')
        
        if name:
            year.name = name
        if is_active is not None:
            year.is_active = is_active
        
        db.session.commit()
        
        return success_response('更新年份成功', year.to_dict())
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新年份失败: {str(e)}')

@years_bp.route('/<int:year_id>', methods=['DELETE'])
@token_required
def delete_year(year_id):
    """
    删除年份（软删除）
    只有创建者或管理员可以删除
    注意：软删除后数据仍在数据库中，只是标记为不活跃
    """
    try:
        year = Year.query.get(year_id)
        if not year:
            return not_found_response('年份不存在')

        user = User.query.get(request.current_user_id)

        # 只有创建者、管理员或超级管理员可以删除
        if year.teacher_id != request.current_user_id and user.role not in [User.ROLE_SUPER_ADMIN, User.ROLE_ADMIN]:
            return error_response('无权限删除此年份', 403)

        # 软删除：只标记为不活跃
        year.is_active = False
        db.session.commit()

        return success_response('删除年份成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除年份失败: {str(e)}')
