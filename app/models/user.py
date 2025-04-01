from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import BaseModel
from datetime import datetime

class User(UserMixin, BaseModel):
    """用户模型"""
    __tablename__ = 'users'
    
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20), unique=True, nullable=True)
    role = db.Column(db.String(20), default='user')  # user, admin
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # 关系
    applications = db.relationship('UserApplication', back_populates='user', cascade='all, delete-orphan')
    app_requests = db.relationship('ApplicationRequest', back_populates='user', cascade='all, delete-orphan')
    
    @property
    def password(self):
        raise AttributeError('密码不可读')
        
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    @property
    def is_admin(self):
        """是否为管理员"""
        return self.role == 'admin'
    
    @classmethod
    def find_by_username(cls, username):
        """通过用户名查找用户"""
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def find_by_email(cls, email):
        """通过邮箱查找用户"""
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def find_by_phone(cls, phone):
        """通过手机号查找用户"""
        return cls.query.filter_by(phone=phone).first()
    
    @classmethod
    def find_by_id(cls, id):
        """通过ID查找用户"""
        return cls.query.get(id)
    
    @classmethod
    def create_user(cls, username, email, password, phone=None, role='user'):
        """创建新用户"""
        try:
            user = cls(
                username=username,
                email=email,
                phone=phone,
                role=role
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            return None
    
    def update_profile(self, **kwargs):
        """更新用户资料"""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            db.session.commit()
            return True, "更新成功"
        except Exception as e:
            db.session.rollback()
            return False, str(e)
            
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.utcnow()
        db.session.commit()
        
    def __repr__(self):
        return f'<User {self.username}>' 