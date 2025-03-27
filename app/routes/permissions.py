from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Application, AppRequest
from app import db

bp = Blueprint('permissions', __name__)

@bp.route('/permissions')
@login_required
def index():
    # 获取所有可用的应用程序
    apps = Application.query.all()
    for app in apps:
        # 检查用户是否已经有访问权限
        app.has_access = False  # 这里需要根据实际情况检查用户是否有权限
        # 检查是否有待处理的申请
        pending_request = AppRequest.query.filter_by(
            user_id=current_user.id,
            app_id=app.id,
            status='pending'
        ).first()
        app.pending_request = pending_request is not None
        # 检查是否有被拒绝的申请
        rejected_request = AppRequest.query.filter_by(
            user_id=current_user.id,
            app_id=app.id,
            status='rejected'
        ).first()
        app.rejected_request = rejected_request is not None

    return render_template('user/permissions.html', available_apps=apps)

@bp.route('/permissions/request', methods=['POST'])
@login_required
def request_access():
    app_id = request.form.get('app_id')
    reason = request.form.get('reason')
    
    if not app_id or not reason:
        flash('请填写完整的申请信息', 'error')
        return redirect(url_for('permissions.index'))
    
    # 检查是否已经有待处理的申请
    existing_request = AppRequest.query.filter_by(
        user_id=current_user.id,
        app_id=app_id,
        status='pending'
    ).first()
    
    if existing_request:
        flash('您已经提交过申请，请等待审核', 'warning')
        return redirect(url_for('permissions.index'))
    
    # 创建新的申请
    new_request = AppRequest(
        user_id=current_user.id,
        app_id=app_id,
        reason=reason,
        status='pending'
    )
    
    db.session.add(new_request)
    db.session.commit()
    
    flash('申请已提交，请等待审核', 'success')
    return redirect(url_for('permissions.index')) 