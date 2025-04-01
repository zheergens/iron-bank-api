from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from flask_login import UserMixin
from app.models import db
from flask import current_app

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    phone = db.Column(db.String(11), unique=True, index=True, nullable=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        self.last_login = datetime.datetime.utcnow()
        db.session.commit()
    
    def update_profile(self, phone=None):
        """更新用户资料
        
        Args:
            phone: 新的手机号码，如果为 None 则不更新
            
        Returns:
            bool: 更新是否成功
        """
        try:
            if phone is not None:
                # 检查手机号是否已被其他用户使用
                existing_user = User.query.filter(User.id != self.id, User.phone == phone).first()
                if existing_user:
                    return False, '该手机号已被其他用户使用'
                self.phone = phone
            
            db.session.commit()
            return True, '个人资料更新成功'
        except Exception as e:
            db.session.rollback()
            return False, '更新失败，请稍后重试'
    
    @classmethod
    def create_user(cls, username, email, password, phone=None, role='user'):
        try:
            current_app.logger.info(f"=== 开始创建用户 ===")
            current_app.logger.info(f"参数: username={username}, email={email}, phone={phone}, role={role}")
            
            # 验证用户名
            if not username or len(username) < 2:
                current_app.logger.warning(f"无效的用户名: {username}")
                return None
                
            # 验证邮箱
            if not email or '@' not in email:
                current_app.logger.warning(f"无效的邮箱: {email}")
                return None
                
            # 验证手机号（如果提供）
            if phone:
                if not phone.isdigit() or len(phone) != 11:
                    current_app.logger.warning(f"无效的手机号: {phone}")
                    return None
            
            current_app.logger.info("验证通过，开始创建用户对象")
            # 创建用户对象
            user = cls(username=username, email=email, phone=phone, role=role)
            user.set_password(password)
            
            current_app.logger.info("开始保存到数据库")
            # 添加到数据库
            db.session.add(user)
            db.session.commit()
            
            current_app.logger.info(f"用户创建成功: {username}")
            return user
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建用户时发生数据库错误: {str(e)}", exc_info=True)
            return None
    
    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def find_by_phone(cls, phone):
        return cls.query.filter_by(phone=phone).first()
    
    @classmethod
    def find_by_id(cls, user_id):
        return cls.query.get(user_id)
    
    @classmethod
    def get_all_users(cls):
        return cls.query.all() 