from flask import request
from info.utils.captcha.captcha import captcha
from . import passport_blue
from info import redis_store


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

    # 2. 生成图像验证码
    name, text, image_data = captcha.generate_captcha()

    # 3. 保存数据库
    redis_store.setex('image_code_id_' + image_code_id, 300, text)

    # 4. 返回图像
    return image_data
