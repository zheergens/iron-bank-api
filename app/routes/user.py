from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from app.models.user import db, User
from app.models.application import ApplicationRequest, UserApplication

user = Blueprint('user', __name__)

@user.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(old_password):
            flash('当前密码错误', 'error')
            return redirect(url_for('user.change_password'))
        
        if new_password != confirm_password:
            flash('新密码两次输入不一致', 'error')
            return redirect(url_for('user.change_password'))
        
        current_user.set_password(new_password)
        db.session.commit()
        flash('密码修改成功', 'success')
        return redirect(url_for('user.change_password'))
    
    return render_template('user/change_password.html')

@user.route('/profile')
@login_required
def profile():
    # 获取所有可用的应用
    available_apps = []
    for app_id, app_data in current_app.config['REGISTERED_APPS'].items():
        # 检查用户是否已经有权限访问此应用
        has_access = UserApplication.user_has_access(current_user.id, app_id)
        
        # 获取用户针对此应用的申请
        pending_request = ApplicationRequest.query.filter_by(
            user_id=current_user.id, 
            app_id=app_id, 
            status='pending'
        ).first()
        
        rejected_request = ApplicationRequest.query.filter_by(
            user_id=current_user.id, 
            app_id=app_id, 
            status='rejected'
        ).order_by(ApplicationRequest.created_at.desc()).first()
        
        available_apps.append({
            'id': app_id,
            'name': app_data['name'],
            'has_access': has_access,
            'pending_request': pending_request is not None,
            'rejected_request': rejected_request is not None
        })
    
    return render_template('user/profile.html', available_apps=available_apps)

@user.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'GET':
        return render_template('user/edit_profile.html')
    
    # POST 请求逻辑
    phone = request.form.get('phone')
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # 如果任何一个密码字段被填写，则需要验证所有密码字段
    if old_password or new_password or confirm_password:
        # 确保所有密码字段都已填写
        if not all([old_password, new_password, confirm_password]):
            flash('如果要修改密码，请填写所有密码字段', 'error')
            return redirect(url_for('user.update_profile'))
        
        # 验证当前密码
        if not current_user.check_password(old_password):
            flash('当前密码错误', 'error')
            return redirect(url_for('user.update_profile'))
        
        # 验证新密码
        if new_password != confirm_password:
            flash('新密码两次输入不一致', 'error')
            return redirect(url_for('user.update_profile'))
        
        # 验证新密码长度
        if len(new_password) < 6:
            flash('新密码长度至少为6个字符', 'error')
            return redirect(url_for('user.update_profile'))
            
        # 验证新密码与旧密码不同
        if old_password == new_password:
            flash('新密码不能与当前密码相同', 'error')
            return redirect(url_for('user.update_profile'))
        
        try:
            current_user.set_password(new_password)
            db.session.commit()
            flash('密码修改成功', 'success')
        except Exception as e:
            db.session.rollback()
            flash('密码修改失败，请稍后重试', 'error')
            return redirect(url_for('user.update_profile'))
    
    # 处理手机号更新
    if phone:
        success, message = current_user.update_profile(phone=phone)
        if not success:
            flash(message, 'error')
            return redirect(url_for('user.update_profile'))
        flash('手机号更新成功', 'success')
    
    return redirect(url_for('user.update_profile'))

@user.route('/request_app_access', methods=['POST'])
@login_required
def request_app_access():
    app_id = request.form.get('app_id')
    reason = request.form.get('reason')
    
    # 验证应用ID是否有效
    app_config = current_app.config['REGISTERED_APPS'].get(app_id)
    if not app_config:
        flash('无效的应用ID')
        return redirect(url_for('user.profile'))
    
    # 检查用户是否已经有权限访问此应用
    if UserApplication.user_has_access(current_user.id, app_id):
        flash('您已经拥有此应用的访问权限')
        return redirect(url_for('user.profile'))
    
    # 检查是否已有待处理的申请
    existing_request = ApplicationRequest.query.filter_by(
        user_id=current_user.id,
        app_id=app_id,
        status='pending'
    ).first()
    
    if existing_request:
        flash('您已经提交过此应用的访问权限申请，请等待审批')
        return redirect(url_for('user.profile'))
    
    # 创建新的申请
    app_request = ApplicationRequest(
        user_id=current_user.id,
        app_id=app_id,
        reason=reason
    )
    
    db.session.add(app_request)
    db.session.commit()
    
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
    
    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash('密码修改成功', 'success')
        return redirect(url_for('user.change_password'))
    except Exception as e:
        db.session.rollback()
        flash('密码修改失败，请稍后重试', 'error')
        return redirect(url_for('user.change_password')) 