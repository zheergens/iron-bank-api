from datetime import datetime
from bson import ObjectId
from app.extensions import get_db

class Menu:
    """菜单模型"""
    collection_name = 'menus'
    
    def __init__(self, name, path, icon=None, parent_id=None, app_id=None, sort_order=0, 
                 is_active=True, created_at=None, updated_at=None, _id=None):
        self._id = _id if _id else ObjectId()
        self.name = name
        self.path = path
        self.icon = icon
        self.parent_id = parent_id
        self.app_id = app_id
        self.sort_order = sort_order
        self.is_active = is_active
        self.created_at = created_at if created_at else datetime.utcnow()
        self.updated_at = updated_at if updated_at else datetime.utcnow()
    
    @classmethod
    def collection(cls):
        """获取数据库集合"""
        db = get_db()
        return db[cls.collection_name]
    
    def save(self):
        """保存菜单"""
        self.updated_at = datetime.utcnow()
        if not self._id:
            self._id = ObjectId()
            self.created_at = self.updated_at
        
        data = {
            'name': self.name,
            'path': self.path,
            'icon': self.icon,
            'parent_id': self.parent_id,
            'app_id': self.app_id,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        self.collection().update_one(
            {'_id': self._id},
            {'$set': data},
            upsert=True
        )
        return self
    
    def delete(self):
        """删除菜单"""
        self.collection().delete_one({'_id': self._id})
    
    @classmethod
    def find_by_id(cls, menu_id):
        """根据ID查找菜单"""
        if isinstance(menu_id, str):
            menu_id = ObjectId(menu_id)
        data = cls.collection().find_one({'_id': menu_id})
        if data:
            return cls(**data)
        return None
    
    @classmethod
    def find_by_app_id(cls, app_id):
        """获取应用的所有菜单"""
        menus = []
        cursor = cls.collection().find({'app_id': app_id}).sort('sort_order', 1)
        for data in cursor:
            menus.append(cls(**data))
        return menus
    
    @classmethod
    def build_tree(cls, menus):
        """构建菜单树"""
        menu_map = {}
        root_menus = []
        
        # 先按 sort_order 排序
        sorted_menus = sorted(menus, key=lambda x: x.sort_order)
        
        # 创建id到菜单的映射
        for menu in sorted_menus:
            menu_data = {
                'id': str(menu._id),
                'name': menu.name,
                'path': menu.path,
                'icon': menu.icon,
                'parent_id': str(menu.parent_id) if menu.parent_id else None,
                'sort_order': menu.sort_order,
                'children': []
            }
            menu_map[str(menu._id)] = menu_data
        
        # 构建树结构
        for menu in sorted_menus:
            menu_data = menu_map[str(menu._id)]
            if menu.parent_id:
                parent_id = str(menu.parent_id)
                if parent_id in menu_map:
                    menu_map[parent_id]['children'].append(menu_data)
            else:
                root_menus.append(menu_data)
        
        return root_menus 