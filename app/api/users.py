from flask import jsonify, request
from flask_login import current_user, login_required
from app.models.user import User
from app.api import api

@api.route('/users/me', methods=['GET'])
@login_required
def get_current_user():
    """获取当前登录用户信息"""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'role': current_user.role,
        'is_admin': current_user.is_admin,
        'last_login': current_user.last_login.isoformat() if current_user.last_login else None,
        'created_at': current_user.created_at.isoformat()
    })

@api.route('/users', methods=['GET'])
@login_required
def get_users():
    """获取用户列表（管理员专用）"""
    if not current_user.is_admin:
        return jsonify({'error': '权限不足'}), 403

    users = User.query.all()
    user_list = []
    
    for user in users:
        user_list.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_admin': user.is_admin,
            'created_at': user.created_at.isoformat()
        })
    
    return jsonify({'users': user_list})

@api.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    """获取特定用户信息（管理员或本人）"""
    # 只有管理员或本人可以查看用户详情
    if not current_user.is_admin and current_user.id != user_id:
        return jsonify({'error': '权限不足'}), 403
    
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat()
    }) 