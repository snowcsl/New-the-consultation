# 工具类中的公用方法文件
from flask import session, current_app, g

from info.models import User


def do_index_class(index):
    if index == 1:
        return 'first'
    elif index == 2:
        return 'second'
    elif index == 3:
        return 'third'
    else:
        return ""


# 在不改变程序代码的情况下, 扩充功能
def user_login_data(view_func):
    def wrapper(*args, **kwargs):
        # 要增加的逻辑代码

        # 1. 从session获取用户id
        user_id = session.get('user_id', None)

        # 2. 根据用户id查询数据
        user = None
        if user_id:
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)

        # 3. 使用g变量进行传值
        # 应用上下文, 随着请求发出而产生, 请求消失而消失
        # 可以使用g变量很方便的在一个请求中的多个函数之间进行传值
        g.user = user

        return view_func(*args, **kwargs)
    return wrapper
