from app.models import BaseModel
from datetime import datetime
from bson import ObjectId

class Application(BaseModel):
    """应用模型，表示系统中注册的外部应用"""
    collection_name = 'applications'
    
    def __init__(self, name, app_id, client_id, client_secret, redirect_uri, is_active=True, description=None):
        self.name = name
        self.app_id = app_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.is_active = is_active
        self.description = description
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def find_by_app_id(cls, app_id):
        """通过app_id查找应用"""
        data = cls.collection().find_one({'app_id': app_id})
        return cls.from_dict(data) if data else None
    
    @classmethod
    def find_by_client_id(cls, client_id):
        """通过client_id查找应用"""
        data = cls.collection().find_one({'client_id': client_id})
        return cls.from_dict(data) if data else None
    
    @classmethod
    def get_all_active(cls):
        """获取所有活跃的应用"""
        data = cls.collection().find({'is_active': True})
        return [cls.from_dict(item) for item in data]

class UserApplication(BaseModel):
    """用户应用关联模型"""
    collection_name = 'user_applications'
    
    def __init__(self, user_id, app_id, access_token=None, refresh_token=None, expires_at=None):
        self.user_id = user_id
        self.app_id = app_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def find_by_user_and_app(cls, user_id, app_id):
        """通过用户ID和应用ID查找关联"""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        data = cls.collection().find_one({
            'user_id': user_id,
            'app_id': app_id
        })
        return cls.from_dict(data) if data else None
    
    def update_tokens(self, access_token, refresh_token, expires_at):
        """更新令牌信息"""
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at
        self.updated_at = datetime.utcnow()
        self.save()

class ApplicationRequest(BaseModel):
    """应用请求模型"""
    collection_name = 'application_requests'
    
    def __init__(self, user_id, app_id, reason=None, status='pending'):
        self.user_id = user_id
        self.app_id = app_id
        self.reason = reason
        self.status = status
        self.processed_at = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def find_by_user_and_app(cls, user_id, app_id):
        """通过用户ID和应用ID查找请求"""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        data = cls.collection().find_one({
            'user_id': user_id,
            'app_id': app_id
        })
        return cls.from_dict(data) if data else None
    
    def process(self, status):
        """处理请求"""
        self.status = status
        self.processed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.save() 