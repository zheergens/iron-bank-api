from app import create_app
from app.models.user import User

def create_admin_user(username, email, password, phone=None):
    app = create_app()
    with app.app_context():
        # 检查用户名是否已存在
        if User.find_by_username(username):
            print(f"用户名 {username} 已存在")
            return False
        
        # 创建管理员用户
        admin = User.create_user(
            username=username,
            email=email,
            password=password,
            phone=phone,
            role='admin'
        )
        
        if admin:
            print(f"管理员账号 {username} 创建成功")
            return True
        else:
            print("创建管理员账号失败")
            return False

if __name__ == '__main__':
    # 设置管理员账号信息
    admin_username = 'admin'
    admin_email = 'admin@example.com'
    admin_password = 'admin123'  # 请修改为更安全的密码
    admin_phone = '13800138000'  # 可选
    
    create_admin_user(admin_username, admin_email, admin_password, admin_phone) 