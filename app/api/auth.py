from flask import Blueprint, jsonify, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.application import Application, ApplicationRequest
import datetime

api_auth = Blueprint('api_auth', __name__)

@api_auth.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400
            
        # 查找用户
        user = User.find_by_username(username)
        if not user or not user.check_password(password):
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            }), 401
            
        # 检查用户是否被禁用
        if not user.is_active:
            return jsonify({
                'success': False,
                'message': '账号已被禁用，请联系管理员'
            }), 403
            
        # 登录用户
        login_user(user)
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'id': str(user._id),
                'username': user.username,
                'is_admin': user.is_admin
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in login: {str(e)}")
        return jsonify({
            'success': False,
            'message': '登录失败'
        }), 500

@api_auth.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    try:
        logout_user()
        return jsonify({
            'success': True,
            'message': '登出成功'
        })
    except Exception as e:
        current_app.logger.error(f"Error in logout: {str(e)}")
        return jsonify({
            'success': False,
            'message': '登出失败'
        }), 500

@api_auth.route('/user/info', methods=['GET'])
@login_required
def get_user_info():
    """获取当前用户信息"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'id': str(current_user._id),
                'username': current_user.username,
                'email': current_user.email,
                'phone': current_user.phone,
                'is_admin': current_user.is_admin
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error getting user info: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取用户信息失败'
        }), 500 