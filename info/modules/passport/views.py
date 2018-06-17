from flask import request, abort, current_app, make_response
from info.utils.captcha.captcha import captcha
from . import passport_blue
from info import redis_store
from info import constants


# 开发中, 后端人员来定义路由地址\请求方式\参数\返回值等
# URL:/image_code
# 请求方式: GET (一般来说, 获取数据用GET, 提交数据用POST. 实际上对于后端来说无所谓)
# 参数: image_code_id
# 返回数据: JSON数据 (模板/JSON数据)
@passport_blue.route('/image_code')
def get_image_code():
    """
    1. 获取UUID
    2. 生成图像验证码
    3. 保存数据库
    4. 返回图像
    """
    # 1. 获取UUID
    image_code_id = request.args.get('image_code_id')
    if not image_code_id:
        return abort(403)

    # 2. 生成图像验证码
    name, text, image_data = captcha.generate_captcha()

    # 3. 保存数据库
    try:
        # 增加类型注释 redis_store = None  # type: redis.StrictRedis
        redis_store.setex('image_code_id_' + image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 3.1 记录日志
        # logging.error(e)
        current_app.logger.error(e)

        # 3.2 返回错误
        return abort(500)

    # 4. 返回图像
    response = make_response(image_data)
    response.headers['Content-Type'] = 'image/jpg'
    return response
