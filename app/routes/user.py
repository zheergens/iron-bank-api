from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.models.application import ApplicationRequest, UserApplication, Application
from werkzeug.security import check_password_hash
import datetime

user = Blueprint('user', __name__)

@user.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码页面"""
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证旧密码
        if not current_user.check_password(old_password):
            flash('旧密码不正确')
            return render_template('user/change_password.html')
        
        # 验证新密码和确认密码是否一致
        if new_password != confirm_password:
            flash('新密码和确认密码不一致')
            return render_template('user/change_password.html')
        
        # 验证新密码是否符合要求（例如：长度、复杂度等）
        if len(new_password) < 6:
            flash('新密码长度不能少于6位')
            return render_template('user/change_password.html')
        
        # 更新密码
        current_user.set_password(new_password)
        current_user.updated_at = datetime.datetime.utcnow().replace(tzinfo=None)
        current_user.save()
        
        flash('密码修改成功')
        return redirect(url_for('index'))
    
    return render_template('user/change_password.html')

@user.route('/profile')
@login_required
def profile():
    """用户个人资料页面"""
    # 获取用户可访问的应用列表
    user_apps = UserApplication.collection().find({'user_id': current_user.id})
    app_ids = [user_app['app_id'] for user_app in user_apps]
    
    # 获取应用详情
    applications = []
    for app_id in app_ids:
        app = Application.find_by_id(app_id)
        if app:
            applications.append(app)
    
    return render_template('user/profile.html', user=current_user, applications=applications)

@user.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    """更新用户个人资料"""
    if request.method == 'GET':
        return render_template('user/edit_profile.html')
        
    phone = request.form.get('phone')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # 更新手机号
    if phone:
        # 验证手机号是否已经被其他用户使用
        existing_user = User.find_by_phone(phone)
        if existing_user and existing_user.id != current_user.id:
            flash('该手机号已被其他用户使用')
            return redirect(url_for('user.profile'))
        
        current_user.phone = phone
    
    # 更新密码
    if new_password:
        # 验证新密码和确认密码是否一致
        if new_password != confirm_password:
            flash('新密码和确认密码不一致')
            return redirect(url_for('user.profile'))
        
        # 验证新密码是否符合要求（例如：长度、复杂度等）
        if len(new_password) < 6:
            flash('新密码长度不能少于6位')
            return redirect(url_for('user.profile'))
        
        current_user.set_password(new_password)
    
    # 更新资料
    current_user.updated_at = datetime.datetime.utcnow().replace(tzinfo=None)
    current_user.save()
    
    flash('个人资料更新成功')
    return redirect(url_for('user.profile'))

@user.route('/request_app/<app_id>', methods=['POST'])
@login_required
def request_app(app_id):
    """申请应用访问权限"""
    # 检查用户是否已经有权限
    existing_access = UserApplication.find_by_user_and_app(current_user.id, app_id)
    if existing_access:
        flash('您已经有权限访问此应用')
        return redirect(url_for('user.profile'))
        
    # 检查是否有待处理的申请
    existing_request = ApplicationRequest.find_by_user_and_app(current_user.id, app_id)
    if existing_request and existing_request.status == 'pending':
        flash('您已提交过申请，请等待管理员审批')
        return redirect(url_for('user.profile'))
        
    # 检查应用是否存在
    app = Application.find_by_id(app_id)
    if not app:
        flash('应用不存在')
        return redirect(url_for('user.profile'))
        
    # 创建新的申请
    app_request = ApplicationRequest(
        user_id=current_user.id,
        app_id=app_id,
        status='pending',
        created_at=datetime.datetime.utcnow().replace(tzinfo=None)
    )
    app_request.save()
    
    flash('申请已提交，请等待管理员审批')
    return redirect(url_for('user.profile'))

@user.route('/update_password', methods=['POST'])
@login_required
def update_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # 验证所有必填字段
    if not all([old_password, new_password, confirm_password]):
        flash('请填写所有密码字段', 'error')
        return redirect(url_for('user.change_password'))
    
    # 验证当前密码
    if not current_user.check_password(old_password):
        flash('当前密码错误', 'error')
        return redirect(url_for('user.change_password'))
    
    # 验证新密码
    if new_password != confirm_password:
        flash('新密码两次输入不一致', 'error')
        return redirect(url_for('user.change_password'))
    
    # 验证新密码长度
    if len(new_password) < 6:
        flash('新密码长度至少为6个字符', 'error')
        return redirect(url_for('user.change_password'))
        
    # 验证新密码与旧密码不同
    if old_password == new_password:
        flash('新密码不能与当前密码相同', 'error')
        return redirect(url_for('user.change_password'))
    
    current_user.set_password(new_password)
    current_user.save()
    flash('密码修改成功', 'success')
    return redirect(url_for('user.change_password'))

@user.route('/app_permissions')
@login_required
def app_permissions():
    """应用权限申请页面"""
    # 获取所有活跃的应用
    applications = Application.get_all_active()
    
    # 获取用户的申请状态
    for app in applications:
        # 检查是否已经授权
        user_app = UserApplication.find_by_user_and_app(current_user.id, app.id)
        if user_app:
            app.request_status = 'approved'
            continue
            
        # 检查是否有待处理的申请
        app_request = ApplicationRequest.find_by_user_and_app(current_user.id, app.id)
        if app_request:
            app.request_status = app_request.status
            app.reject_reason = getattr(app_request, 'reject_reason', None)
        else:
            app.request_status = None
    
    return render_template('user/app_permissions.html', applications=applications)

@user.route('/request_permission', methods=['POST'])
@login_required
def request_permission():
    """提交应用权限申请"""
    try:
        data = request.get_json()
        app_id = data.get('app_id')
        reason = data.get('reason', '')
        
        if not app_id:
            return jsonify({'success': False, 'message': '缺少应用ID'}), 400
            
        # 检查应用是否存在
        app = Application.find_by_id(app_id)
        if not app:
            return jsonify({'success': False, 'message': '应用不存在'}), 404
            
        # 检查是否已经授权
        user_app = UserApplication.find_by_user_and_app(current_user.id, app_id)
        if user_app:
            return jsonify({'success': False, 'message': '您已经拥有该应用的访问权限'}), 400
            
        # 检查是否有待处理的申请
        app_request = ApplicationRequest.find_by_user_and_app(current_user.id, app_id)
        if app_request and app_request.status == 'pending':
            return jsonify({'success': False, 'message': '您已经提交过申请，请等待审核'}), 400
            
        # 创建新的申请
        new_request = ApplicationRequest(
            user_id=current_user.id,
            app_id=app_id
        )
        if reason:
            new_request.reason = reason
        new_request.save()
        
        return jsonify({
            'success': True,
            'message': '申请已提交，请等待审核'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error requesting permission: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500 