from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .base import BaseModel
from bson import ObjectId

class User(UserMixin, BaseModel):
    """用户模型"""
    collection_name = 'users'
    
    def __init__(self, username=None, password=None, email=None, phone=None, is_admin=False):
        self.username = username
        self.email = email
        self.phone = phone
        self.is_admin = is_admin
        self.is_active = True  # 添加 is_active 字段，默认为 True
        self.created_at = datetime.utcnow().replace(tzinfo=None)
        self.updated_at = self.created_at
        if password:
            self.set_password(password)
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return getattr(self, '_is_active', True)
    
    @is_active.setter
    def is_active(self, value):
        self._is_active = bool(value)
    
    @property
    def is_anonymous(self):
        return False
    
    @property
    def id(self):
        """获取用户ID"""
        return str(self._id) if hasattr(self, '_id') else None
    
    def get_id(self):
        return str(self._id) if hasattr(self, '_id') else None
    
    @classmethod
    def find_by_username(cls, username):
        """通过用户名查找用户"""
        data = cls.collection().find_one({'username': username})
        return cls.from_dict(data) if data else None
    
    @classmethod
    def find_by_email(cls, email):
        """通过邮箱查找用户"""
        data = cls.collection().find_one({'email': email})
        return cls.from_dict(data) if data else None
    
    @classmethod
    def find_by_phone(cls, phone):
        """通过手机号查找用户"""
        data = cls.collection().find_one({'phone': phone})
        return cls.from_dict(data) if data else None
    
    @classmethod
    def find_by_id(cls, user_id):
        """通过ID查找用户"""
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except:
                return None
        data = cls.collection().find_one({'_id': user_id})
        return cls.from_dict(data)
    
    @classmethod
    def create_user(cls, username, email, password, phone=None, is_admin=False, role='user'):
        """创建新用户"""
        # 检查用户名是否已存在
        if cls.find_by_username(username):
            return None, '用户名已存在'
        
        # 检查邮箱是否已存在
        if cls.find_by_email(email):
            return None, '邮箱已被注册'
        
        # 检查手机号是否已存在
        if phone and cls.find_by_phone(phone):
            return None, '手机号已被注册'
        
        # 创建新用户
        user = cls(
            username=username,
            email=email,
            password=password,
            phone=phone,
            is_admin=is_admin
        )
        user.permissions = [role]  # 将role作为权限添加
        
        try:
            user.save()
            return user, None
        except Exception as e:
            return None, str(e)
    
    def update_profile(self, phone=None):
        """更新用户资料"""
        if phone:
            # 检查手机号是否已被其他用户使用
            existing_user = User.find_by_phone(phone)
            if existing_user and existing_user._id != self._id:
                return False, '手机号已被其他用户使用'
            self.phone = phone
        
        self.updated_at = datetime.utcnow().replace(tzinfo=None)
        self.save()
        return True, None
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.utcnow().replace(tzinfo=None)
        self.save()
        
    def has_permission(self, permission):
        """检查用户是否有指定权限"""
        return hasattr(self, 'permissions') and permission in self.permissions
    
    def add_permission(self, permission):
        """添加权限"""
        if not hasattr(self, 'permissions'):
            self.permissions = []
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.save()
    
    def remove_permission(self, permission):
        """移除权限"""
        if hasattr(self, 'permissions') and permission in self.permissions:
            self.permissions.remove(permission)
            self.save()
    
    def save(self):
        """保存用户数据"""
        data = {
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'is_admin': self.is_admin,
            'is_active': getattr(self, '_is_active', True),
            'password_hash': getattr(self, 'password_hash', None),
            'permissions': getattr(self, 'permissions', ['user']),
            'created_at': getattr(self, 'created_at', datetime.utcnow().replace(tzinfo=None)),
            'updated_at': datetime.utcnow().replace(tzinfo=None),
            'last_login': getattr(self, 'last_login', None)
        }
        
        if hasattr(self, '_id') and self._id:
            self.collection().update_one(
                {'_id': self._id},
                {'$set': data}
            )
        else:
            result = self.collection().insert_one(data)
            self._id = result.inserted_id
    
    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        """将对象转换为字典"""
        return {
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'is_admin': self.is_admin,
            'is_active': getattr(self, '_is_active', True),
            'password_hash': getattr(self, 'password_hash', None),
            'permissions': getattr(self, 'permissions', ['user']),
            'created_at': getattr(self, 'created_at', None),
            'updated_at': getattr(self, 'updated_at', None),
            'last_login': getattr(self, 'last_login', None)
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        if data is None:
            return None
        # 将 is_active 转换为 _is_active
        if 'is_active' in data:
            data['_is_active'] = data.pop('is_active')
        return super().from_dict(data) 