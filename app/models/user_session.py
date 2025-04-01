from app.models import BaseModel
from datetime import datetime, timedelta
from bson import ObjectId

class UserSession(BaseModel):
    """用户会话模型"""
    collection_name = 'user_sessions'
    
    def __init__(self, user_id, token, device_info=None):
        self.user_id = user_id
        self.token = token
        self.device_info = device_info or {}
        self.created_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(days=1)  # 默认1天过期
    
    @classmethod
    def find_by_token(cls, token):
        """通过token查找会话"""
        data = cls.collection().find_one({'token': token})
        return cls.from_dict(data) if data else None
    
    @classmethod
    def find_by_user_id(cls, user_id):
        """通过用户ID查找所有会话"""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        data = cls.collection().find({'user_id': user_id})
        return [cls.from_dict(item) for item in data]
    
    def is_expired(self):
        """检查会话是否过期"""
        return datetime.utcnow() > self.expires_at
    
    def extend_expiry(self, days=1):
        """延长会话过期时间"""
        self.expires_at = datetime.utcnow() + timedelta(days=days)
        self.save() 