from app import create_app, db
from app.models.user import User

app = create_app()

def init_db():
    with app.app_context():
        # 删除所有表
        db.drop_all()
        # 创建所有表
        db.create_all()
        
        try:
            # 创建管理员用户
            User.create_user(
                username='admin',
                email='admin@example.com',
                password='123456',
                phone=None,
                role='admin'
            )
            print('默认管理员用户已创建: admin/123456')
        except Exception as e:
            print('管理员用户已存在或创建失败:', str(e))

if __name__ == '__main__':
    init_db() 