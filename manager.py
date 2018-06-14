import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


# 配置信息
class Config(object):
    DEBUG = True

    # 配置mysql数据库
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1/information11'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 配置redis数据库
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379


app = Flask(__name__)

app.config.from_object(Config)

db = SQLAlchemy(app)

redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)


@app.route('/')
def hello_world():
    # redis_store.setex('name', 10, 'itheima')
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
