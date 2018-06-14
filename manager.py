import redis
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand


# 配置信息
class Config(object):
    DEBUG = True

    # 配置mysql数据库
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1/information11'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 配置redis数据库
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    SECRET_KEY = "EjpNVSNQTyGi1VvWECj9TvC/+kq3oujee2kTfQUs8yCM6xX9Yjq52v54g+HVoknA"

    # flask-session的配置信息
    SESSION_TYPE = "redis"  # 指定 session 保存到 redis 中
    SESSION_USE_SIGNER = True  # 让 cookie 中的 session_id 被加密签名处理
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)  # 使用 redis 的实例
    PERMANENT_SESSION_LIFETIME = 86400  # session 的有效期，单位是秒


app = Flask(__name__)

app.config.from_object(Config)

db = SQLAlchemy(app)

redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

# Flask-session扩展对象. 将存储到浏览器cookie中的session信息, 同步到指定地方(Redis)
Session(app)

manager = Manager(app)

Migrate(app, db)

manager.add_command('db', MigrateCommand)


@app.route('/')
def hello_world():
    # redis_store.setex('name', 10, 'itheima')
    session['name'] = 'zhubo'
    return 'Hello World!'


if __name__ == '__main__':
    manager.run()
