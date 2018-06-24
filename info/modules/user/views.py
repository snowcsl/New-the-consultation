from info.models import User, Category, News, Comment
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import user_blue
from info import redis_store, constants, db
from flask import render_template, current_app, session, jsonify, request, g, redirect


@user_blue.route('/base_info', methods=['GET', 'POST'])
@user_login_data
def base_info():

    # 获取用户信息
    user = g.user

    # GET请求渲染模板
    if request.method == 'GET':
        data = {
            'user': user.to_dict()
        }
        return render_template('news/user_base_info.html', data=data)

    # POST请求修改数据
    # 一. 获取参数
    nick_name = request.json.get("nick_name")
    gender = request.json.get("gender")
    signature = request.json.get("signature")

    # 二. 校验参数
    if not all([nick_name, gender, signature]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    if gender not in ['MAN', 'WOMAN']:
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 三. 逻辑处理
    # 修改模型数据
    user.nick_name = nick_name
    user.gender = gender
    user.signature = signature

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    # 设置session数据
    session['nick_name'] = nick_name

    # 四. 返回数据
    return jsonify(errno=RET.OK, errmsg="更新成功")


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