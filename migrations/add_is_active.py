from app.extensions import mongo_client
from app.models.user import User

def migrate():
    """为所有用户添加 is_active 字段"""
    db = mongo_client.get_default_database()
    users = db.users.find({})
    
    for user in users:
        # 如果用户没有 is_active 字段，添加它并设置为 True
        if 'is_active' not in user:
            db.users.update_one(
                {'_id': user['_id']},
                {'$set': {'is_active': True}}
            )
            print(f"Added is_active field for user: {user['username']}")

if __name__ == '__main__':
    migrate()
    print("Migration completed successfully!") 