from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from app.models.user import db
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
            flash('当前密码错误')
            return render_template('user/change_password.html')
        
        if new_password != confirm_password:
            flash('新密码两次输入不一致')
            return render_template('user/change_password.html')
        
        current_user.set_password(new_password)
        db.session.commit()
        flash('密码修改成功')
        return redirect(url_for('auth.profile'))
    
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

@user.route('/request_app_access', methods=['POST'])
@login_required
def request_app_access():
    app_id = request.form.get('app_id')
    reason = request.form.get('reason')
    
    # 验证应用ID是否有效
    app_config = current_app.config['REGISTERED_APPS'].get(app_id)
    if not app_config:
        flash('无效的应用ID')
        return redirect(url_for('auth.profile'))
    
    # 检查用户是否已经有权限访问此应用
    if UserApplication.user_has_access(current_user.id, app_id):
        flash('您已经拥有此应用的访问权限')
        return redirect(url_for('auth.profile'))
    
    # 检查是否已有待处理的申请
    existing_request = ApplicationRequest.query.filter_by(
        user_id=current_user.id,
        app_id=app_id,
        status='pending'
    ).first()
    
    if existing_request:
        flash('您已经提交过此应用的访问权限申请，请等待审批')
        return redirect(url_for('auth.profile'))
    
    # 创建新的申请
    app_request = ApplicationRequest(
        user_id=current_user.id,
        app_id=app_id,
        reason=reason
    )
    
    db.session.add(app_request)
    db.session.commit()
    
    flash('申请已提交，请等待管理员审批')
    return redirect(url_for('auth.profile')) 