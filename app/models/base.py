from app.extensions import get_db
from datetime import datetime
from bson import ObjectId

class BaseModel:
    """基础模型类，包含所有模型共用的字段和方法"""
    
    @classmethod
    def collection(cls):
        """获取集合"""
        return get_db()[cls.collection_name]
    
    @classmethod
    def get_by_id(cls, id):
        """通过ID获取对象"""
        if isinstance(id, str):
            id = ObjectId(id)
        data = cls.collection().find_one({'_id': id})
        return cls.from_dict(data) if data else None
    
    def save(self):
        """保存对象到数据库"""
        if hasattr(self, '_id') and self._id:
            # 更新现有文档
            data = self.to_dict()
            self.collection().update_one(
                {'_id': self._id},
                {'$set': data}
            )
        else:
            # 插入新文档，不包含_id字段
            data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
            result = self.collection().insert_one(data)
            self._id = result.inserted_id
        return self
    
    def delete(self):
        """从数据库删除对象"""
        if hasattr(self, '_id') and self._id:
            self.collection().delete_one({'_id': self._id})
    
    def to_dict(self):
        """将对象转换为字典"""
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        if hasattr(self, '_id') and self._id:
            data['_id'] = self._id
        return data
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建对象"""
        if data is None:
            return None
        instance = cls()
        for k, v in data.items():
            if k != '_id':
                setattr(instance, k, v)
        if '_id' in data:
            instance._id = data['_id']
        return instance 