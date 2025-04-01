from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from app.models.user import User, db
from app.models.application import ApplicationRequest, UserApplication
from functools import wraps
import datetime
import random
from flask_wtf import FlaskForm

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('您需要管理员权限才能访问此页面')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@login_required
@admin_required
def index():
    # 获取统计数据
    total_users = User.query.count()
    active_users_today = User.query.filter(
        User.last_login >= datetime.datetime.now().replace(hour=0, minute=0, second=0)
    ).count()
    pending_requests = ApplicationRequest.query.filter_by(status='pending').count()
    
    # 计算系统运行时间（示例：从应用启动时开始计算）
    if not hasattr(current_app, 'start_time'):
        current_app.start_time = datetime.datetime.now()
    uptime = datetime.datetime.now() - current_app.start_time
    uptime_str = f"{uptime.days}天 {uptime.seconds//3600}小时"
    
    stats = {
        'total_users': total_users,
        'active_users_today': active_users_today,
        'pending_requests': pending_requests,
        'uptime': uptime_str
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
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    current_app.logger.info("=== 进入新用户创建路由 ===")
    form = FlaskForm()
    
    if request.method == 'POST':
        try:
            if not form.validate():
                current_app.logger.warning("CSRF validation failed")
                flash('表单验证失败，请重试')
                return render_template('admin/users/new.html', form=form)
                
            # 记录请求数据
            current_app.logger.info(f"Form data: {request.form.to_dict()}")
            
            username = request.form.get('username')
            email = request.form.get('email')
            phone = request.form.get('phone')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            role = request.form.get('role', 'user')
            
            current_app.logger.info(f"Parsed data: username={username}, email={email}, phone={phone}, role={role}")
            
            # 验证必填字段
            if not username or not email or not password or not confirm_password:
                current_app.logger.warning("Missing required fields")
                flash('请填写所有必填字段')
                return render_template('admin/users/new.html', form=form)
            
            # 验证密码长度
            if len(password) < 6:
                current_app.logger.warning("Password too short")
                flash('密码长度至少为6个字符')
                return render_template('admin/users/new.html', form=form)
            
            # 验证两次密码是否一致
            if password != confirm_password:
                current_app.logger.warning("Passwords do not match")
                flash('两次输入的密码不一致')
                return render_template('admin/users/new.html', form=form)
            
            # 检查用户名是否已存在
            existing_user = User.find_by_username(username)
            if existing_user:
                current_app.logger.warning(f"Username already exists: {username}")
                flash('用户名已存在')
                return render_template('admin/users/new.html', form=form)
            
            # 检查邮箱是否已存在
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                current_app.logger.warning(f"Email already exists: {email}")
                flash('邮箱已被使用')
                return render_template('admin/users/new.html', form=form)
            
            # 检查手机号是否已存在
            if phone:
                existing_phone = User.find_by_phone(phone)
                if existing_phone:
                    current_app.logger.warning(f"Phone already exists: {phone}")
                    flash('手机号已被使用')
                    return render_template('admin/users/new.html', form=form)
            
            # 创建新用户
            current_app.logger.info("Attempting to create user...")
            user = User.create_user(username, email, password, phone, role)
            
            if user:
                current_app.logger.info(f"User created successfully: {username}")
                flash('用户创建成功')
                return redirect(url_for('admin.users'))
            else:
                current_app.logger.error("User creation failed")
                flash('用户创建失败，请稍后重试')
                return render_template('admin/users/new.html', form=form)
                
        except Exception as e:
            current_app.logger.error(f"Error in user creation: {str(e)}", exc_info=True)
            flash('创建用户时发生错误，请稍后重试')
            return render_template('admin/users/new.html', form=form)
    
    current_app.logger.info("Rendering new user form")
    return render_template('admin/users/new.html', form=form)

@admin.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.find_by_id(user_id)
    if not user:
        flash('用户不存在')
        return redirect(url_for('admin.users'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        role = request.form.get('role')
        
        user.email = email
        user.role = role
        
        password = request.form.get('password')
        if password:
            user.set_password(password)
        
        db.session.commit()
        flash('用户更新成功')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', user=user)

@admin.route('/users/<user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.find_by_id(user_id)
    if not user:
        flash('用户不存在')
        return redirect(url_for('admin.users'))
    
    # 防止删除自己
    if user.id == current_user.id:
        flash('不能删除当前登录的用户')
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('用户删除成功')
    return redirect(url_for('admin.users'))

@admin.route('/system_info')
@login_required
@admin_required
def system_info():
    # 获取用户数量
    user_count = User.query.count()
    
    # 获取系统信息
    if not hasattr(current_app, 'start_time'):
        current_app.start_time = datetime.datetime.now()
    uptime = datetime.datetime.now() - current_app.start_time
    uptime_str = f"{uptime.days}天 {uptime.seconds//3600}小时"
    
    system_info = {
        'version': 'v1.0.0',  # 系统版本号
        'uptime': uptime_str,  # 运行时间
        'cpu_usage': random.randint(20, 80),  # CPU使用率（示例数据）
        'memory_usage': random.randint(30, 90)  # 内存使用率（示例数据）
    }
    
    # 获取注册的应用
    registered_apps = []
    for app_id, app_data in current_app.config['REGISTERED_APPS'].items():
        registered_apps.append({
            'id': app_id,
            'name': app_data['name'],
            'client_id': app_data['client_id'],
            'redirect_uri': app_data['redirect_uri'],
            'is_active': True,
            'created_at': datetime.datetime.now() - datetime.timedelta(days=len(registered_apps))
        })
    
    return render_template('admin/system_info.html', 
                         user_count=user_count,
                         system_info=system_info,
                         registered_apps=registered_apps)

@admin.route('/apps/<app_id>/users')
@login_required
@admin_required
def manage_app_users(app_id):
    # 获取应用信息
    app_data = current_app.config['REGISTERED_APPS'].get(app_id)
    if not app_data:
        flash('应用不存在')
        return redirect(url_for('admin.system_info'))
    
    app = {
        'id': app_id,
        'name': app_data['name'],
        'client_id': app_data['client_id'],
        'redirect_uri': app_data['redirect_uri'],
        'is_active': True
    }
    
    # 获取所有用户，并标记是否已授权访问此应用
    users = User.query.all()
    for user in users:
        # 使用UserApplication模型检查用户是否已授权
        user.is_authorized = UserApplication.user_has_access(user.id, app_id)
    
    return render_template('admin/manage_app_users.html', app=app, users=users)

@admin.route('/apps/<app_id>/users/<user_id>/add', methods=['POST'])
@login_required
@admin_required
def add_app_user(app_id, user_id):
    # 授权用户访问应用
    if UserApplication.grant_access(user_id, app_id):
        flash('用户授权成功')
    else:
        flash('用户已经拥有此应用的访问权限')
    return redirect(url_for('admin.manage_app_users', app_id=app_id))

@admin.route('/apps/<app_id>/users/<user_id>/remove', methods=['POST'])
@login_required
@admin_required
def remove_app_user(app_id, user_id):
    # 移除用户访问应用的授权
    if UserApplication.revoke_access(user_id, app_id):
        flash('用户授权已移除')
    else:
        flash('用户未拥有此应用的访问权限')
    return redirect(url_for('admin.manage_app_users', app_id=app_id))

@admin.route('/apps/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_app():
    # 在此处实现添加新应用的逻辑
    flash('新应用添加功能正在开发中')
    return redirect(url_for('admin.system_info'))

@admin.route('/apps/<app_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_app(app_id):
    # 在此处实现编辑应用的逻辑
    flash('应用编辑功能正在开发中')
    return redirect(url_for('admin.system_info'))

@admin.route('/apps/<app_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_app(app_id):
    # 在此处实现删除应用的逻辑
    flash('应用删除功能正在开发中')
    return redirect(url_for('admin.system_info'))

@admin.route('/app_requests')
@login_required
@admin_required
def app_requests():
    # 获取所有待处理的申请
    pending_requests = ApplicationRequest.query.filter_by(status='pending').order_by(ApplicationRequest.created_at.desc()).all()
    
    # 为每个申请添加应用名称
    for request in pending_requests:
        app_config = current_app.config['REGISTERED_APPS'].get(request.app_id)
        request.app_name = app_config['name'] if app_config else '未知应用'
    
    # 获取已审批的历史记录
    history_requests = ApplicationRequest.query.filter(
        ApplicationRequest.status.in_(['approved', 'rejected'])
    ).order_by(ApplicationRequest.approved_at.desc()).all()
    
    # 为历史记录添加应用名称
    for request in history_requests:
        app_config = current_app.config['REGISTERED_APPS'].get(request.app_id)
        request.app_name = app_config['name'] if app_config else '未知应用'
    
    return render_template('admin/app_requests.html', 
                           pending_requests=pending_requests, 
                           history_requests=history_requests)

@admin.route('/approve_request', methods=['POST'])
@login_required
@admin_required
def approve_request():
    request_id = request.form.get('request_id')
    comment = request.form.get('comment')
    
    app_request = ApplicationRequest.query.get(request_id)
    if not app_request:
        flash('申请不存在')
        return redirect(url_for('admin.app_requests'))
    
    if app_request.status != 'pending':
        flash('该申请已被处理')
        return redirect(url_for('admin.app_requests'))
    
    # 批准申请并授予权限
    app_request.approve(current_user.id, comment)
    UserApplication.grant_access(app_request.user_id, app_request.app_id)
    
    flash('申请已批准')
    return redirect(url_for('admin.app_requests'))

@admin.route('/reject_request', methods=['POST'])
@login_required
@admin_required
def reject_request():
    request_id = request.form.get('request_id')
    comment = request.form.get('comment')
    
    app_request = ApplicationRequest.query.get(request_id)
    if not app_request:
        flash('申请不存在')
        return redirect(url_for('admin.app_requests'))
    
    if app_request.status != 'pending':
        flash('该申请已被处理')
        return redirect(url_for('admin.app_requests'))
    
    # 拒绝申请
    app_request.reject(current_user.id, comment)
    
    flash('申请已拒绝')
    return redirect(url_for('admin.app_requests')) 