from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db
from config import *

app = create_app(DevelopmentConfig)

manager = Manager(app)

Migrate(app, db)

manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
