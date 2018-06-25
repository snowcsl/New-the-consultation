from flask import Blueprint, session, redirect, url_for, request

admin_blue = Blueprint('admin', __name__, url_prefix='/admin')

from . import views


# 可以给蓝图增加钩子函数. 会针对该蓝图所有的请求都实现
@admin_blue.before_request
def before_request():

    # 为了给后台管理站点, 每一个都增加权限的判断

    # 以下代码逻辑, 除了登录界面, 其他都需要执行
    if not request.url.endswith(url_for('admin.login')):

        # 去 session 中取指定的值
        user_id = session.get("user_id", None)
        is_admin = session.get("is_admin", False)

        # 如果任何一个缺失, 就不能正常访问-->返回首页
        if not user_id or not is_admin:
            return redirect('/')

    # 如果是登录界面, 什么都不干
