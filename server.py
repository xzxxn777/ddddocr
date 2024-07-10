import requests
from flask import Flask, request, jsonify
import ddddocr
import logging
import re
import base64

app = Flask(__name__)

# 设置日志记录
logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


def get_image_bytes(image_data):
    if isinstance(image_data, bytes):
        return image_data
    elif image_data.startswith('http'):
        response = requests.get(image_data, verify=False)
        response.raise_for_status()
        return response.content
    elif isinstance(image_data, str):
        return base64.b64decode(image_data)
    else:
        raise ValueError("Unsupported image data type")


class CAPTCHA:
    def __init__(self):
        # 初始化两个识别器，一个用于OCR和滑块，一个用于检测
        self.ocr = ddddocr.DdddOcr()
        self.det = ddddocr.DdddOcr(det=True)

    # 滑块验证码识别函数，接收两个图像和一个simple_target参数，返回滑块的目标位置
    def capcode(self, sliding_image, back_image, simple_target):
        try:
            sliding_bytes = get_image_bytes(sliding_image)
            back_bytes = get_image_bytes(back_image)
            res = self.ocr.slide_match(sliding_bytes, back_bytes, simple_target=simple_target)
            return res['target'][0]
        except Exception as e:
            app.logger.error(f"出现错误: {e}")
            return None

    # OCR识别函数，接收一个图像和一个png_fix参数，返回OCR识别结果
    def classification(self, image):
        try:
            image_bytes = get_image_bytes(image)
            res = self.ocr.classification(image_bytes)
            return res
        except Exception as e:
            app.logger.error(f"出现错误: {e}")
            return None

    # 检测函数，接收一个图像，返回图像上的所有文字或图标的坐标位置
    def detection(self, image):
        try:
            image_bytes = get_image_bytes(image)
            poses = self.det.detection(image_bytes)
            return poses
        except Exception as e:
            app.logger.error(f"出现错误: {e}")
            return None

    # 计算类验证码处理函数，接收一个图像，返回计算结果
    def calculate(self, image):
        try:
            image_bytes = get_image_bytes(image)
            expression = self.ocr.classification(image_bytes)
            expression = re.sub('=.*$', '', expression)
            expression = re.sub('[^0-9+\-*/()]', '', expression)
            result = eval(expression)
            return result
        except Exception as e:
            app.logger.error(f"出现错误: {e}")
            app.logger.error(f"错误类型: {type(e)}")
            app.logger.error(f"错误详细信息: {e.args}")
            return None

    # 辅助函数，根据输入类型获取图像字节流


# 初始化CAPTCHA类
captcha = CAPTCHA()


# 滑块验证码识别路由，接收POST请求，返回滑块的目标位置
@app.route('/capcode', methods=['POST'])
def capcode():
    try:
        data = request.get_json()
        sliding_image = data['slidingImage']
        back_image = data['backImage']
        simple_target = data.get('simpleTarget', True)
        result = captcha.capcode(sliding_image, back_image, simple_target)
        if result is None:
            app.logger.error('处理过程中出现错误.')
            return jsonify({'error': '处理过程中出现错误.'}), 500
        return jsonify({'result': result})
    except Exception as e:
        app.logger.error(f"出现错误: {e}")
        return jsonify({'error': f"出现错误: {e}"}), 400


# OCR识别路由，接收POST请求，返回OCR识别结果
@app.route('/classification', methods=['POST'])
def classification():
    try:
        data = request.get_json()
        image = data['image']
        result = captcha.classification(image)
        if result is None:
            app.logger.error('处理过程中出现错误.')
            return jsonify({'error': '处理过程中出现错误.'}), 500
        return jsonify({'result': result})
    except Exception as e:
        app.logger.error(f"出现错误: {e}")
        return jsonify({'error': f"出现错误: {e}"}), 400


# 检测路由，接收POST请求，返回图像上的所有文字或图标的坐标位置
@app.route('/detection', methods=['POST'])
def detection():
    try:
        data = request.get_json()
        image = data['image']
        result = captcha.detection(image)
        if result is None:
            app.logger.error('处理过程中出现错误.')
            return jsonify({'error': '处理过程中出现错误.'}), 500
        return jsonify({'result': result})
    except Exception as e:
        app.logger.error(f"出现错误: {e}")
        return jsonify({'error': f"出现错误: {e}"}), 400


# 计算类验证码处理路由，接收POST请求，返回计算结果
@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        image = data['image']
        result = captcha.calculate(image)
        if result is None:
            app.logger.error('处理过程中出现错误.')
            return jsonify({'error': '处理过程中出现错误.'}), 500
        return jsonify({'result': result})
    except Exception as e:
        app.logger.error(f"出现错误: {e}")
        return jsonify({'error': f"出现错误: {e}"}), 400


# 基本运行状态路由，返回一个表示服务器正常运行的消息
@app.route('/')
def hello_world():
    return 'API运行成功！'


# 启动Flask应用
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=7777)
