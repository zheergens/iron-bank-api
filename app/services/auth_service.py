from app.models.user import User
from flask_login import login_user, logout_user
from datetime import datetime

class AuthService:
    """认证服务，处理用户认证相关业务逻辑"""
    
    @staticmethod
    def login(username, password, remember=False):
        """用户登录
        
        Args:
            username: 用户名或邮箱
            password: 密码
            remember: 是否记住用户
            
        Returns:
            tuple: (user, error_message)
        """
        # 先尝试用用户名查找
        user = User.find_by_username(username)
        if not user:
            # 如果用户名找不到，尝试用邮箱查找
            user = User.find_by_email(username)
            
        if not user:
            return None, '用户名或密码错误'
            
        # 检查密码哈希是否存在
        if not user.password_hash:
            return None, '账号异常，请联系管理员'
            
        # 检查密码是否正确
        try:
            if not user.check_password(password):
                return None, '用户名或密码错误'
        except Exception as e:
            return None, '账号异常，请联系管理员'
            
        # 检查用户是否被禁用
        if not user.is_active:
            return None, '账号已被禁用，请联系管理员'
        
        # 更新最后登录时间
        try:
            user.update_last_login()
        except Exception as e:
            # 登录时间更新失败不影响登录
            pass
        
        # 登录用户
        login_user(user, remember=remember)
        
        return user, None
    
    @staticmethod
    def logout():
        """用户登出"""
        logout_user()
        return True, '您已成功退出登录'
    
    @staticmethod
    def register(username, email, password, phone=None):
        """用户注册
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            phone: 手机号，可选
            
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
        
        # 创建用户
        user, error = User.create_user(username, email, password, phone)
        if error:
            return None, error
        
        return user, None 