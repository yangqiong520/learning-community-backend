from flask import Blueprint, request
from libs.db import db
from app.models.user import User
from libs.jwt_auth import token_required, role_required
from libs.response import success_response, created_response, bad_request_response, not_found_response
import hashlib

users_bp = Blueprint('users', __name__, url_prefix='/api/v2/users')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@users_bp.route('', methods=['GET'])
@token_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    role = request.args.get('role', type=int)
    keyword = request.args.get('keyword', '')
    
    query = User.query
    
    if role:
        query = query.filter_by(role=role)
    
    if keyword:
        query = query.filter(
            (User.username.like(f'%{keyword}%')) |
            (User.phone.like(f'%{keyword}%'))
        )
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    users = pagination.items
    
    return success_response('获取成功', {
        'users': [user.to_dict() for user in users],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@users_bp.route('/<int:user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return not_found_response('用户不存在')
    
    return success_response('获取成功', {'user': user.to_dict()})

@users_bp.route('/search-by-phone', methods=['GET'])
@token_required
def search_user_by_phone():
    phone = request.args.get('phone', '')
    
    if not phone:
        return bad_request_response('手机号不能为空')
    
    user = User.query.filter_by(phone=phone).first()
    
    if not user:
        return success_response('用户不存在', {'user': None})
    
    return success_response('查找成功', {'user': user.to_dict()})

@users_bp.route('', methods=['POST'])
@role_required(User.ROLE_SUPER_ADMIN, User.ROLE_ADMIN)
def create_user():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('phone') or not data.get('password'):
        return bad_request_response('用户名、手机号和密码不能为空')
    
    if User.query.filter_by(username=data['username']).first():
        return bad_request_response('用户名已存在')
    
    if User.query.filter_by(phone=data['phone']).first():
        return bad_request_response('手机号已被注册')
    
    role = data.get('role', User.ROLE_STUDENT)
    if role not in User.ROLE_NAMES:
        return bad_request_response('无效的角色')
    
    user = User(
        username=data['username'],
        password=hash_password(data['password']),
        phone=data['phone'],
        role=role
    )
    
    db.session.add(user)
    db.session.commit()
    
    return created_response('用户创建成功', {'user': user.to_dict()})

@users_bp.route('/<int:user_id>', methods=['PUT'])
@role_required(User.ROLE_SUPER_ADMIN, User.ROLE_ADMIN)
def update_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return not_found_response('用户不存在')
    
    data = request.get_json()
    
    if 'username' in data:
        existing_user = User.query.filter(
            User.username == data['username'],
            User.id != user_id
        ).first()
        if existing_user:
            return bad_request_response('用户名已存在')
        user.username = data['username']
    
    if 'phone' in data:
        existing_user = User.query.filter(
            User.phone == data['phone'],
            User.id != user_id
        ).first()
        if existing_user:
            return bad_request_response('手机号已被使用')
        user.phone = data['phone']
    
    if 'role' in data:
        if data['role'] not in User.ROLE_NAMES:
            return bad_request_response('无效的角色')
        user.role = data['role']

    if 'password' in data:
        user.password = hash_password(data['password'])
    
    db.session.commit()
    
    return success_response('用户更新成功', {'user': user.to_dict()})

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@role_required(User.ROLE_SUPER_ADMIN, User.ROLE_ADMIN)
def delete_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return not_found_response('用户不存在')
    
    db.session.delete(user)
    db.session.commit()

    return success_response('用户删除成功')