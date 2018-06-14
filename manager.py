from flask import Flask
from flask_sqlalchemy import SQLAlchemy


# 配置信息
class Config(object):
    DEBUG = True

    # 配置mysql数据库
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1/information11'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


app = Flask(__name__)

app.config.from_object(Config)

db = SQLAlchemy(app)


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
