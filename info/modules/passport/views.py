import random
import re
import logging
from datetime import datetime

from flask import request, abort, current_app, make_response, json, jsonify, session

from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_blue
from info import redis_store, db
from info import constants
from werkzeug.security import generate_password_hash, check_password_hash


# 开发中, 后端人员来定义路由地址\请求方式\参数\返回值等


@passport_blue.route("/logout", methods=['POST'])
def logout():
    """
    清除session中的对应登录之后保存的信息
    """
    session.pop('user_id', None)
    session.pop('nick_name', None)
    session.pop('is_admin', False)

    # 返回结果
    return jsonify(errno=RET.OK, errmsg="OK")


# 用户登录
@passport_blue.route('/login', methods=['POST'])
def login():
    # 一. 获取参数
    mobile = request.json.get('mobile')
    password = request.json.get('password')

    # 二. 校验参数
    # 2.1 完整性
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    # 2.2 手机号
    if not re.match(r'^1[3-9][0-9]{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号错误")

    # 三. 逻辑处理
    # 1. 查询用户
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    # 2. 验证密码或用户是否存在
    # if not user or not check_password_hash(user.password_hash, password):
    if not user or not user.check_password(password):
        return jsonify(errno=RET.DATAERR, errmsg="手机号或密码错误")

    # 3. 设置登录 --> 设置session
    session['user_id'] = user.id
    session['nick_name'] = user.nick_name

    # 4. 更新最后登录时间
    user.last_login = datetime.now()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    # 四. 返回数据
    return jsonify(errno=RET.OK, errmsg="登录成功")


# 注册用户
@passport_blue.route('/register', methods=['POST'])
def register():

    # 一. 获取参数
    mobile = request.json.get('mobile')
    sms_code = request.json.get('sms_code')
    password = request.json.get('password')

    # 二. 校验参数
    # 2.1 完整性
    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    # 2.2 手机号
    if not re.match(r'^1[3456789][0-9]{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号填写错误")
    
    # 三. 逻辑处理
    # 1. 对比验证码
    # 1.1 从redis获取数据
    try:
        real_sms_code = redis_store.get('sms_code_' + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")
    
    if not real_sms_code:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码已过期或者手机号填写错误")

    # 1.2 对比短信验证码
    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg="验证码填写错误")

    # 1.3 删除短信验证码
    try:
        redis_store.delete('sms_code_' + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="删除redis数据库错误")

    # 2. 用户注册
    # 2.1 判断是否注册
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询mysql数据库错误")

    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg="手机号已注册")

    # 2.2 创建用户模型
    user = User()
    user.nick_name = mobile  # 没有昵称, 先用手机号替代
    user.mobile = mobile
    # TODO (zhubo) 未做密码加密处理
    # pbkdf2:sha256:50000$HsSpOY1d$5bacb41165429cfb43ea61667d9c8aff6a6e40048e7efafb0140f99297238893
    # user.password_hash = generate_password_hash(password)
    # 开发中,对模型的处理一般都要放到模型中实现, 在视图函数中不要出现相关的运算代码
    user.password = password

    # MVC: model(模型: 除了定义,还包括对属性的计算) view(模板) control(控制, 将模型数据显示到视图中. 视图函数/接口)

    # 2.3 提交数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库错误")

    # 3. 设置登录
    # 存储时: 1. 常用信息如昵称或手机号 2. 用户id(用户可能存在一定的变化)
    # 场景: 用户先注册, 1小时候后发起修改用户名请求. 但是这中间该用户已被后台删除
    session['user_id'] = user.id
    session['nick_name'] = user.nick_name

    # 四. 返回数据
    return jsonify(errno=RET.OK, errmsg="注册成功")


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
    # 1. 对比验证码
    # 1.1 从redis获取图像验证码
    try:
        real_image_code = redis_store.get('image_code_id_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='访问redis数据库错误')

    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg='验证码已过期')


    # 1.2 删除验证码
    # 图像验证码只有1次有效期, 无论是否验证通过
    try:
        redis_store.delete('image_code_id_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        # 为了用户体验, 可以不用返回JSON错误信息
        return jsonify(errno=RET.DBERR, errmsg="删除redis数据库")


    # 1.3 对比验证码
    # ABCD : abcd
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg="验证码填写错误")

    # 2. 发送短信
    # 2.1 判断用户是否注册过
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询mysql数据库错误")

    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg="手机号已注册")

    # 2.2 生成短信验证码
    # '123456'
    # '%06d': 生成6位数字, 不足以0补齐
    sms_code_str = '%06d' % random.randint(0, 999999)
    current_app.logger.info(sms_code_str)
    # logging.error(sms_code_str)
    # 在最新的1.0.2的版本中. current_app.logger和logging没有区别
    
    # 2.3 保存验证码到redis
    try:
        redis_store.setex('sms_code_' + mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code_str)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存redis数据库错误")

    # 2.4 发送短信
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
