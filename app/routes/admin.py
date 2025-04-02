from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.models.application import Application, ApplicationRequest
from app.decorators import admin_required
import datetime
import random
from flask_wtf import FlaskForm
from bson import ObjectId
import json
from app.models.menu import Menu

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
    """编辑用户"""
    try:
        user = User.find_by_id(user_id)
        if not user:
            flash('用户不存在')
            return redirect(url_for('admin.users'))
            
        form = FlaskForm()
        
        if request.method == 'POST' and form.validate():
            # 更新用户信息
            user.username = request.form.get('username')
            user.email = request.form.get('email')
            user.phone = request.form.get('phone')
            user.is_admin = request.form.get('role') == 'admin'
            
            # 如果提供了新密码，则更新密码
            new_password = request.form.get('password')
            if new_password:
                user.set_password(new_password)
            
            # 保存更改
            user.save()
            flash('用户信息更新成功')
            return redirect(url_for('admin.users'))
            
        return render_template('admin/edit_user.html', form=form, user=user)
        
    except Exception as e:
        current_app.logger.error(f"Error editing user: {str(e)}")
        flash('编辑用户时发生错误')
        return redirect(url_for('admin.users'))

@admin.route('/users/delete/<user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """删除用户（将用户状态设置为非活跃）"""
    user = User.find_by_id(user_id)
    if not user:
        flash('用户不存在', 'error')
        return redirect(url_for('admin.users'))
    
    if user.is_admin:
        flash('不能删除管理员用户', 'error')
        return redirect(url_for('admin.users'))
    
    # 将用户状态设置为非活跃
    user.is_active = False
    user.save()
    
    flash('用户已禁用', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/system_info')
@login_required
@admin_required
def system_info():
    """系统信息页面"""
    try:
        # 获取所有应用
        applications = Application.get_all_active()
        current_app.logger.info(f"Total applications in database: {len(applications)}")
        current_app.logger.info(f"Applications type: {type(applications)}")
        
        # 打印原始数据
        for app_data in Application.collection().find({'is_active': True}):
            current_app.logger.info(f"Raw app data: {app_data}")
        
        # 打印每个应用的信息用于调试
        for app in applications:
            current_app.logger.info(f"Application: {app.name}, ID: {app.id}, Client ID: {app.client_id}, Is Active: {app.is_active}")
            # 打印完整的应用对象属性
            current_app.logger.info(f"Full app attributes: {app.__dict__}")
            
        # 检查applications是否为None或空列表
        if applications is None:
            current_app.logger.error("applications is None!")
        elif len(applications) == 0:
            current_app.logger.error("applications is empty list!")
        else:
            current_app.logger.info(f"applications contains {len(applications)} items")
            
        # 打印模板变量
        template_vars = {'applications': applications}
        current_app.logger.info(f"Template variables: {template_vars}")
        
        return render_template('admin/system_info.html', **template_vars)
    except Exception as e:
        current_app.logger.error(f"Error in system_info: {str(e)}")
        flash('获取系统信息失败')
        return redirect(url_for('admin.index'))

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
    app_requests = ApplicationRequest.collection().find({'app_id': app_id, 'status': 'approved'})
    users = []
    for app_request in app_requests:
        user = User.find_by_id(app_request.get('user_id'))
        if user:
            users.append(user)
    
    return render_template('admin/app_users.html', app=app, users=users)

@admin.route('/apps/<app_id>/users/<user_id>/add', methods=['POST'])
@login_required
@admin_required
def add_app_user(app_id, user_id):
    # 创建新的应用请求并直接批准
    app_request = ApplicationRequest(
        user_id=user_id,
        app_id=app_id,
        status='approved'
    )
    app_request.processed_at = datetime.datetime.utcnow()
    app_request.processed_by = current_user.id
    app_request.save()
    flash('用户授权成功')
    return redirect(url_for('admin.manage_app_users', app_id=app_id))

@admin.route('/apps/<app_id>/users/<user_id>/remove', methods=['POST'])
@login_required
@admin_required
def remove_app_user(app_id, user_id):
    # 将用户的应用请求状态更新为rejected
    result = ApplicationRequest.collection().update_many(
        {'user_id': user_id, 'app_id': app_id, 'status': 'approved'},
        {'$set': {'status': 'rejected', 'processed_at': datetime.datetime.utcnow(), 'processed_by': current_user.id}}
    )
    if result.modified_count > 0:
        flash('用户授权已移除')
    return redirect(url_for('admin.manage_app_users', app_id=app_id))

@admin.route('/apps/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register_app():
    """注册新应用"""
    form = FlaskForm()
    
    if request.method == 'POST' and form.validate():
        name = request.form.get('name')
        description = request.form.get('description')
        redirect_uri = request.form.get('redirect_uri')
        
        try:
            # 生成随机的client_id和client_secret
            client_id = f"client_{random.randbytes(12).hex()}"
            client_secret = random.randbytes(24).hex()
            
            # 创建新应用
            app = Application(
                name=name,
                description=description,
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                is_active=True
            )
            app.save()
            
            flash(f'应用注册成功！请保存好以下信息：\nClient ID: {client_id}\nClient Secret: {client_secret}', 'success')
            return redirect(url_for('admin.system_info'))
        except Exception as e:
            current_app.logger.error(f"Error creating application: {str(e)}")
            flash('创建应用失败，请重试', 'error')
    
    return render_template('admin/register_app.html', form=form)

@admin.route('/apps/<app_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_app(app_id):
    """编辑应用"""
    try:
        current_app.logger.info(f"Editing app with ID: {app_id}")
        
        # 查找应用
        app = Application.find_by_id(app_id)
        current_app.logger.info(f"Found app: {app.__dict__ if app else None}")
        
        if not app:
            flash('应用不存在')
            return redirect(url_for('admin.system_info'))
            
        form = FlaskForm()
        
        if request.method == 'POST' and form.validate():
            # 更新应用信息
            app.name = request.form.get('name')
            app.description = request.form.get('description')
            app.redirect_uri = request.form.get('redirect_uri')
            app.is_active = request.form.get('is_active') == 'true'
            
            # 保存更改
            app.save()
            
            # 处理菜单数据
            menus_json = request.form.get('menus', '[]')
            menus = json.loads(menus_json)
            
            # 获取当前所有菜单的ID
            existing_menu_ids = set()
            for menu in Menu.find_by_app_id(str(app._id)):
                existing_menu_ids.add(str(menu._id))
            
            # 记录处理过的菜单ID
            processed_menu_ids = set()
            
            # 更新或插入菜单
            for menu_data in menus:
                menu_id = menu_data.get('id')
                if menu_id and not menu_id.startswith('temp_'):
                    # 更新现有菜单
                    menu = Menu.find_by_id(menu_id)
                    if menu:
                        menu.name = menu_data['name']
                        menu.path = menu_data['path']
                        menu.icon = menu_data.get('icon')
                        menu.parent_id = menu_data.get('parent_id')
                        menu.sort_order = menu_data.get('sort_order', 0)
                        menu.save()
                        processed_menu_ids.add(menu_id)
                        continue
                
                # 创建新菜单
                menu = Menu(
                    name=menu_data['name'],
                    path=menu_data['path'],
                    icon=menu_data.get('icon'),
                    parent_id=menu_data.get('parent_id'),
                    app_id=str(app._id),
                    sort_order=menu_data.get('sort_order', 0)
                )
                menu.save()
                processed_menu_ids.add(str(menu._id))
            
            # 删除未处理的菜单（已被移除的菜单）
            menus_to_delete = existing_menu_ids - processed_menu_ids
            for menu_id in menus_to_delete:
                menu = Menu.find_by_id(menu_id)
                if menu:
                    menu.delete()
            
            flash('应用信息更新成功')
            return redirect(url_for('admin.system_info'))
            
        # 获取当前菜单
        menus = Menu.find_by_app_id(str(app._id))
        # 将菜单对象转换为字典列表
        menu_list = []
        for menu in menus:
            menu_list.append({
                'id': str(menu._id),
                'name': menu.name,
                'path': menu.path,
                'icon': menu.icon,
                'parent_id': menu.parent_id,
                'sort_order': menu.sort_order
            })
        
        # 准备模板变量
        template_vars = {
            'form': form,
            'app': app,
            'menus': menu_list  # 传递扁平的菜单列表
        }
        current_app.logger.info(f"Template variables: {template_vars}")
        
        return render_template('admin/edit_app.html', **template_vars)
        
    except Exception as e:
        current_app.logger.error(f"Error editing app: {str(e)}")
        flash('编辑应用时发生错误')
        return redirect(url_for('admin.system_info'))

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
        ApplicationRequest.collection().delete_many({'app_id': app_id})
        
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

@admin.route('/apps/<app_id>/menus', methods=['GET'])
@login_required
@admin_required
def get_app_menus(app_id):
    """获取应用的菜单列表"""
    try:
        menus = Menu.find_by_app_id(app_id)
        menu_tree = Menu.build_tree(menus)
        return jsonify({
            'success': True,
            'data': menu_tree
        })
    except Exception as e:
        current_app.logger.error(f"Error getting menus: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取菜单失败'
        }), 500

@admin.route('/apps/<app_id>/menus', methods=['POST'])
@login_required
@admin_required
def add_app_menu(app_id):
    """添加应用菜单"""
    try:
        data = request.get_json()
        menu = Menu(
            name=data['name'],
            path=data['path'],
            icon=data.get('icon'),
            parent_id=data.get('parent_id'),
            app_id=app_id,
            sort_order=data.get('sort_order', 0)
        )
        menu.save()
        
        return jsonify({
            'success': True,
            'message': '添加菜单成功',
            'data': {
                'id': str(menu._id),
                'name': menu.name,
                'path': menu.path,
                'icon': menu.icon,
                'parent_id': menu.parent_id,
                'sort_order': menu.sort_order
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error adding menu: {str(e)}")
        return jsonify({
            'success': False,
            'message': '添加菜单失败'
        }), 500

@admin.route('/apps/<app_id>/menus/<menu_id>', methods=['PUT'])
@login_required
@admin_required
def update_app_menu(app_id, menu_id):
    """更新应用菜单"""
    try:
        menu = Menu.find_by_id(menu_id)
        if not menu or str(menu.app_id) != app_id:
            return jsonify({
                'success': False,
                'message': '菜单不存在'
            }), 404
        
        data = request.get_json()
        menu.name = data.get('name', menu.name)
        menu.path = data.get('path', menu.path)
        menu.icon = data.get('icon', menu.icon)
        menu.parent_id = data.get('parent_id', menu.parent_id)
        menu.sort_order = data.get('sort_order', menu.sort_order)
        menu.save()
        
        return jsonify({
            'success': True,
            'message': '更新菜单成功'
        })
    except Exception as e:
        current_app.logger.error(f"Error updating menu: {str(e)}")
        return jsonify({
            'success': False,
            'message': '更新菜单失败'
        }), 500

@admin.route('/apps/<app_id>/menus/<menu_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_app_menu(app_id, menu_id):
    """删除应用菜单"""
    try:
        menu = Menu.find_by_id(menu_id)
        if not menu or str(menu.app_id) != app_id:
            return jsonify({
                'success': False,
                'message': '菜单不存在'
            }), 404
        
        menu.delete()
        return jsonify({
            'success': True,
            'message': '删除菜单成功'
        })
    except Exception as e:
        current_app.logger.error(f"Error deleting menu: {str(e)}")
        return jsonify({
            'success': False,
            'message': '删除菜单失败'
        }), 500 