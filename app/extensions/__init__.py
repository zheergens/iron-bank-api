"""
扩展模块 - 集中管理Flask扩展的初始化
"""
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from pymongo import MongoClient

# 创建扩展实例
mongo_client = None
login_manager = LoginManager()
csrf = CSRFProtect()

def get_db():
    """获取数据库实例"""
    if mongo_client is None:
        raise RuntimeError('MongoDB client not initialized')
    return mongo_client.get_database()

def init_extensions(app):
    """初始化所有扩展"""
    # 配置登录管理器
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录后再访问此页面。'
    
    # 初始化MongoDB
    global mongo_client
    mongo_client = MongoClient(app.config['MONGO_URI'])
    
    # 初始化扩展
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # 加载用户
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.find_by_id(user_id) 