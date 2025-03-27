from app import create_app
from app.models.user import User, db

app = create_app()

with app.app_context():
    # 检查管理员用户是否已存在
    admin = User.find_by_username('admin')
    if not admin:
        # 创建管理员用户
        admin = User.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin'
        )
        print('管理员用户创建成功') 