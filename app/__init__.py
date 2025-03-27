from flask import Flask, redirect, url_for
from flask_login import LoginManager
from app.config import Config
from app.models.user import db, User
from app.models.application import ApplicationRequest, UserApplication
from flask_migrate import Migrate

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录后再访问此页面。'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 禁用静态文件缓存
    
    # 初始化数据库
    db.init_app(app)
    
    # 初始化数据库迁移
    migrate = Migrate(app, db)
    
    # 初始化登录管理器
    login_manager.init_app(app)
    
    # 注册蓝图
    from app.routes.auth import auth as auth_bp
    from app.routes.admin import admin as admin_bp
    from app.routes.user import user as user_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')
    
    # 添加根路由重定向到用户个人资料页面
    @app.route('/')
    def index():
        return redirect(url_for('user.profile'))
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.find_by_id(int(user_id))
    
    return app 