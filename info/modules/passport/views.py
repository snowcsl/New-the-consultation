from . import passport_blue


@passport_blue.route('/index')
def index():
    return 'index'
