# 2. 导入创建的蓝图对象, 使用蓝图实现路由
from . import index_blue
from info import redis_store
from flask import render_template, current_app


@index_blue.route('/')
def index():
    return render_template('news/index.html')


# 浏览器会自动请求该地址, 以获取网站的图标
@index_blue.route('/favicon.ico')
def favicon():
    # current_app: 是一次请求中, 产生的app的对象. 能够拥有所有app的属性和方法
    # 使用时无需关心原来的app在那个文件中
    # send_static_file: 发送静态文件. 查找到目录默认从static开始的
    return current_app.send_static_file('news/favicon.ico')
