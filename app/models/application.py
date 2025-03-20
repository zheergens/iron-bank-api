from app.models.user import db
import datetime

class ApplicationRequest(db.Model):
    __tablename__ = 'application_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    app_id = db.Column(db.String(50))  # 应用的ID
    reason = db.Column(db.Text)  # 申请原因
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 审批管理员ID
    approved_at = db.Column(db.DateTime, nullable=True)  # 审批时间
    comment = db.Column(db.Text, nullable=True)  # 审批意见
    
    user = db.relationship('User', foreign_keys=[user_id], backref='application_requests')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_requests')
    
    @staticmethod
    def get_user_applications(user_id):
        return ApplicationRequest.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def get_pending_requests():
        return ApplicationRequest.query.filter_by(status='pending').all()
    
    def approve(self, admin_id, comment=None):
        self.status = 'approved'
        self.approved_by = admin_id
        self.approved_at = datetime.datetime.utcnow()
        self.comment = comment
        db.session.commit()
        
    def reject(self, admin_id, comment=None):
        self.status = 'rejected'
        self.approved_by = admin_id
        self.approved_at = datetime.datetime.utcnow()
        self.comment = comment
        db.session.commit()

class UserApplication(db.Model):
    __tablename__ = 'user_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    app_id = db.Column(db.String(50))  # 应用的ID
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    user = db.relationship('User', backref='applications')
    
    @staticmethod
    def user_has_access(user_id, app_id):
        return UserApplication.query.filter_by(user_id=user_id, app_id=app_id).first() is not None
    
    @staticmethod
    def grant_access(user_id, app_id):
        if not UserApplication.user_has_access(user_id, app_id):
            access = UserApplication(user_id=user_id, app_id=app_id)
            db.session.add(access)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def revoke_access(user_id, app_id):
        access = UserApplication.query.filter_by(user_id=user_id, app_id=app_id).first()
        if access:
            db.session.delete(access)
            db.session.commit()
            return True
        return False 