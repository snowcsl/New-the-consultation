# 2. 导入创建的蓝图对象, 使用蓝图实现路由
from . import index_blue
from info import redis_store


@index_blue.route('/')
def hello_world():
    redis_store.setex('name', 10, 'itheima')
    # session['name'] = 'zhubo'

    # logging.fatal('fatal')
    # logging.error('error')
    # logging.warning('warning')
    # logging.info('info')
    # logging.debug('debug')

    # current_app.logger.fatal('fatal')
    # current_app.logger.error('error')
    # current_app.logger.warning('warning')
    # current_app.logger.info('info')
    # current_app.logger.debug('debug')

    return 'Hello World!'