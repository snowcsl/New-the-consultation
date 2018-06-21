import redis
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from config import *
from logging.handlers import RotatingFileHandler
from flask_wtf.csrf import CSRFProtect, generate_csrf


db = SQLAlchemy()
redis_store = None  # type: redis.StrictRedis

def setup_log(config_name):
    # 设置日志的记录等级
    logging.basicConfig(level=config_name.LOG_LEVEL)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


# 提供工厂方法, 方便的通过配置参数的更改, 实现不同app的创建
def create_app(config_name):

    # 配置日志
    setup_log(config_name)

    app = Flask(__name__)

    app.config.from_object(config_name)

    # 几乎所有的扩展, 都支持这种创建方式
    db.init_app(app)

    global redis_store
    redis_store = redis.StrictRedis(host=config_name.REDIS_HOST, port=config_name.REDIS_PORT, decode_responses=True)

    # Flask-session扩展对象. 将存储到浏览器cookie中的session信息, 同步到指定地方(Redis)
    Session(app)

    # 开启CSRF保护
    # 从现在起, 程序会获取cookie中的随机值, 以及从表单或者ajax中获取随机值, 进行对比
    # 如果对比失败, 则无法访问路由
    # 后续需要设置随机值到cookie中, 以及增加ajax的hdeaers
    CSRFProtect(app)

    # 在这里增加请求钩子, 在请求之后设置cookie
    # 我们无法判断用户第一次访问网站时, 是哪个页面. 不能写死给某个网页
    # 需要对所有的请求都进行监听

    # csrf token 会被缓存起来, 多次调用, 只会返回相同的token(没有被强制删除或者没有过期)
    # 如果需要获取, 可以使用session['csrf_token']-->token会被扩展设置到session中
    # 应该对所有的post\put\delete请求增加ajax的header或者表单的隐藏字段
    @app.after_request
    def after_request(response):
        token = generate_csrf()
        response.set_cookie('csrf_token', token)
        return response

    # 增加自定义过滤器
    from info.utils.common import do_index_class
    app.add_template_filter(do_index_class, 'index_class')

    # 3. 在app创建的地方注册蓝图对象
    from info.modules.index import index_blue
    app.register_blueprint(index_blue)

    from info.modules.passport import passport_blue
    app.register_blueprint(passport_blue)

    return app
