from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        self.last_login = datetime.datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def create_user(cls, username, email, password, role='user'):
        user = cls(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    
    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def find_by_id(cls, user_id):
        return cls.query.get(user_id)
    
    @classmethod
    def get_all_users(cls):
        return cls.query.all() 