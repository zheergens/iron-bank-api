from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_models():
    from .user import User
    from .application import Application, UserApplication

from .user import User
from .application import Application 