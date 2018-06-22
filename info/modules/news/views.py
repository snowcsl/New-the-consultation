from info.models import User, Category, News
from info.utils.response_code import RET
from . import news_blue
from info import redis_store, constants
from flask import render_template, current_app, session, jsonify, request


@news_blue.route('/<news_id>')
def get_news_detail(news_id):
    return render_template('news/detail.html')
