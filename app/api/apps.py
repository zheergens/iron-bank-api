from flask import jsonify, request, current_app
from flask_login import current_user, login_required
from app.models.application import Application, UserApplication, ApplicationRequest
from app.api import api
from app.utils.decorators import admin_required

@api.route('/apps', methods=['GET'])
@login_required
def get_apps():
    """获取应用列表"""
    # 如果是管理员，返回所有应用
    # 如果是普通用户，只返回有权限访问的应用
    
    apps = []
    
    for app_id, app_data in current_app.config['REGISTERED_APPS'].items():
        # 检查用户是否已经有权限访问此应用
        has_access = UserApplication.user_has_access(current_user.id, app_id)
        
        # 管理员看所有，普通用户只看有权限的
        if current_user.is_admin or has_access:
            apps.append({
                'id': app_id,
                'name': app_data['name'],
                'description': app_data.get('description', ''),
                'redirect_uri': app_data['redirect_uri'],
                'has_access': has_access
            })
    
    return jsonify({'apps': apps})

@api.route('/apps/<app_id>', methods=['GET'])
@login_required
def get_app(app_id):
    """获取特定应用信息"""
    app_data = current_app.config['REGISTERED_APPS'].get(app_id)
    if not app_data:
        return jsonify({'error': '应用不存在'}), 404
    
    # 检查用户是否有权限访问
    has_access = UserApplication.user_has_access(current_user.id, app_id)
    if not current_user.is_admin and not has_access:
        return jsonify({'error': '权限不足'}), 403
    
    return jsonify({
        'id': app_id,
        'name': app_data['name'],
        'description': app_data.get('description', ''),
        'redirect_uri': app_data['redirect_uri'],
        'has_access': has_access
    })

@api.route('/apps/<app_id>/request', methods=['POST'])
@login_required
def request_app_access(app_id):
    """申请应用访问权限"""
    app_data = current_app.config['REGISTERED_APPS'].get(app_id)
    if not app_data:
        return jsonify({'error': '应用不存在'}), 404
    
    # 获取申请原因
    data = request.get_json() or {}
    reason = data.get('reason', '')
    
    # 检查用户是否已经有权限访问此应用
    if UserApplication.user_has_access(current_user.id, app_id):
        return jsonify({'error': '您已经拥有此应用的访问权限'}), 400
    
    # 检查是否已有待处理的申请
    existing_request = ApplicationRequest.query.filter_by(
        user_id=current_user.id,
        app_id=app_id,
        status='pending'
    ).first()
    
    if existing_request:
        return jsonify({'error': '您已经提交过此应用的访问权限申请，请等待审批'}), 400
    
    # 创建新的申请
    app_request = ApplicationRequest(
        user_id=current_user.id,
        app_id=app_id,
        reason=reason
    )
    
    try:
        app_request.save()
        return jsonify({'success': True, 'message': '申请已提交，请等待管理员审批'})
    except Exception as e:
        return jsonify({'error': f'申请提交失败: {str(e)}'}), 500 