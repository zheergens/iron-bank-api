from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from app.models.user import User
from .forms import LoginForm
from datetime import datetime
from app.services.auth_service import AuthService

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user.profile'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data
        
        # 使用AuthService进行登录
        user, error = AuthService.login(username, password, remember)
        
        if user:
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('user.profile')
            return redirect(next)
        else:
            flash(error, 'error')
    
    return render_template('auth/login.html', form=form, current_year=datetime.now().year)

@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    # 使用AuthService进行登出
    _, message = AuthService.logout()
    flash(message, 'success')
    return redirect(url_for('auth.login')) 