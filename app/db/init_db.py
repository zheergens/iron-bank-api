def init_db(app):
    """初始化数据库"""
    from app.models.user import User
    from app.models.application import Application
    from datetime import datetime
    
    with app.app_context():
        # 创建管理员用户
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password='admin123',  # 设置初始密码
            is_admin=True,
            is_active=True,
            permissions=['admin']
        )
        
        # 设置创建时间为当前时间
        admin_user.created_at = datetime.utcnow().replace(tzinfo=None)
        admin_user.updated_at = datetime.utcnow().replace(tzinfo=None)
        
        # 检查管理员用户是否已存在
        existing_admin = User.find_by_username('admin')
        if not existing_admin:
            admin_user.save()
            print('Created admin user')
        else:
            print('Admin user already exists')
        
        # 创建测试应用
        test_app = Application(
            name='测试应用',
            description='这是一个测试应用',
            client_id='test_client',
            client_secret='test_secret',
            redirect_uri='http://localhost:5000/callback',
            is_active=True
        )
        
        # 检查测试应用是否已存在
        existing_app = Application.find_by_client_id('test_client')
        if not existing_app:
            test_app.save()
            print('Created test application')
        else:
            print('Test application already exists') 