from flask import Blueprint

auth = Blueprint('auth', __name__)

from . import views  # 避免循环导入 