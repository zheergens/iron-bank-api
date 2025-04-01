from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app.models.application import Application, ApplicationRequest
from app.decorators import admin_required
import datetime

api_apps = Blueprint('api_apps', __name__)

@api_apps.route('/apps', methods=['GET'])
@login_required
def get_apps():
    """获取应用列表"""
    try:
        # 获取所有活跃的应用
        apps = Application.get_all_active()
        
        # 获取用户已授权的应用
        user_apps = ApplicationRequest.get_user_apps(current_user.id)
        user_app_ids = {str(app.app_id) for app in user_apps}
        
        # 构建响应数据
        result = []
        for app in apps:
            app_data = app.to_dict()
            app_data['id'] = str(app._id)
            app_data['has_access'] = str(app._id) in user_app_ids
            result.append(app_data)
            
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting apps: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取应用列表失败'
        }), 500

@api_apps.route('/apps/<app_id>/request', methods=['POST'])
@login_required
def request_access(app_id):
    """申请应用访问权限"""
    try:
        # 检查应用是否存在
        app = Application.find_by_id(app_id)
        if not app:
            return jsonify({
                'success': False,
                'message': '应用不存在'
            }), 404
            
        # 检查是否已经有访问权限
        if ApplicationRequest.check_user_access(current_user.id, app_id):
            return jsonify({
                'success': False,
                'message': '您已经拥有该应用的访问权限'
            }), 400
            
        # 检查是否有待处理的申请
        existing_request = ApplicationRequest.find_by_user_and_app(current_user.id, app_id)
        if existing_request and existing_request.status == 'pending':
            return jsonify({
                'success': False,
                'message': '您已经提交过申请，请等待审核'
            }), 400
            
        # 创建新的申请
        app_request = ApplicationRequest(
            user_id=current_user.id,
            app_id=app_id,
            status='pending'
        )
        app_request.save()
        
        return jsonify({
            'success': True,
            'message': '申请已提交，请等待审核'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error requesting access: {str(e)}")
        return jsonify({
            'success': False,
            'message': '申请访问权限失败'
        }), 500

@api_apps.route('/apps/<app_id>/revoke', methods=['POST'])
@login_required
def revoke_access(app_id):
    """撤销应用访问权限"""
    try:
        # 将用户的应用请求状态更新为rejected
        result = ApplicationRequest.collection().update_many(
            {
                'user_id': current_user.id,
                'app_id': app_id,
                'status': 'approved'
            },
            {
                '$set': {
                    'status': 'rejected',
                    'updated_at': datetime.datetime.utcnow(),
                    'processed_at': datetime.datetime.utcnow(),
                    'processed_by': current_user.id
                }
            }
        )
        
        if result.modified_count > 0:
            return jsonify({
                'success': True,
                'message': '已撤销应用访问权限'
            })
        else:
            return jsonify({
                'success': False,
                'message': '您没有该应用的访问权限'
            }), 404
            
    except Exception as e:
        current_app.logger.error(f"Error revoking access: {str(e)}")
        return jsonify({
            'success': False,
            'message': '撤销访问权限失败'
        }), 500 