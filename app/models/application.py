from app.models import BaseModel
from datetime import datetime
from bson import ObjectId

class Application(BaseModel):
    """应用模型，用于OAuth2认证"""
    collection_name = 'oauth_applications'
    
    def __init__(self, name, description, client_id, client_secret, redirect_uri, is_active=True):
        self.name = name
        self.description = description
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.is_active = is_active
        self.created_at = datetime.utcnow().replace(tzinfo=None)
        self.updated_at = datetime.utcnow().replace(tzinfo=None)
    
    @property
    def id(self):
        """获取应用ID（字符串格式）"""
        return str(self._id) if hasattr(self, '_id') and self._id else None
    
    @classmethod
    def find_by_app_id(cls, app_id):
        """通过app_id查找应用"""
        # 由于我们没有app_id字段，这个方法不再需要
        # 实际上我们应该使用find_by_id方法，该方法查找_id字段
        return cls.find_by_id(app_id)
    
    @classmethod
    def find_by_client_id(cls, client_id):
        """通过客户端ID查找应用"""
        data = cls.collection().find_one({'client_id': client_id})
        if not data:
            return None
        
        return cls(
            name=data.get('name'),
            description=data.get('description'),
            client_id=data.get('client_id'),
            client_secret=data.get('client_secret'),
            redirect_uri=data.get('redirect_uri'),
            is_active=data.get('is_active', True)
        )
    
    @classmethod
    def find_by_id(cls, id):
        """通过ID查找应用"""
        if isinstance(id, str):
            try:
                id = ObjectId(id)
            except:
                return None
            
        data = cls.collection().find_one({'_id': id})
        if not data:
            return None
        
        app = cls(
            name=data.get('name'),
            description=data.get('description'),
            client_id=data.get('client_id'),
            client_secret=data.get('client_secret'),
            redirect_uri=data.get('redirect_uri'),
            is_active=data.get('is_active', True)
        )
        app._id = data.get('_id')
        return app
    
    def to_dict(self):
        """转换为字典"""
        data = {
            'name': self.name,
            'description': self.description,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        if hasattr(self, '_id') and self._id:
            data['_id'] = self._id
        return data
    
    @classmethod
    def get_all_active(cls):
        """获取所有活跃的应用"""
        apps = []
        for app_data in cls.collection().find({'is_active': True}):
            app = cls(
                name=app_data.get('name'),
                description=app_data.get('description'),
                client_id=app_data.get('client_id'),
                client_secret=app_data.get('client_secret'),
                redirect_uri=app_data.get('redirect_uri'),
                is_active=app_data.get('is_active', True)
            )
            app._id = app_data.get('_id')
            apps.append(app)
        return apps

    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        if not data:
            return None
        
        app = cls(
            name=data.get('name'),
            description=data.get('description'),
            client_id=data.get('client_id'),
            client_secret=data.get('client_secret'),
            redirect_uri=data.get('redirect_uri'),
            is_active=data.get('is_active', True)
        )
        if '_id' in data:
            app._id = data['_id']
        if 'created_at' in data:
            app.created_at = data['created_at']
        if 'updated_at' in data:
            app.updated_at = data['updated_at']
        return app

class UserApplication(BaseModel):
    """用户应用关联模型，表示用户对应用的授权"""
    collection_name = 'oauth_user_applications'
    
    def __init__(self, user_id, app_id, scope=None, created_at=None):
        self.user_id = user_id
        self.app_id = app_id
        self.scope = scope or []
        self.created_at = created_at or datetime.utcnow().replace(tzinfo=None)
    
    @classmethod
    def find_by_user_and_app(cls, user_id, app_id):
        """通过用户ID和应用ID查找关联"""
        data = cls.collection().find_one({
            'user_id': user_id,
            'app_id': app_id
        })
        return cls.from_dict(data) if data else None
    
    def to_dict(self):
        """转换为字典"""
        data = {
            'user_id': self.user_id,
            'app_id': self.app_id,
            'scope': self.scope,
            'created_at': self.created_at
        }
        if hasattr(self, '_id') and self._id:
            data['_id'] = self._id
        return data
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        if not data:
            return None
            
        user_app = cls(
            user_id=data.get('user_id'),
            app_id=data.get('app_id'),
            scope=data.get('scope'),
            created_at=data.get('created_at')
        )
        if '_id' in data:
            user_app._id = data['_id']
        return user_app

class ApplicationRequest(BaseModel):
    """应用请求模型，表示用户对应用的访问请求"""
    collection_name = 'oauth_application_requests'
    
    def __init__(self, user_id, app_id, status='pending', created_at=None):
        self.user_id = user_id
        self.app_id = app_id
        self.status = status  # pending, approved, rejected
        self.created_at = created_at or datetime.utcnow().replace(tzinfo=None)
        self.updated_at = datetime.utcnow().replace(tzinfo=None)
    
    @property
    def id(self):
        """获取申请ID（字符串格式）"""
        return str(self._id) if hasattr(self, '_id') and self._id else None
    
    @classmethod
    def find_by_id(cls, id):
        """通过ID查找申请"""
        if isinstance(id, str):
            try:
                id = ObjectId(id)
            except:
                return None
            
        data = cls.collection().find_one({'_id': id})
        if not data:
            return None
        
        request = cls.from_dict(data)
        if request:
            request._id = data.get('_id')
        return request
    
    @classmethod
    def find_pending_requests(cls):
        """获取所有待处理的申请"""
        requests = []
        for data in cls.collection().find({'status': 'pending'}).sort('created_at', -1):
            request = cls.from_dict(data)
            if request:
                requests.append(request)
        return requests
    
    @classmethod
    def find_by_user_and_app(cls, user_id, app_id):
        """通过用户ID和应用ID查找申请"""
        data = cls.collection().find_one({
            'user_id': user_id,
            'app_id': app_id,
            'status': 'pending'
        })
        return cls.from_dict(data) if data else None
    
    def to_dict(self):
        """转换为字典"""
        data = {
            'user_id': self.user_id,
            'app_id': self.app_id,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        if hasattr(self, '_id') and self._id:
            data['_id'] = self._id
        if hasattr(self, 'processed_at'):
            data['processed_at'] = self.processed_at
        if hasattr(self, 'processed_by'):
            data['processed_by'] = self.processed_by
        if hasattr(self, 'reject_reason'):
            data['reject_reason'] = self.reject_reason
        return data
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        if not data:
            return None
            
        request = cls(
            user_id=data.get('user_id'),
            app_id=data.get('app_id'),
            status=data.get('status', 'pending'),
            created_at=data.get('created_at')
        )
        
        if '_id' in data:
            request._id = data['_id']
        if 'processed_at' in data:
            request.processed_at = data['processed_at']
        if 'processed_by' in data:
            request.processed_by = data['processed_by']
        if 'reject_reason' in data:
            request.reject_reason = data['reject_reason']
        if 'updated_at' in data:
            request.updated_at = data['updated_at']
            
        return request 