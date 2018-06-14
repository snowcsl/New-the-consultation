from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db
from config import *

app = create_app(DevelopmentConfig)

manager = Manager(app)

Migrate(app, db)

manager.add_command('db', MigrateCommand)


@app.route('/')
def hello_world():
    # redis_store.setex('name', 10, 'itheima')
    # session['name'] = 'zhubo'
    return 'Hello World!'


if __name__ == '__main__':
    manager.run()
