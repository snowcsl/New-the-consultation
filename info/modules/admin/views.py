from info.models import User, Category, News, Comment
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import admin_blue
from info import redis_store, constants, db
from flask import render_template, current_app, session, jsonify, request, g, redirect, url_for


@admin_blue.route('/user_count')
@user_login_data
def user_count():

    # 一. 上方统计数据

    # 1. 用户总数
    total_count = 0

    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    data = {
        'total_count': total_count
    }
    return render_template('admin/user_count.html', data=data)


@admin_blue.route('/index')
@user_login_data
def index():
    user = g.user
    return render_template('admin/index.html', user=user.to_dict() if user else  None)


@admin_blue.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":

        # 去 session 中取指定的值
        user_id = session.get("user_id", None)
        is_admin = session.get("is_admin", False)

        # 如果用户id存在，并且是管理员，那么直接跳转管理后台主页
        if user_id and is_admin:
            return redirect(url_for('admin.index'))

        return render_template('admin/login.html')

    # 取到登录的参数
    username = request.form.get("username")
    password = request.form.get("password")

    # 判断参数
    if not all([username, password]):
        return render_template('admin/login.html', errmsg="参数错误")

    # 查询当前用户
    try:
        user = User.query.filter(User.mobile == username, User.is_admin == True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg="用户信息查询失败")

    if not user or not user.check_password(password):
        return render_template('admin/login.html', errmsg="用户名或者密码错误")

    # 保存用户的登录信息
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["is_admin"] = user.is_admin

    # 跳转到后面管理首页
    return redirect(url_for('admin.index'))