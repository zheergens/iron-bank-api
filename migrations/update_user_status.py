from app.extensions import mongo_client
from bson import ObjectId

def update_user_status(username, is_active):
    """更新指定用户的状态
    
    Args:
        username: 用户名
        is_active: 是否激活
    """
    db = mongo_client.get_default_database()
    result = db.users.update_one(
        {'username': username},
        {'$set': {'is_active': is_active}}
    )
    
    if result.modified_count > 0:
        print(f"Successfully updated status for user: {username}")
    else:
        print(f"No user found with username: {username}")

if __name__ == '__main__':
    # 更新 bc 用户的状态为禁用
    update_user_status('bc', False)
    print("Migration completed successfully!") 