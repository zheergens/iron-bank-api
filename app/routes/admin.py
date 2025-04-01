from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.models.application import Application, ApplicationRequest, UserApplication
from app.decorators import admin_required
import datetime
import random
from flask_wtf import FlaskForm
from bson import ObjectId

admin = Blueprint('admin', __name__)

@admin.route('/')
@login_required
@admin_required
def index():
    # 获取统计数据
    total_users = User.collection().count_documents({})
    today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0)
    active_users_today = User.collection().count_documents({
        'last_login': {'$gte': today_start}
    })
    pending_requests = ApplicationRequest.collection().count_documents({'status': 'pending'})
    
    stats = {
        'total_users': total_users,
        'active_users_today': active_users_today,
        'pending_requests': pending_requests
    }
    
    # 获取最近活动（示例数据）
    recent_activities = []
    # TODO: 实现实际的活动记录逻辑
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_activities=recent_activities)

@admin.route('/users')
@login_required
@admin_required
def users():
    """用户管理页面"""
    # 获取所有用户
    all_users = [User.from_dict(user) for user in User.collection().find()]
    
    # 先按照激活状态排序（激活的用户在前），再按照注册时间排序（注册时间早的在前）
    sorted_users = sorted(all_users, key=lambda u: (not u.is_active, u.created_at.timestamp() if u.created_at else 0))
    
    return render_template('admin/users.html', users=sorted_users)

