from flask import jsonify

def success_response(message='操作成功', data=None):
    response = {
        'code': 200,
        'message': message,
        'data': data
    }
    return jsonify(response), 200

def created_response(message='创建成功', data=None):
    response = {
        'code': 201,
        'message': message,
        'data': data
    }
    return jsonify(response), 201

def bad_request_response(message='请求参数错误', code=400):
    response = {
        'code': code,
        'message': message,
        'data': None
    }
    return jsonify(response), code

def unauthorized_response(message='未授权', code=401):
    response = {
        'code': code,
        'message': message,
        'data': None
    }
    return jsonify(response), code

def forbidden_response(message='禁止访问', code=403):
    response = {
        'code': code,
        'message': message,
        'data': None
    }
    return jsonify(response), code

def not_found_response(message='资源不存在', code=404):
    response = {
        'code': code,
        'message': message,
        'data': None
    }
    return jsonify(response), code

def error_response(message='服务器错误', code=500):
    response = {
        'code': code,
        'message': message,
        'data': None
    }
    return jsonify(response), code