from app.models.user import User
from app.extensions import db
from app.models.application import Application, UserApplication, ApplicationRequest
from datetime import datetime

class AdminService:
    """管理员服务，处理管理员相关业务逻辑"""
    
    @staticmethod
    def get_users_list():
        """获取用户列表"""
        return User.query.all()
    
    @staticmethod
    def create_user(username, email, phone=None, role='user'):
        """创建新用户
        
        Args:
            username: 用户名
            email: 邮箱
            phone: 手机号，可选
            role: 角色，默认为user
            
        Returns:
            tuple: (user, error_message)
        """
        # 检查用户名是否已存在
        existing_user = User.find_by_username(username)
        if existing_user:
            return None, '用户名已存在'
        
        # 检查邮箱是否已存在
        existing_email = User.find_by_email(email)
        if existing_email:
            return None, '邮箱已被使用'
        
        # 检查手机号是否已存在
        if phone:
            existing_phone = User.find_by_phone(phone)
            if existing_phone:
                return None, '手机号已被使用'
        
        # 创建默认密码：用户名+123
        password = username + '123'
        
        # 创建用户
        user = User.create_user(username, email, password, phone, role)
        if not user:
            return None, '用户创建失败，请稍后重试'
        
        return user, None
    
    @staticmethod
    def update_user(user_id, **kwargs):
        """更新用户信息
        
        Args:
            user_id: 用户ID
            **kwargs: 要更新的字段和值
            
        Returns:
            tuple: (success, message)
        """
        user = User.find_by_id(user_id)
        if not user:
            return False, '用户不存在'
        
        try:
            # 更新密码
            if 'password' in kwargs and kwargs['password']:
                user.set_password(kwargs['password'])
                
            # 更新其他字段
            for key, value in kwargs.items():
                if key != 'password' and hasattr(user, key):
                    setattr(user, key, value)
                    
            db.session.commit()
            return True, '用户更新成功'
        except Exception as e:
            db.session.rollback()
            return False, f'更新失败: {str(e)}'
    
    @staticmethod
    def delete_user(user_id, current_user_id):
        """删除用户
        
        Args:
            user_id: 要删除的用户ID
            current_user_id: 当前管理员ID
            
        Returns:
            tuple: (success, message)
        """
        # 不能删除自己
        if int(user_id) == int(current_user_id):
            return False, '不能删除当前登录的用户'
        
        user = User.find_by_id(user_id)
        if not user:
            return False, '用户不存在'
        
        try:
            db.session.delete(user)
            db.session.commit()
            return True, '用户删除成功'
        except Exception as e:
            db.session.rollback()
            return False, f'删除失败: {str(e)}'
    
    @staticmethod
    def get_system_info():
        """获取系统信息"""
        # 获取用户数量
        user_count = User.query.count()
        
        # 计算系统运行时间（示例）
        import random
        uptime_str = f"{random.randint(1, 30)}天 {random.randint(0, 23)}小时"
        
        system_info = {
            'version': 'v1.0.0',  # 系统版本号
            'uptime': uptime_str,  # 运行时间
            'cpu_usage': random.randint(20, 80),  # CPU使用率（示例数据）
            'memory_usage': random.randint(30, 90)  # 内存使用率（示例数据）
        }
        
        return {
            'user_count': user_count,
            'system_info': system_info
        }
    
    @staticmethod
    def handle_app_request(request_id, action):
        """处理应用请求
        
        Args:
            request_id: 请求ID
            action: 操作，approve或reject
            
        Returns:
            tuple: (success, message)
        """
        app_request = ApplicationRequest.get_by_id(request_id)
        if not app_request:
            return False, '申请不存在'
        
        if app_request.status != 'pending':
            return False, '该申请已被处理'
        
        try:
            if action == 'approve':
                # 授予用户访问权限
                UserApplication.grant_access(app_request.user_id, app_request.app_id)
                app_request.status = 'approved'
                app_request.processed_at = datetime.utcnow()
                db.session.commit()
                return True, '申请已批准'
            elif action == 'reject':
                app_request.status = 'rejected'
                app_request.processed_at = datetime.utcnow()
                db.session.commit()
                return True, '申请已拒绝'
            else:
                return False, '不支持的操作'
        except Exception as e:
            db.session.rollback()
            return False, f'处理失败: {str(e)}' 