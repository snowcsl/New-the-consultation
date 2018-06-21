# 2. 导入创建的蓝图对象, 使用蓝图实现路由
from info.models import User, Category
from info.utils.response_code import RET
from . import index_blue
from info import redis_store
from flask import render_template, current_app, session, jsonify


@index_blue.route('/')
def index():

    # 一. 用户信息
    # 显示用户名和头像--> 核心逻辑--> 当重新加载首页时, 查询用户数据给模板

    # 1. 从session获取用户id
    user_id = session.get('user_id', None)

    # 2. 根据用户id查询数据
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    # 二. 分类信息
    # 查询数据 --> 模型转字典 --> 返回给前端
    try:
        category_models = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    category_list = []
    # 如果category_models有值, 就使用category_models的值
    # 如果category_models没有值, 就使用else后面的空数组给category_models赋值
    for category in category_models if category_models else []:
        category_list.append(category.to_dict())

    # 封装成data字典, 传入模板
    data = {
        # 在处理不同接口的返回数据时, 不需要全部返回, 可以值返回需要的数据
        # user.to_index_dict(): 将模型对象转换为需要的数据字典
        'user': user.to_index_dict() if user else None,
        'category_list': category_list
    }

    return render_template('news/index.html', data=data)


# 浏览器会自动请求该地址, 以获取网站的图标
@index_blue.route('/favicon.ico')
def favicon():
    # current_app: 是一次请求中, 产生的app的对象. 能够拥有所有app的属性和方法
    # 使用时无需关心原来的app在那个文件中
    # send_static_file: 发送静态文件. 查找到目录默认从static开始的
    return current_app.send_static_file('news/favicon.ico')
