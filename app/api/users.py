from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models.user import User
from app.decorators import admin_required

api_users = Blueprint('api_users', __name__)

@api_users.route('/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """获取用户列表"""
    try:
        users = []
        for user in User.collection().find():
            user_data = {
                'id': str(user['_id']),
                'username': user['username'],
                'email': user['email'],
                'phone': user.get('phone'),
                'is_admin': user.get('is_admin', False),
                'created_at': user.get('created_at')
            }
            users.append(user_data)
            
        return jsonify({
            'success': True,
            'data': users
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting users: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取用户列表失败'
        }), 500

@api_users.route('/users/<user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """删除用户"""
    try:
        # 查找用户
        user = User.get_by_id(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
            
        # 不能删除自己
        if str(user._id) == str(current_user._id):
            return jsonify({
                'success': False,
                'message': '不能删除当前登录用户'
            }), 400
            
        # 删除用户
        user.delete()
        
        return jsonify({
            'success': True,
            'message': '用户已删除'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error deleting user: {str(e)}")
        return jsonify({
            'success': False,
            'message': '删除用户失败'
        }), 500 