from info.models import News, Comment, User, CommentLike
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import news_blue
from info import constants, db
from flask import render_template, current_app, jsonify, request, g, abort


@news_blue.route('/comment_like', methods=["POST"])
@user_login_data
def set_comment_like():
    """评论点赞"""

    if not g.user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 获取参数
    comment_id = request.json.get("comment_id")
    action = request.json.get("action")

    # 判断参数
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ("add", "remove"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询评论数据
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论数据不存在")

    if action == "add":
        # 判断没有点过赞, 才能增加
        comment_like = CommentLike.query.filter_by(comment_id=comment_id, user_id=g.user.id).first()
        if not comment_like:
            comment_like = CommentLike()
            comment_like.comment_id = comment_id
            comment_like.user_id = g.user.id
            db.session.add(comment_like)
            # 增加点赞条数
            comment.like_count += 1
    else:
        # 删除点赞数据
        comment_like = CommentLike.query.filter_by(comment_id=comment_id, user_id=g.user.id).first()
        if comment_like:
            db.session.delete(comment_like)
            # 减小点赞条数
            comment.like_count -= 1

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")
    return jsonify(errno=RET.OK, errmsg="操作成功")


@news_blue.route('/followed_user', methods=["POST"])
@user_login_data
def followed_user():
    """关注/取消关注用户"""
    if not g.user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    # 被关注的人的ID
    user_id = request.json.get("user_id")
    action = request.json.get("action")

    if not all([user_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ("follow", "unfollow"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 查询到关注的用户信息
    try:
        target_user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据库失败")

    if not target_user:
        return jsonify(errno=RET.NODATA, errmsg="未查询到用户数据")

    # 根据不同操作做不同逻辑
    if action == "follow":
        # 要想关注某个用户, 要先确保对方的粉丝列表中没有我

        # 目标用户的粉丝表中, 查询自己的id, 如果个数大于0, 说明已关注
        if target_user.followers.filter(User.id == g.user.id).count() > 0:
            return jsonify(errno=RET.DATAEXIST, errmsg="当前已关注")
        target_user.followers.append(g.user)
    else:
        if target_user.followers.filter(User.id == g.user.id).count() > 0:
            target_user.followers.remove(g.user)

    # 保存到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据保存错误")

    return jsonify(errno=RET.OK, errmsg="操作成功")


# 发布评论
@news_blue.route('/news_comment', methods=['POST'])
@user_login_data
def news_comment():

    # 一. 获取参数
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    news_id = request.json.get('news_id')
    comment_str = request.json.get('comment')
    parent_id = request.json.get('parent_id')  # 只有子评论才有父评论ID

    # 二. 校验参数
    if not all([news_id, comment_str]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 三. 逻辑处理
    # 先确保用户和新闻都存在 --> 添加评论模型
    # 3.1 查询新闻
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="无新闻数据")

    # 3.2 创建评论模型
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news.id
    comment.content = comment_str
    if parent_id:
        comment.parent_id = parent_id

    # 3.3 提交数据库
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    # 四. 返回数据
    return jsonify(errno=RET.OK, errmsg="成功", data=comment.to_dict())


# 收藏和取消收藏
@news_blue.route('/news_collect', methods=['POST'])
@user_login_data
def news_collect():

    # 一. 获取参数
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")

    news_id = request.json.get('news_id')
    action = request.json.get('action')

    # 二. 校验参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ['collect', 'cancel_collect']:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 三. 逻辑处理
    # 1. 查询新闻
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="无数据")

    # 2. 根据按钮点击的值来进行添加或删除
    if action == 'collect':
        # 先判断用户没有收藏过,才能收藏
        if news not in user.collection_news:
            user.collection_news.append(news)
    else:
        # 先判断用户收藏过, 才能删除
        if news in user.collection_news:
            user.collection_news.remove(news)

    # 3. 提交数据
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    # 四. 返回数据
    return jsonify(errno=RET.OK, errmsg="成功")


# 获取新闻详情
@news_blue.route('/<int:news_id>')
@user_login_data
def get_news_detail(news_id):
    # 一. 用户信息
    # 显示用户名和头像--> 核心逻辑--> 当重新加载首页时, 查询用户数据给模板
    user = g.user

    # 二. 点击排行信息
    news_models = None
    try:
        # limit: 会按照设置的数量来返回结果
        news_models = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    click_news_list = []
    for news in news_models if news_models else []:
        click_news_list.append(news.to_basic_dict())

    # 三. 获取新闻详情信息
    # 3.1 查询新闻数据
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)

    if not news:
        abort(404)

    # 3.2 增加点击量
    news.clicks += 1

    # 3.3 提交到数据库中
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        abort(500)

    # 四. 查询用户收藏数据
    is_collected = False
    if user:
        # 判断已登录的用户, 有收藏该新闻
        if news in user.collection_news:
            is_collected = True

    # 五. 新闻评论
    comment_models = []
    try:
        comment_models = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    # 六. 关注的处理
    is_followed = False

    # 已关注: 1. 确保用户登录和新闻的作者都存在
    if user and news.user:
        # 2. 查看我是否在新闻作者的粉丝表中
        if user in news.user.followers:
            is_followed = True

    comment_list =[]
    for comment in comment_models:
        comment_list.append(comment.to_dict())

    # 封装成data字典, 传入模板
    data = {
        # 在处理不同接口的返回数据时, 不需要全部返回, 可以值返回需要的数据
        # user.to_index_dict(): 将模型对象转换为需要的数据字典
        'user': user.to_index_dict() if user else None,
        'click_news_list': click_news_list,
        'news': news.to_dict(),
        'is_collected': is_collected,
        'comment_list': comment_list,
        'is_followed': is_followed
    }
    return render_template('news/detail.html', data=data)
