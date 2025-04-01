from flask import Flask, redirect, url_for, render_template
from flask_wtf.csrf import generate_csrf

from app.config import Config
from app.extensions import init_extensions
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 禁用静态文件缓存
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # 初始化扩展
    init_extensions(app)
    
    # 初始化数据库模型
    from app.models import init_models
    init_models()
    
    # 配置日志
    configure_logging(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 添加上下文处理器
    register_context_processors(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 添加根路由
    @app.route('/')
    def index():
        return redirect(url_for('user.profile'))
    
    # 注册API路由
    from app.api import register_api_routes
    register_api_routes(app)
    
    return app

def register_blueprints(app):
    """注册蓝图"""
    from app.auth.views import auth as auth_bp
    from app.routes.admin import admin as admin_bp
    from app.routes.user import user as user_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')

def register_error_handlers(app):
    """注册错误处理器"""
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f'服务器错误: {str(e)}')
        return render_template('errors/500.html'), 500

def register_context_processors(app):
    """注册上下文处理器"""
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=lambda: generate_csrf())

def configure_logging(app):
    """配置日志系统"""
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/app.log', 
            maxBytes=10240, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('应用启动') 