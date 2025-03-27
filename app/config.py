import os
from dotenv import load_dotenv
import datetime
import random

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-should-be-changed'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///user_auth.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_NAME = 'sso_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # 在生产环境中设置为True
    REMEMBER_COOKIE_DURATION = 86400  # 1天
    
    # 已注册的应用程序列表
    REGISTERED_APPS = {
        'app1': {
            'name': '应用程序1',
            'redirect_uri': 'http://localhost:5001/auth/callback',
            'client_id': 'app1_client_id',
            'client_secret': 'app1_client_secret',
        },
        'app2': {
            'name': '应用程序2',
            'redirect_uri': 'http://localhost:5002/auth/callback',
            'client_id': 'app2_client_id',
            'client_secret': 'app2_client_secret',
        },
        # 可以添加更多应用
    } 