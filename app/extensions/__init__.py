"""
扩展模块 - 集中管理Flask扩展的初始化
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# 创建扩展实例
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def init_extensions(app):
    """初始化所有扩展"""
    # 配置登录管理器
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录后再访问此页面。'
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # 加载用户
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.find_by_id(int(user_id)) 