"""
API模块 - 提供RESTful API接口
"""
from flask import Blueprint

# 创建API蓝图
api = Blueprint('api', __name__, url_prefix='/api')

def register_api_routes(app):
    """注册API路由到Flask应用"""
    app.register_blueprint(api)

# 导入API模块 - 在末尾导入避免循环引用
from . import auth, users, apps 