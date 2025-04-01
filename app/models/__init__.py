from app.extensions import db
from datetime import datetime

class BaseModel(db.Model):
    """基础模型类，包含所有模型共用的字段和方法"""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_by_id(cls, id):
        """通过ID获取对象"""
        return cls.query.get(id)
    
    def save(self):
        """保存对象到数据库"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """从数据库删除对象"""
        db.session.delete(self)
        db.session.commit()

def init_models():
    from .user import User
    from .application import Application, UserApplication, ApplicationRequest 