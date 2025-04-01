"""
API模块 - 提供RESTful API接口
"""
from flask import Blueprint

def register_api_routes(app):
    """注册所有API路由"""
    # 创建API蓝图
    api = Blueprint('api', __name__, url_prefix='/api')
    
    # 导入子蓝图
    from .auth import api_auth
    from .users import api_users
    from .apps import api_apps
    
    # 注册子蓝图
    api.register_blueprint(api_auth)
    api.register_blueprint(api_users)
    api.register_blueprint(api_apps)
    
    # 注册API蓝图到应用
    app.register_blueprint(api)

# 导入API模块 - 在末尾导入避免循环引用
from . import auth, users, apps 