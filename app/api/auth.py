from flask import jsonify, request
from app.services.auth_service import AuthService
from app.api import api

@api.route('/auth/login', methods=['POST'])
def login():
    """用户登录API"""
    data = request.get_json()
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    
    username = data.get('username')
    password = data.get('password')
    remember = data.get('remember', False)
    
    if not username or not password:
        return jsonify({'error': '请提供用户名和密码'}), 400
    
    user, error = AuthService.login(username, password, remember)
    if error:
        return jsonify({'error': error}), 401
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    }), 200

@api.route('/auth/logout', methods=['POST'])
def logout():
    """用户登出API"""
    success, message = AuthService.logout()
    return jsonify({'success': success, 'message': message}), 200 