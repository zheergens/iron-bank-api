from app.extensions import db
from app.models import BaseModel
from datetime import datetime

class Application(BaseModel):
    """应用模型，表示系统中注册的外部应用"""
    __tablename__ = 'applications'
    
    name = db.Column(db.String(100), nullable=False)
    app_id = db.Column(db.String(50), unique=True, nullable=False)
    client_id = db.Column(db.String(100), unique=True, nullable=False)
    client_secret = db.Column(db.String(100), nullable=False)
    redirect_uri = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, nullable=True)
    
    # 与用户的关系
    user_applications = db.relationship('UserApplication', back_populates='application', cascade='all, delete-orphan')
    app_requests = db.relationship('ApplicationRequest', back_populates='app', cascade='all, delete-orphan')
    
    @classmethod
    def find_by_app_id(cls, app_id):
        """通过app_id查找应用"""
        return cls.query.filter_by(app_id=app_id).first()
    
    @classmethod
    def find_by_client_id(cls, client_id):
        """通过client_id查找应用"""
        return cls.query.filter_by(client_id=client_id).first()
    
    @classmethod
    def get_all_active(cls):
        """获取所有活跃的应用"""
        return cls.query.filter_by(is_active=True).all()

class UserApplication(BaseModel):
    """用户应用授权关系"""
    __tablename__ = 'user_applications'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_user_application_user'), nullable=False)
    app_id = db.Column(db.String(50), db.ForeignKey('applications.app_id', name='fk_user_application_app'), nullable=False)
    access_token = db.Column(db.String(255), nullable=True)
    refresh_token = db.Column(db.String(255), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # 关系
    user = db.relationship('User', back_populates='applications')
    application = db.relationship('Application', back_populates='user_applications')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'app_id', name='uix_user_application'),
    )
    
    @classmethod
    def user_has_access(cls, user_id, app_id):
        """检查用户是否有访问应用的权限"""
        return cls.query.filter_by(user_id=user_id, app_id=app_id).first() is not None
    
    @classmethod
    def grant_access(cls, user_id, app_id):
        """授权用户访问应用"""
        if cls.user_has_access(user_id, app_id):
            return False
        
        user_app = cls(user_id=user_id, app_id=app_id)
        db.session.add(user_app)
        db.session.commit()
        return True
    
    @classmethod
    def revoke_access(cls, user_id, app_id):
        """撤销用户访问应用的权限"""
        user_app = cls.query.filter_by(user_id=user_id, app_id=app_id).first()
        if not user_app:
            return False
        
        db.session.delete(user_app)
        db.session.commit()
        return True

class ApplicationRequest(BaseModel):
    """应用访问请求"""
    __tablename__ = 'application_requests'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_app_request_user'), nullable=False)
    app_id = db.Column(db.String(50), db.ForeignKey('applications.app_id', name='fk_app_request_app'), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # 关系
    user = db.relationship('User', back_populates='app_requests')
    app = db.relationship('Application', back_populates='app_requests')
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'app_id', name='uix_user_app_request'),
    ) 