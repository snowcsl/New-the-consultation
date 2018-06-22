from info.models import User, Category, News
from info.utils.response_code import RET
from . import news_blue
from info import redis_store, constants
from flask import render_template, current_app, session, jsonify, request


@news_blue.route('/<news_id>')
def get_news_detail(news_id):
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

    # 封装成data字典, 传入模板
    data = {
        # 在处理不同接口的返回数据时, 不需要全部返回, 可以值返回需要的数据
        # user.to_index_dict(): 将模型对象转换为需要的数据字典
        'user': user.to_index_dict() if user else None,
        'click_news_list': click_news_list
    }
    return render_template('news/detail.html', data=data)
