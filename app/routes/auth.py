from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.application import Application, UserApplication
import datetime
from urllib.parse import urlparse
import uuid

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user.profile'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.find_by_username(username)
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.update_last_login()
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('user.profile'))
        flash('用户名或密码错误', 'error')
    
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/profile')
@login_required
def profile():
    # 重定向到user蓝图中的profile路由
    return redirect(url_for('user.profile'))

@auth.route('/token', methods=['POST'])
def token():
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    auth_code = request.form.get('code')
    
    if not client_id or not client_secret or not auth_code:
        return jsonify({'error': 'Missing parameters'}), 400
    
    # 验证客户端凭据
    app_config = current_app.config['REGISTERED_APPS'].get(client_id)
    if not app_config or app_config['client_secret'] != client_secret:
        return jsonify({'error': 'Invalid client credentials'}), 401
    
    # 验证授权码
    code_data = session.get(f'auth_code_{auth_code}')
    if not code_data or code_data['client_id'] != client_id:
        return jsonify({'error': 'Invalid authorization code'}), 401
    
    # 检查授权码是否过期
    if datetime.datetime.utcnow().timestamp() > code_data['expires']:
        session.pop(f'auth_code_{auth_code}', None)
        return jsonify({'error': 'Authorization code expired'}), 401
    
    # 生成访问令牌
    user = User.find_by_id(code_data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    access_token = str(uuid.uuid4())
    expires_in = 3600  # 1小时
    
    # 存储令牌信息
    session[f'token_{access_token}'] = {
        'user_id': user.id,
        'client_id': client_id,
        'expires': (datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)).timestamp()
    }
    
    # 清除授权码
    session.pop(f'auth_code_{auth_code}', None)
    
    return jsonify({
        'access_token': access_token,
        'token_type': 'bearer',
        'expires_in': expires_in,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    })

@auth.route('/verify_token', methods=['POST'])
def verify_token():
    token = request.form.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    app_id = request.form.get('app_id')
    
    if not token:
        return jsonify({'error': 'No token provided'}), 401
    
    token_data = session.get(f'token_{token}')
    if not token_data:
        return jsonify({'error': 'Invalid token'}), 401
    
    if datetime.datetime.utcnow().timestamp() > token_data['expires']:
        session.pop(f'token_{token}', None)
        return jsonify({'error': 'Token expired'}), 401
    
    user = User.find_by_id(token_data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # 检查用户是否有权访问此应用
    if app_id and not (user.is_admin or UserApplication.user_has_access(user.id, app_id)):
        return jsonify({'error': 'Access denied for this application'}), 403
    
    return jsonify({
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role
    }) 