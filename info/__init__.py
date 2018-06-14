import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from config import *

db = SQLAlchemy()
redis_store = None


# 提供工厂方法, 方便的通过配置参数的更改, 实现不同app的创建
def create_app(config_name):

    app = Flask(__name__)

    app.config.from_object(config_name)

    # 几乎所有的扩展, 都支持这种创建方式
    db.init_app(app)

    global redis_store
    redis_store = redis.StrictRedis(host=config_name.REDIS_HOST, port=config_name.REDIS_PORT)

    # Flask-session扩展对象. 将存储到浏览器cookie中的session信息, 同步到指定地方(Redis)
    Session(app)

    return app