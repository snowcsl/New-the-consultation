from info.models import User, Category, News, Comment
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import user_blue
from info import redis_store, constants, db
from flask import render_template, current_app, session, jsonify, request, g, redirect


@user_blue.route('/base_info')
@user_login_data
def base_info():
    user = g.user
    data = {
        'user': user.to_dict()
    }
    return render_template('news/user_base_info.html', data=data)


@user_blue.route('/info')
@user_login_data
def info():
    user = g.user
    # 目前我们只需要在这里判断一次用户没登录. 因为如果咱们大的模板页面都无法加载, 小页面也是无法加载的
    if not user:
        return redirect('/')
    data = {
        'user': user.to_dict()
    }
    return render_template('news/user.html', data=data)