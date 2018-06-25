from info.models import User, Category, News, Comment
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import admin_blue
from info import redis_store, constants, db
from flask import render_template, current_app, session, jsonify, request, g, redirect, url_for


@admin_blue.route('/index')
@user_login_data
def index():
    user = g.user
    return render_template('admin/index.html', user=user.to_dict() if user else  None)


@admin_blue.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
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