@admin.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    """创建新用户"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        role = request.form.get('role', 'user')
        
        # 设置默认密码为用户名+123
        default_password = username + '123'
        
        # 创建用户
        user, error = User.create_user(
            username=username,
            email=email,
            password=default_password,  # 使用默认密码
            phone=phone,
            is_admin=(role == 'admin')
        )
        
        if user:
            flash('用户创建成功，默认密码为：' + default_password)
            return redirect(url_for('admin.users'))
        else:
            flash('创建用户失败：' + error)
            
    return render_template('admin/users/new.html')

@admin.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    try:
        user = User.find_by_id(user_id)
        if not user:
            flash('用户不存在')
            return redirect(url_for('admin.users'))
            
        form = FlaskForm()
        
        if request.method == 'POST':
            if not form.validate():
                flash('表单验证失败，请重试')
                return render_template('admin/users/edit.html', form=form, user=user)
            
            # 更新用户信息
            user.username = request.form.get('username')
            user.email = request.form.get('email')
            user.phone = request.form.get('phone')
            user.role = request.form.get('role', 'user')
            
            # 如果提供了新密码，则更新密码
            new_password = request.form.get('password')
            if new_password:
                user.set_password(new_password)
            
            user.save()
            flash('用户信息更新成功')
            return redirect(url_for('admin.users'))
            
        return render_template('admin/users/edit.html', form=form, user=user)
        
    except Exception as e:
        current_app.logger.error(f"Error editing user: {str(e)}")
        flash('编辑用户时发生错误')
        return redirect(url_for('admin.users'))

@admin.route('/users/<user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """禁用用户"""
    try:
        # 先查找用户
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
            
        # 不允许禁用管理员用户
        if user.is_admin:
            return jsonify({'success': False, 'message': '不能禁用管理员用户'}), 400
            
        # 更新用户状态为禁用
        result = User.collection().update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'is_active': False}}
        )
        
        if result.modified_count > 0:
            return jsonify({
                'success': True,
                'message': f'用户 {user.username} 已成功禁用'
            })
        else:
            return jsonify({'success': False, 'message': '禁用用户失败'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error disabling user: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin.route('/system_info')
@login_required
@admin_required
def system_info():
    # 获取注册的应用
    apps = Application.get_all_active()
    return render_template('admin/system_info.html', apps=apps)

@admin.route('/apps/<app_id>/users')
@login_required
@admin_required
def manage_app_users(app_id):
    # 获取应用信息
    app = Application.find_by_app_id(app_id)
    if not app:
        flash('应用不存在')
        return redirect(url_for('admin.system_info'))
    
    # 获取已授权的用户
    user_apps = UserApplication.find_by_app_id(app_id)
    users = []
    for user_app in user_apps:
        user = User.find_by_id(user_app.user_id)
        if user:
            users.append(user)
    
    return render_template('admin/app_users.html', app=app, users=users)

@admin.route('/apps/<app_id>/users/<user_id>/add', methods=['POST'])
@login_required
@admin_required
def add_app_user(app_id, user_id):
    # 授权用户访问应用
    user_app = UserApplication(user_id=user_id, app_id=app_id)
    user_app.save()
    flash('用户授权成功')
    return redirect(url_for('admin.manage_app_users', app_id=app_id))

@admin.route('/apps/<app_id>/users/<user_id>/remove', methods=['POST'])
@login_required
@admin_required
def remove_app_user(app_id, user_id):
    # 移除用户访问应用的授权
    user_app = UserApplication.find_by_user_and_app(user_id, app_id)
    if user_app:
        user_app.delete()
        flash('用户授权已移除')
    return redirect(url_for('admin.manage_app_users', app_id=app_id))

@admin.route('/apps/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_app():
    """创建新应用"""
    if request.method == 'POST':
        # 获取表单数据
        name = request.form.get('name')
        description = request.form.get('description')
        redirect_uri = request.form.get('redirect_uri')
        
        # 生成客户端ID和密钥
        client_id = 'client_' + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=16))
        client_secret = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=32))
        
        # 创建新应用
        app = Application(
            name=name,
            description=description,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            is_active=True
        )
        
        # 保存应用
        try:
            app.save()
            return jsonify({
                'success': True, 
                'message': f'应用 {name} 创建成功',
                'app': {
                    'id': app.id,
                    'name': app.name,
                    'client_id': app.client_id,
                    'client_secret': app.client_secret
                }
            })
        except Exception as e:
            current_app.logger.error(f"Error creating app: {str(e)}")
            return jsonify({'success': False, 'message': f'创建应用失败：{str(e)}'}), 500
    
    # GET请求不应该到达这里，因为我们使用的是模态框
    return redirect(url_for('admin.system_info'))

@admin.route('/apps/<app_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_app(app_id):
    # 在此处实现编辑应用的逻辑
    pass

@admin.route('/apps/<app_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_app(app_id):
    """删除应用"""
    try:
        # 查找应用
        app = Application.find_by_id(app_id)
        if not app:
            return jsonify({'success': False, 'message': '应用不存在'}), 404
            
        # 删除与应用相关的授权
        UserApplication.collection().delete_many({'app_id': app_id})
        
        # 删除应用
        app.delete()
        
        return jsonify({
            'success': True, 
            'message': f'应用 {app.name} 已成功删除'
        })
            
    except Exception as e:
        current_app.logger.error(f"Error deleting app: {str(e)}")
        return jsonify({'success': False, 'message': f'删除应用失败：{str(e)}'}), 500

@admin.route('/app_requests')
@login_required
@admin_required
def app_requests():
    """应用权限申请审核页面"""
    # 获取所有待处理的申请
    requests = ApplicationRequest.find_pending_requests()
    
    # 获取用户和应用信息
    for request in requests:
        request.user = User.find_by_id(request.user_id)
        request.application = Application.find_by_id(request.app_id)
    
    return render_template('admin/app_requests.html', requests=requests)

@admin.route('/requests/<request_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_request(request_id):
    """批准应用权限申请"""
    try:
        # 查找申请记录
        request = ApplicationRequest.find_by_id(request_id)
        if not request:
            return jsonify({'success': False, 'message': '申请不存在'}), 404
            
        if request.status != 'pending':
            return jsonify({'success': False, 'message': '该申请已被处理'}), 400
            
        # 创建用户应用关联
        user_app = UserApplication(
            user_id=request.user_id,
            app_id=request.app_id
        )
        user_app.save()
        
        # 更新申请状态
        request.status = 'approved'
        request.processed_at = datetime.datetime.utcnow()
        request.processed_by = current_user.id
        request.save()
        
        return jsonify({
            'success': True,
            'message': '申请已批准'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error approving request: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin.route('/requests/<request_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_request(request_id):
    """拒绝应用权限申请"""
    try:
        # 查找申请记录
        app_request = ApplicationRequest.find_by_id(request_id)
        if not app_request:
            return jsonify({'success': False, 'message': '申请不存在'}), 404
            
        if app_request.status != 'pending':
            return jsonify({'success': False, 'message': '该申请已被处理'}), 400
            
        # 从 JSON 数据中获取拒绝原因
        data = request.get_json()
        reason = data.get('reason') if data else None
        
        if not reason:
            return jsonify({'success': False, 'message': '请提供拒绝原因'}), 400
            
        # 更新申请状态
        app_request.status = 'rejected'
        app_request.processed_at = datetime.datetime.utcnow()
        app_request.processed_by = current_user.id
        app_request.reject_reason = reason
        app_request.save()
        
        return jsonify({
            'success': True,
            'message': '申请已拒绝'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error rejecting request: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500 