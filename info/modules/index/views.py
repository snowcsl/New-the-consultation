# 2. 导入创建的蓝图对象, 使用蓝图实现路由
from info.models import User, Category, News
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import index_blue
from info import redis_store, constants
from flask import render_template, current_app, session, jsonify, request, g


# 获取新闻列表接口
# 请求方式: GET
# 请求参数: cid, page, per_page
# 传入参数：args
@index_blue.route('/news_list')
def get_news_list():
    # 一. 获取参数 --> 不传设置默认
    cid = request.args.get('cid', 1)
    page = request.args.get('page', 1)
    per_page = request.args.get('per_page', constants.HOME_PAGE_MAX_NEWS)

    # 二. 校验参数 --> 类型校验(int)
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 三. 逻辑处理 --> News.query.filter(可有可无).order_by(创建时间降序).paginate(页码, 每页数据, False)

    # 以后遇到可选参数的查询语句. filter的条件是不确定的, 可以采取下面的技巧

    # 3.1 定义空列表, 用于将来拼接查询条件
    filters = []

    # 3.2 判断分类id是否有值
    if cid != 1:
        filters.append(News.category_id == cid)

    # 3.3 条件判断且拼接完毕, 会通过*进行展开
    try:
        paginates = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    # 3.4 获取查询后的数据
    news_models = paginates.items

    # 获取分页的总页码
    total_page = paginates.pages

    # 获取当前页码
    current_page = paginates.page

    # 3.5 模型转字典
    news_list = []
    for news in news_models if news_models else []:
        news_list.append(news.to_basic_dict())

    # 四. 返回数据 --> 返回data
    data = {
        'news_list': news_list,
        'total_page': total_page,
        'current_page': current_page
    }
    return jsonify(errno=RET.OK, errmsg="成功", data=data)


@index_blue.route('/')
@user_login_data
def index():

    # 一. 用户信息
    # 显示用户名和头像--> 核心逻辑--> 当重新加载首页时, 查询用户数据给模板
    user = g.user

    # 二. 分类信息
    # 查询数据 --> 模型转字典 --> 返回给前端
    try:
        category_models = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)

    category_list = []
    # 如果category_models有值, 就使用category_models的值
    # 如果category_models没有值, 就使用else后面的空数组给category_models赋值
    for category in category_models if category_models else []:
        category_list.append(category.to_dict())

    # 三. 点击排行信息
    try:
        # limit: 会按照设置的数量来返回结果
        news_models = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    click_news_list = []
    for news in news_models if news_models else []:
        click_news_list.append(news.to_basic_dict())

    # 封装成data字典, 传入模板
    data = {
        # 在处理不同接口的返回数据时, 不需要全部返回, 可以值返回需要的数据
        # user.to_index_dict(): 将模型对象转换为需要的数据字典
        'user': user.to_index_dict() if user else None,
        'category_list': category_list,
        'click_news_list': click_news_list
    }

    return render_template('news/index.html', data=data)


# 浏览器会自动请求该地址, 以获取网站的图标
@index_blue.route('/favicon.ico')
def favicon():
    # current_app: 是一次请求中, 产生的app的对象. 能够拥有所有app的属性和方法
    # 使用时无需关心原来的app在那个文件中
    # send_static_file: 发送静态文件. 查找到目录默认从static开始的
    return current_app.send_static_file('news/favicon.ico')
