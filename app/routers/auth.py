from flask import Blueprint, request
from libs.db import db
from app.models.user import User
from libs.jwt_auth import generate_token
from libs.response import created_response, success_response, bad_request_response, unauthorized_response, forbidden_response, not_found_response

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v2/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('phone') or not data.get('password'):
        return bad_request_response('用户名、手机号和密码不能为空')
    
    if User.query.filter_by(username=data['username']).first():
        return bad_request_response('用户名已存在')
    
    if User.query.filter_by(phone=data['phone']).first():
        return bad_request_response('手机号已被注册')
    
    user = User(
        username=data['username'],
        password=data['password'],
        phone=data['phone'],
        role=User.ROLE_STUDENT,
        user_img=None
    )
    
    db.session.add(user)
    db.session.commit()
    
    return created_response('注册成功', {'user': user.to_dict()})

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('phone') or not data.get('password'):
        return bad_request_response('手机号和密码不能为空')
    
    user = User.query.filter_by(phone=data['phone']).first()
    
    if not user or user.password != data['password']:
        return unauthorized_response('手机号或密码错误')
    
    token = generate_token(user.id, user.role)
    
    return success_response('登录成功', {'token': token, 'user': user.to_dict()})

@auth_bp.route('/logout', methods=['POST'])
def logout():
    return success_response('登出成功')

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    token = request.headers.get('Authorization')
    
    if not token or not token.startswith('Bearer '):
        return unauthorized_response('Token缺失或格式错误')
    
    token = token.split(' ')[1]
    
    from libs.jwt_auth import decode_token
    payload = decode_token(token)
    
    if not payload:
        return unauthorized_response('Token无效或已过期')
    
    user = User.query.get(payload['user_id'])
    
    if not user:
        return not_found_response('用户不存在')
    
    return success_response('获取成功', {'user': user.to_dict()})