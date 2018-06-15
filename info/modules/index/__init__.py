# 1. 导入蓝图模块, 创建蓝图对象, 导入子模块
from flask import Blueprint

index_blue = Blueprint('index', __name__)

from . import views
