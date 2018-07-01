from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db, models
from config import *
from info.models import User

app = create_app(DevelopmentConfig)

manager = Manager(app)

Migrate(app, db)

manager.add_command('db', MigrateCommand)

# zhubo
# python manager.py createsuperuser -n admin -p 123456
@manager.option('-n', '-name', dest='name')
@manager.option('-p', '-password', dest='password')
def createsuperuser(name, password):
    """创建管理员用户"""
    if not all([name, password]):
        print('参数不全')
        return

    user = User()
    user.mobile = name
    user.nick_name = name
    user.password = password
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
        print("创建成功")
    except Exception as e:
        print(e)
        db.session.rollback()



if __name__ == '__main__':
    print(app.url_map)
    manager.run()
