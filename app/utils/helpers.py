import hashlib
import random
import string
from datetime import datetime, timedelta

def generate_token(length=32):
    """生成随机令牌"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_hash(text):
    """生成文本的哈希值"""
    return hashlib.sha256(text.encode()).hexdigest()

def format_datetime(dt, format='%Y-%m-%d %H:%M:%S'):
    """格式化日期时间"""
    if not dt:
        return ''
    return dt.strftime(format)

def get_expiration_time(hours=24):
    """获取过期时间"""
    return datetime.utcnow() + timedelta(hours=hours)

def truncate_text(text, max_length=100, suffix='...'):
    """截断文本并添加后缀"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length] + suffix 