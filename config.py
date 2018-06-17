import redis
import logging


# 配置信息
class Config(object):

    # 配置mysql数据库
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1/information11'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 配置redis数据库
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # SECRET_KEY
    # import os, base64
    # base64.b64encode(os.urandom(32)
    SECRET_KEY = 'ULj2Dsn90IRqfAOqepxhT1ZxCehsURZH'

    # flask-session的配置信息
    SESSION_TYPE = "redis"  # 指定 session 保存到 redis 中
    SESSION_USE_SIGNER = True  # 让 cookie 中的 session_id 被加密签名处理
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)  # 使用 redis 的实例
    PERMANENT_SESSION_LIFETIME = 86400  # session 的有效期，单位是秒


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = logging.WARN
    # 正式开发中, 还需要更改mysql/redis的数据库配置(测试/正式)
    # SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@177.13.1.1/information11'


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = logging.DEBUG
