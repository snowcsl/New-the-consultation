from info.models import User, Category, News, Comment
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import user_blue
from info import redis_store, constants, db
from flask import render_template, current_app, session, jsonify, request, g, redirect


@user_blue.route('/news_list')
@user_login_data
def news_list():
    
    # 一. 获取参数
    page = request.args.get('page', 1)
    
    # 二. 校验参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1
    
    # 三. 逻辑处理
    user = g.user
    news_models = []
    current_page = 1
    total_page = 1
    try:
        paginate = News.query.filter(News.user_id == user.id).paginate(page, 1, False)

        # 获取分页数据
        news_models = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages

    except Exception as e:
        current_app.logger.error(e)

    news_list = []
    for news in news_models:
        news_list.append(news.to_dict())

    # 四. 返回数据
    data = {
        'news_list': news_list,
        'current_page': current_page,
        'total_page': total_page
    }
    return render_template('news/user_news_list.html', data=data)


@user_blue.route('/news_release', methods=['GET', 'POST'])
@user_login_data
def news_release():

    # GET请求传递分类数据并渲染模板
    if request.method == 'GET':
        # 查询分类
        category_models = []
        try:
            category_models = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库错误")

        # 模型转字典
        category_list = []
        for category in category_models:
            category_list.append(category.to_dict())

        # 删除第一个元素
        category_list.pop(0)

        data = {
            'category_list': category_list
        }
        return render_template('news/user_news_release.html', data=data)

    # POST请求
    # 一. 获取参数
    title = request.form.get("title")
    source = "个人发布"
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    category_id = request.form.get("category_id")

    # 二. 校验参数
    # 1. 完整性
    if not all([title, source, digest, content, index_image, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 2. 读取图片
    try:
        image_data = index_image.read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 3. 分类ID(类型, 查询是否已存在)
    try:
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    try:
        category_model = Category.query.get(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    if not category_model:
        return jsonify(errno=RET.NODATA, errmsg="无分类数据")

    # 三. 逻辑处理
    # 1. 上传图片
    try:
        image_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    # 2. 创建新闻模型
    news = News()
    news.title = title
    news.digest = digest
    news.source = source
    news.content = content
    # 新闻很多是爬来的. 网址前缀并非统一. 为了读取方便, 我们统一都加上前缀
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + image_name
    news.category_id = category_id
    news.user_id = g.user.id  # 发布新闻的人
    # 1代表待审核状态
    news.status = 1

    # 3. 保存到数据库
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    # 四. 返回数据
    return jsonify(errno=RET.OK, errmsg="发布成功，等待审核")


@user_blue.route('/collection')
@user_login_data
def collection():
    # 一. 获取参数
    page = request.args.get('page', 1)

    # 二. 校验参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        # 此时因为需要渲染网站, 不能返回JSON错误.
        # 就需要对错误的参数进行赋默认值
        page = 1

    # 三. 逻辑处理
    user = g.user
    try:
        # 进行分页数据查询
        paginate = user.collection_news.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        # 获取分页数据
        collection_models = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        collection_models = []
        current_page = 1
        total_page = 1

    collection_list = []
    for collection in collection_models:
        collection_list.append(collection.to_dict())

    # 四. 返回数据
    data = {
        "total_page": total_page,
        "current_page": current_page,
        "collection_list": collection_list
    }
    return render_template('news/user_collection.html', data=data)


@user_blue.route('/pass_info', methods=["GET", "POST"])
@user_login_data
def pass_info():
    if request.method == "GET":
        return render_template('news/user_pass_info.html')

    # 1. 获取到传入参数
    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")

    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    # 2. 获取当前登录用户的信息
    user = g.user

    if not user.check_password(old_password):
        return jsonify(errno=RET.PWDERR, errmsg="原密码错误")

    # 更新数据
    user.password = new_password

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    return jsonify(errno=RET.OK, errmsg="保存成功")


@user_blue.route('/pic_info', methods=["GET", "POST"])
@user_login_data
def pic_info():
    user = g.user
    if request.method == 'GET':
        return render_template('news/user_pic_info.html', data={"user": user.to_dict()})

    # POST请求
    # 一. 获取数据&参数校验
    try:
        avatar_data = request.files.get('avatar').read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 二. 上传到七牛云&存储到数据库
    try:
        avatar_name = storage(avatar_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="上传七牛云错误")

    # 存储时可以不存前缀
    user.avatar_url = avatar_name
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    # 三. 返回数据
    return jsonify(errno=RET.OK, errmsg="OK", data={"avatar_url": constants.QINIU_DOMIN_PREFIX + avatar_name})


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