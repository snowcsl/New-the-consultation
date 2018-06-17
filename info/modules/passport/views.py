import re
from flask import request, abort, current_app, make_response, json, jsonify
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_blue
from info import redis_store
from info import constants


# 开发中, 后端人员来定义路由地址\请求方式\参数\返回值等


# URL:/sms_code
# 请求方式: POST
# 参数: image_code_id, mobile , image_code
# 返回数据: JSON数据
@passport_blue.route('/sms_code', methods=['POST'])
def sms_code():
    """
    1. 获取参数
    2. 校验参数
    3. 从redis获取图像验证码
    4. 对比验证码
    5. 生成短信验证码
    6. 保存验证码到redis
    7. 发送短信
    8. 返回成功信息
    """

    # 一. 获取参数
    # 1. 获取参数
    # data = request.data
    # json_data = json.loads(data)
    # 开发中获取JSON数据, 会使用request.json. 直接可以获取字典数据, 方便解析数据
    json_data = request.json
    image_code_id = json_data.get('image_code_id')
    image_code = json_data.get('image_code')
    mobile = json_data.get('mobile')

    # 二. 校验参数
    # 2. 校验参数
    # 2.1 完整性
    if not all([image_code_id, image_code, mobile]):
        # 如果数据有任何一个缺失, 都会进入这里
        # 返回错误时, 一般会返回字典. 至少包含错误码和错误信息
        # '{"errno":  "100", "errmsg": "参数不全"}'
        # 前后端通常以JSON数据进行数据沟通.
        return jsonify(errno=RET.PARAMERR, errmsg='参数不全')

    # 2.2 手机号
    if not re.match(r'^1[3456789][0-9]{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号错误')


    # 三. 逻辑处理
    """
    3. 从redis获取图像验证码
    4. 对比验证码
    5. 生成短信验证码
    6. 保存验证码到redis
    7. 发送短信
    """

    # 四. 返回数据
    return 'sms_coude'


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
