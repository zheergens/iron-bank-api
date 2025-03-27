from datetime import datetime
from app.models import db
from app.models.user import User

class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    client_id = db.Column(db.String(100), unique=True, nullable=False)
    client_secret = db.Column(db.String(100), nullable=False)
    redirect_uri = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_all_applications():
        return Application.query.all()

class ApplicationRequest(db.Model):
    __tablename__ = 'application_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    user = db.relationship('User', backref=db.backref('application_requests', lazy=True))
    application = db.relationship('Application', backref=db.backref('requests', lazy=True))

class UserApplication(db.Model):
    __tablename__ = 'user_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    access_token = db.Column(db.String(100))
    refresh_token = db.Column(db.String(100))
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    user = db.relationship('User', backref=db.backref('applications', lazy=True))
    application = db.relationship('Application', backref=db.backref('users', lazy=True))

    @staticmethod
    def user_has_access(user_id, app_id):
        return UserApplication.query.filter_by(user_id=user_id, application_id=app_id).first() is not None
    
    @staticmethod
    def grant_access(user_id, app_id):
        if not UserApplication.user_has_access(user_id, app_id):
            access = UserApplication(user_id=user_id, application_id=app_id)
            db.session.add(access)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def revoke_access(user_id, app_id):
        access = UserApplication.query.filter_by(user_id=user_id, application_id=app_id).first()
        if access:
            db.session.delete(access)
            db.session.commit()
            return True
        return False 