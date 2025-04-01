from app.models.user import User
from app.extensions import db
from app.models.application import UserApplication, ApplicationRequest
from flask_login import current_user

class UserService:
    """用户服务，处理用户相关业务逻辑"""
    
    @staticmethod
    def update_password(user, old_password, new_password, confirm_password):
        """更新用户密码
        
        Args:
            user: 用户对象
            old_password: 旧密码
            new_password: 新密码
            confirm_password: 确认密码
            
        Returns:
            tuple: (success, message)
        """
        # 验证当前密码
        if not user.check_password(old_password):
            return False, '当前密码错误'
        
        # 验证新密码
        if new_password != confirm_password:
            return False, '新密码两次输入不一致'
        
        # 验证新密码长度
        if len(new_password) < 6:
            return False, '新密码长度至少为6个字符'
            
        # 验证新密码与旧密码不同
        if old_password == new_password:
            return False, '新密码不能与当前密码相同'
        
        try:
            user.set_password(new_password)
            db.session.commit()
            return True, '密码修改成功'
        except Exception as e:
            db.session.rollback()
            return False, '密码修改失败，请稍后重试'
    
    @staticmethod
    def update_profile(user, **kwargs):
        """更新用户资料
        
        Args:
            user: 用户对象
            **kwargs: 要更新的字段和值
            
        Returns:
            tuple: (success, message)
        """
        try:
            # 如果要更新手机号，需要验证是否已被使用
            if 'phone' in kwargs and kwargs['phone']:
                existing_user = User.query.filter(
                    User.id != user.id, 
                    User.phone == kwargs['phone']
                ).first()
                if existing_user:
                    return False, '该手机号已被其他用户使用'
            
            # 更新资料
            return user.update_profile(**kwargs)
        except Exception as e:
            return False, f'更新资料失败: {str(e)}'
    
    @staticmethod
    def request_app_access(user_id, app_id, reason=""):
        """申请应用访问权限
        
        Args:
            user_id: 用户ID
            app_id: 应用ID
            reason: 申请原因
            
        Returns:
            tuple: (success, message)
        """
        # 验证用户是否已有访问权限
        if UserApplication.user_has_access(user_id, app_id):
            return False, '您已经拥有此应用的访问权限'
        
        # 验证是否已申请过
        existing_request = ApplicationRequest.query.filter_by(
            user_id=user_id, 
            app_id=app_id,
            status='pending'
        ).first()
        
        if existing_request:
            return False, '您已经提交过此应用的访问权限申请，请等待审批'
        
        try:
            # 创建申请
            app_request = ApplicationRequest(
                user_id=user_id,
                app_id=app_id,
                reason=reason
            )
            db.session.add(app_request)
            db.session.commit()
            return True, '申请已提交，请等待管理员审批'
        except Exception as e:
            db.session.rollback()
            return False, f'申请提交失败: {str(e)}' 