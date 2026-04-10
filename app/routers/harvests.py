from flask import Blueprint, request
from libs.db import db
from app.models.harvest import Harvest
from libs.jwt_auth import token_required
from libs.response import success_response, created_response, bad_request_response, not_found_response, forbidden_response, error_response

harvests_bp = Blueprint('harvests', __name__, url_prefix='/api/v2/harvests')

@harvests_bp.route('', methods=['GET'])
@token_required
def get_harvests():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        
        if page < 1:
            return bad_request_response('页码必须大于0')
        if per_page < 1 or per_page > 100:
            return bad_request_response('每页数量必须在1-100之间')
        
        query = Harvest.query.filter_by(user_id=request.current_user_id)
        pagination = query.order_by(Harvest.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        harvests = pagination.items
        
        return success_response('获取成功', {
            'harvests': [harvest.to_dict() for harvest in harvests],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return error_response(f'获取失败: {str(e)}')

@harvests_bp.route('', methods=['POST'])
@token_required
def create_harvest():
    try:
        data = request.get_json()
        
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        
        if not title:
            return bad_request_response('标题不能为空')
        if len(title) > 255:
            return bad_request_response('标题不能超过255个字符')
        if not content:
            return bad_request_response('内容不能为空')
        if len(content) > 50000:
            return bad_request_response('内容不能超过50000个字符')
        
        harvest = Harvest(
            user_id=request.current_user_id,
            title=title,
            content=content
        )
        
        db.session.add(harvest)
        db.session.commit()
        
        return created_response('发布成功', {'harvest': harvest.to_dict()})
    except Exception as e:
        db.session.rollback()
        return error_response(f'发布失败: {str(e)}')

@harvests_bp.route('/<int:harvest_id>', methods=['GET'])
@token_required
def get_harvest(harvest_id):
    try:
        harvest = Harvest.query.get(harvest_id)
        
        if not harvest:
            return not_found_response('收获不存在')
        
        if harvest.user_id != request.current_user_id:
            return forbidden_response('无权访问该收获')
        
        return success_response('获取成功', {'harvest': harvest.to_dict()})
    except Exception as e:
        return error_response(f'获取失败: {str(e)}')

@harvests_bp.route('/<int:harvest_id>', methods=['DELETE'])
@token_required
def delete_harvest(harvest_id):
    try:
        harvest = Harvest.query.get(harvest_id)
        
        if not harvest:
            return not_found_response('收获不存在')
        
        if harvest.user_id != request.current_user_id:
            return forbidden_response('无权删除该收获')
        
        db.session.delete(harvest)
        db.session.commit()
        
        return success_response('删除成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除失败: {str(e)}')
