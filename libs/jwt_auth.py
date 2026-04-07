import jwt
import yaml
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

JWT_SECRET_KEY = config['jwt']['secret_key']
JWT_ALGORITHM = config['jwt']['algorithm']
JWT_EXPIRATION = config['jwt']['expiration']

def generate_token(user_id, role):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def decode_token(token):
    try:
        print(f"DEBUG: Decoding token...")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        print(f"DEBUG: Token decoded successfully")
        return payload
    except jwt.ExpiredSignatureError as e:
        print(f"DEBUG: Token expired: {str(e)}")
        return None
    except jwt.InvalidTokenError as e:
        print(f"DEBUG: Invalid token: {str(e)}")
        return None
    except Exception as e:
        print(f"DEBUG: Token decode error: {type(e).__name__}: {str(e)}")
        return None

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            print("DEBUG: No Authorization header found")
            return jsonify({'error': 'Token is missing'}), 401
        
        
        if 'Bearer' not in token:
            print("DEBUG: No 'Bearer' in Authorization header")
            return jsonify({'error': 'Invalid token format'}), 401
        
        token = token.replace('Bearer ', '').strip()
        
        payload = decode_token(token)
        if not payload:
            print("DEBUG: decode_token returned None")
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        from flask import g
        g.user_id = payload['user_id']
        g.user_role = payload['role']
        request.current_user_id = g.user_id
        request.current_user_role = g.user_role
        
        print(f"DEBUG: User authenticated: user_id={g.user_id}, role={g.user_role}")
        
        return f(*args, **kwargs)
    
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            
            if not token:
                return jsonify({'error': 'Token is missing'}), 401
            
            if 'Bearer' not in token:
                return jsonify({'error': 'Invalid token format'}), 401
            
            token = token.replace('Bearer ', '').strip()
            
            payload = decode_token(token)
            if not payload:
                return jsonify({'error': 'Token is invalid or expired'}), 401
            
            print(f"DEBUG role_required: payload = {payload}")
            try:
                user_role = payload['role']
                print(f"DEBUG role_required: user_role = {user_role} (type: {type(user_role)}), allowed_roles = {allowed_roles}")
                print(f"DEBUG role_required: user_role in allowed_roles = {user_role in allowed_roles}")
                if user_role not in allowed_roles:
                    print(f"DEBUG role_required: Permission denied!")
                    return jsonify({'error': 'Insufficient permissions'}), 403
            except KeyError as e:
                print(f"DEBUG role_required: KeyError - {e}")
                return jsonify({'error': 'Invalid token payload'}), 401
            
            from flask import g
            g.user_id = payload['user_id']
            g.user_role = user_role
            
            return f(*args, **kwargs)
        return decorated_function
    
    return decorator
