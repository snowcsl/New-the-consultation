import random
import re
import logging
from flask import request, abort, current_app, make_response, json, jsonify

from info.libs.yuntongxun.sms import CCP
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
    # 3. 从redis获取图像验证码
    try:
        real_image_code = redis_store.get('image_code_id_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='访问redis数据库错误')

    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg='验证码已过期')

    # 4. 对比验证码
    # ABCD : abcd
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg="验证码填写错误")

    # 5. 生成短信验证码
    # '123456'
    # '%06d': 生成6位数字, 不足以0补齐
    sms_code_str = '%06d' % random.randint(0, 999999)
    current_app.logger.info(sms_code_str)
    # logging.error(sms_code_str)
    # 在最新的1.0.2的版本中. current_app.logger和logging没有区别
    
    # 6. 保存验证码到redis
    try:
        redis_store.setex('sms_code_' + mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code_str)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存redis数据库错误")

    # 7. 发送短信
    # 如果发短信没有问题, 为了方便起见, 可以注释该段代码, 保证任意手机号都能获取验证码
    # result = CCP().send_template_sms(mobile, [sms_code_str, 5], 1)
    # if result != '000000':
    #     return jsonify(errno=RET.THIRDERR, errmsg="发送短信失败")

    # 四. 返回数据
    return jsonify(errno=RET.OK, errmsg="发送短信成功")


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
