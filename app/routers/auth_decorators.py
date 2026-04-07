from functools import wraps
from flask import request, jsonify
from libs.jwt_auth import decode_token

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token or not token.startswith('Bearer '):
            return jsonify({'success': False, 'message': 'Token缺失或格式错误'}), 401
        
        token = token.split(' ')[1]
        
        payload = decode_token(token)
        
        if not payload:
            return jsonify({'success': False, 'message': 'Token无效或已过期'}), 401
        
        request.current_user_id = payload['user_id']
        request.current_user_role = payload.get('role', 0)
        
        return f(*args, **kwargs)
    return decorated_function
