from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """要求用户具有管理员权限的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('您需要管理员权限才能访问此页面', 'error')
            return redirect(url_for('user.profile'))
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission):
    """要求用户具有特定权限的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.has_permission(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator 