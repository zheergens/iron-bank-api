from flask.cli import FlaskGroup
from app import create_app, init_db
from app.models.user import User

cli = FlaskGroup(create_app=create_app)

@cli.command("init_db")
def init_db_command():
    """初始化数据库"""
    app = create_app()
    init_db(app)
    print("数据库初始化完成")

@cli.command("create_admin")
def create_admin_command():
    """创建管理员用户"""
    app = create_app()
    with app.app_context():
        try:
            # 检查是否已存在管理员用户
            admin = User.find_by_username('admin')
            if admin:
                print("管理员用户已存在")
                return
            
            # 创建新的管理员用户
            admin, error = User.create_user(
                username='admin',
                email='admin@example.com',
                password='admin123',
                is_admin=True
            )
            
            if error:
                print(f"创建管理员用户失败: {error}")
                return
                
            print("管理员用户创建成功")
        except Exception as e:
            print(f"创建管理员用户时发生错误: {str(e)}")

if __name__ == '__main__':
    cli() 