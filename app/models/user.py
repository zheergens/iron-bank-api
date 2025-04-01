from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import BaseModel
from datetime import datetime
from bson import ObjectId

class User(UserMixin, BaseModel):
    """用户模型"""
    collection_name = 'users'
    
    def __init__(self, username, email, password, phone=None, is_active=True, is_admin=False, permissions=None):
        self.username = username
        self.email = email
        self.password_hash = None
        self.phone = phone
        self._is_active = is_active
        self._is_admin = is_admin
        self.permissions = permissions or []
        self.last_login = None
        self.created_at = datetime.utcnow().replace(tzinfo=None)
        self.updated_at = datetime.utcnow().replace(tzinfo=None)
        if password:
            self.set_password(password)
    
    def get_id(self):
        """获取用户ID（字符串格式）"""
        return str(self._id) if hasattr(self, '_id') and self._id else None
    
    @property
    def id(self):
        return self.get_id()
    
    @property
    def password(self):
        raise AttributeError('密码不可读')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    @property
    def is_active(self):
        """是否激活"""
        return self._is_active
    
    @is_active.setter
    def is_active(self, value):
        """设置激活状态"""
        self._is_active = bool(value)
    
    @property
    def is_admin(self):
        """是否为管理员"""
        return self._is_admin
    
    @is_admin.setter
    def is_admin(self, value):
        """设置管理员状态"""
        self._is_admin = bool(value)
    
    def to_dict(self):
        data = {
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'permissions': self.permissions,
            'last_login': self.last_login,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'password_hash': self.password_hash
        }
        if hasattr(self, '_id') and self._id:
            data['_id'] = self._id
        return data
    
    @classmethod
    def from_dict(cls, data):
        if data is None:
            return None
            
        user = cls(
            username=data.get('username'),
            email=data.get('email'),
            password=None,
            phone=data.get('phone'),
            is_active=data.get('is_active', True),
            is_admin=data.get('is_admin', False),
            permissions=data.get('permissions', [])
        )
        if '_id' in data:
            user._id = data['_id']
        user.password_hash = data.get('password_hash')
        user.last_login = data.get('last_login')
        user.created_at = data.get('created_at')
        user.updated_at = data.get('updated_at')
        return user
    
    @classmethod
    def find_by_username(cls, username):
        """通过用户名查找用户"""
        data = cls.collection().find_one({'username': username})
        return cls.from_dict(data)
    
    @classmethod
    def find_by_email(cls, email):
        """通过邮箱查找用户"""
        data = cls.collection().find_one({'email': email})
        return cls.from_dict(data)
    
    @classmethod
    def find_by_phone(cls, phone):
        """通过手机号查找用户"""
        data = cls.collection().find_one({'phone': phone})
        return cls.from_dict(data)
    
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
            is_admin=is_admin,
            permissions=[role]  # 将role作为权限添加
        )
        
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
        return permission in self.permissions
    
    def add_permission(self, permission):
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.save()
    
    def remove_permission(self, permission):
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.save()
    
    def save(self):
        data = self.to_dict()
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