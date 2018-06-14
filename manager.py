import redis
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from config import *

app = Flask(__name__)

app.config.from_object(DevelopmentConfig)

db = SQLAlchemy(app)

redis_store = redis.StrictRedis(host=DevelopmentConfig.REDIS_HOST, port=DevelopmentConfig.REDIS_PORT)

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
