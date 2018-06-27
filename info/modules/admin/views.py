import time
from datetime import datetime, timedelta
from info.models import User, Category, News, Comment
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import admin_blue
from info import redis_store, constants, db
from flask import render_template, current_app, session, jsonify, request, g, redirect, url_for


@admin_blue.route('/news_edit_detail')
def news_edit_detail():
    """新闻编辑详情"""

    # 获取参数
    news_id = request.args.get("news_id")

    if not news_id:
        return render_template('admin/news_edit_detail.html', data={"errmsg": "未查询到此新闻"})

    # 查询新闻
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        return render_template('admin/news_edit_detail.html', data={"errmsg": "未查询到此新闻"})

    # 查询分类的数据
    categories = Category.query.all()
    categories_li = []
    for category in categories:

        # 增加一个字段, 用来描述是否需要选中
        c_dict = category.to_dict()
        c_dict["is_selected"] = False
        # 只有当新闻的分类ID和数据库的一样时, 才会设置为Ture
        if category.id == news.category_id:
            c_dict["is_selected"] = True

        categories_li.append(c_dict)

    # 移除`最新`分类
    categories_li.pop(0)

    data = {"news": news.to_dict(), "categories": categories_li}
    return render_template('admin/news_edit_detail.html', data=data)


@admin_blue.route('/news_edit')
def news_edit():
    """返回新闻列表"""

    page = request.args.get("p", 1)
    keywords = request.args.get("keywords", "")
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    news_list = []
    current_page = 1
    total_page = 1

    try:
        filters = []
        # 如果有关键词
        if keywords:
            # 添加关键词的检索选项
            filters.append(News.title.contains(keywords))

        # 查询
        paginate = News.query.filter(*filters) \
            .order_by(News.create_time.desc()) \
            .paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)

        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_basic_dict())

    context = {"total_page": total_page, "current_page": current_page, "news_list": news_dict_list}

    return render_template('admin/news_edit.html', data=context)


@admin_blue.route('/news_review_detail', methods=['GET', 'POST'])
def news_review_detail():
    """新闻审核"""

    if request.method == 'GET':
        # 获取新闻id
        news_id = request.args.get("news_id")
        if not news_id:
            return render_template('admin/news_review_detail.html', data={"errmsg": "未查询到此新闻"})

        # 通过id查询新闻
        news = None
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)

        if not news:
            return render_template('admin/news_review_detail.html', data={"errmsg": "未查询到此新闻"})

        # 返回数据
        data = {"news": news.to_dict()}
        return render_template('admin/news_review_detail.html', data=data)

    # 执行审核操作
    # 1.获取参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    # 2.判断参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    news = None
    try:
        # 3.查询新闻
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到数据")

    # 4.根据不同的状态设置不同的值
    if action == "accept":
        news.status = 0
    else:
        # 拒绝通过，需要获取原因
        reason = request.json.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
        news.reason = reason
        news.status = -1

    # 保存数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="数据保存失败")
    return jsonify(errno=RET.OK, errmsg="操作成功")


@admin_blue.route('/news_review')
def news_review():
    """返回待审核新闻列表"""

    page = request.args.get("p", 1)
    keywords = request.args.get("keywords", "")

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    news_list = []
    current_page = 1
    total_page = 1

    # 处理可选参数
    filters = [News.status != 0]

    if keywords:
        filters.append(News.title.contains(keywords))

    try:
        paginate = News.query.filter(*filters) \
            .order_by(News.create_time.desc()) \
            .paginate(page, constants.ADMIN_NEWS_PAGE_MAX_COUNT, False)

        news_list = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    news_dict_list = []
    for news in news_list:
        news_dict_list.append(news.to_review_dict())

    context = {"total_page": total_page, "current_page": current_page, "news_list": news_dict_list}

    return render_template('admin/news_review.html', data=context)


@admin_blue.route('/user_list')
def user_list():
    """获取用户列表"""

    # 获取参数
    page = request.args.get("p", 1)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 设置变量默认值
    users = []
    current_page = 1
    total_page = 1

    # 查询数据
    try:
        paginate = User.query.filter(User.is_admin == False).order_by(User.last_login.desc()).paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        users = paginate.items
        current_page = paginate.page
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    # 将模型列表转成字典列表
    users_list = []
    for user in users:
        users_list.append(user.to_admin_dict())

    context = {"total_page": total_page, "current_page": current_page, "users": users_list}
    return render_template('admin/user_list.html',
                           data=context)


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

    # 2. 当月新增 --> 获取同年同月1号的时间 从这个时间开始查询数据即可

    """
    2018-06-01 00:00:00
    2018-06-27 15:14:11
    
    1. 如何获取 ()年 ()月
    2. 如何将字符串按照一定的格式转换为日期对象
    """

    #  1. 获取 ()年 ()月
    # now = datetime.now()
    # now = time.localtime()
    # mon_begin = '%d-%02d-01' % (now.tm_year, now.tm_mon)

    # 2. 将字符串, 转换日期
    # strptime: 专门用户将字符串转日期的
    # begin_date = datetime.strptime(mon_begin, '%Y-%m-%d')
    # User.query.filter(User.create_time >= 当月开始时间).count()
    mon_count = 0
    now = time.localtime()
    try:
        mon_begin = '%d-%02d-01' % (now.tm_year, now.tm_mon)
        mon_begin_date = datetime.strptime(mon_begin, '%Y-%m-%d')
        mon_count = User.query.filter(User.is_admin == False, User.create_time >= mon_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 3. 查询日新增数
    day_count = 0
    try:
        # 2018-6-27
        day_begin = '%d-%02d-%02d' % (now.tm_year, now.tm_mon, now.tm_mday)
        day_begin_date = datetime.strptime(day_begin, '%Y-%m-%d')
        day_count = User.query.filter(User.is_admin == False, User.create_time > day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 二. 下方活跃度
    """
    统计最近一个月每一天的用户活跃度(最后登录)
    # 2018-5-28 --> 2018-5-28 00:00:00 -- 2018-5-29 00:00:00
    User.last_login >= day_begin_date, User.last_login < day_end_date
    
    1. 如何获取指定日期的下一天时间
    2. 如何快速实现前一个的查询(for)
    """
    # 查询图表信息
    # 获取到当天00:00:00时间
    # strftime: 将日期按照一定的格式转换字符串的. 用法和strftime相反
    now_date_str = datetime.now().strftime('%Y-%m-%d')
    now_date = datetime.strptime(now_date_str, '%Y-%m-%d')

    # 定义空数组，保存数据
    active_date = []
    active_count = []

    # 依次添加数据，再反转
    for i in range(0, 31):
        begin_date = now_date - timedelta(days=i)
        end_date = now_date - timedelta(days=(i - 1))
        # 获取计算的当天日期 ['2018-06-27']
        active_date.append(begin_date.strftime('%Y-%m-%d'))
        count = 0
        try:
            count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,
                                      User.last_login < end_date).count()
        except Exception as e:
            current_app.logger.error(e)
        # 获取当天的活跃数
        active_count.append(count)

    active_date.reverse()
    active_count.reverse()

    data = {
        'total_count': total_count,
        'mon_count': mon_count,
        'day_count': day_count,
        'active_date': active_date,
        'active_count': active_count
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