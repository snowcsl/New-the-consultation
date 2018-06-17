from flask import Blueprint

# url_prefix: 给蓝图增加前缀, 可以区分去路由地址
passport_blue = Blueprint('passport', __name__, url_prefix='/passport')

from . import views
