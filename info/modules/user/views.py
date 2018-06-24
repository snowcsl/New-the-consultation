from info.models import User, Category, News, Comment
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import user_blue
from info import redis_store, constants, db
from flask import render_template, current_app, session, jsonify, request, g, redirect


@user_blue.route('/info')
@user_login_data
def info():
    user = g.user
    if not user:
        return redirect('/')
    data = {
        'user': user.to_dict()
    }
    return render_template('news/user.html', data=data)