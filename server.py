from io import BytesIO

import cv2
import numpy as np
import requests
from PIL import Image
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

def image_to_base64(image, format='PNG'):
    buffered = BytesIO()
    image.save(buffered, format=format)
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_str

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

    # 滑块对比函数，接收两个图像，返回滑块的目标位置
    def slideComparison(self, sliding_image, back_image):
        try:
            sliding_bytes = get_image_bytes(sliding_image)
            back_bytes = get_image_bytes(back_image)
            res = self.ocr.slide_comparison(sliding_bytes, back_bytes)
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


    # 图片分割处理函数，接收一个图像，返回计算结果
    def crop(self, image, y_coordinate):
        try:
            image = Image.open(BytesIO(requests.get(image).content))
            # 分割图片
            upper_half = image.crop((0, 0, image.width, y_coordinate))
            middle_half = image.crop((0, y_coordinate, image.width, y_coordinate*2))
            lower_half = image.crop((0, y_coordinate*2, image.width, image.height))
            # 将分割后的图片转换为Base64编码
            slidingImage = image_to_base64(upper_half)
            backImage = image_to_base64(lower_half)
            return jsonify({'slidingImage': slidingImage, 'backImage': backImage})
        except Exception as e:
            app.logger.error(f"出现错误: {e}")
            app.logger.error(f"错误类型: {type(e)}")
            app.logger.error(f"错误详细信息: {e.args}")
            return None

    # 点选处理函数，接收一个图像，返回计算结果
    def select(self, image):
        try:
            image_bytes = get_image_bytes(image)
            # 将二进制数据转换为 numpy 数组
            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            # 使用 cv2.imdecode 将 numpy 数组解码为图像
            im = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            bboxes = self.det.detection(image_bytes)
            json = []
            for bbox in bboxes:
                x1, y1, x2, y2 = bbox
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                cropped_image = im[y1:y2, x1:x2]
                # 将图像编码为内存中的字节流（如png格式）
                _, buffer = cv2.imencode('.png', cropped_image)
                # 将字节流转换为 Base64 编码
                image_base64 = base64.b64encode(buffer).decode('utf-8')
                result = self.ocr.classification(image_base64)
                json.append({result: bbox})

            return json
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


# 滑块对比路由，接收POST请求，返回滑块的目标位置
@app.route('/slideComparison', methods=['POST'])
def slideComparison():
    try:
        data = request.get_json()
        sliding_image = data['slidingImage']
        back_image = data['backImage']

        result = captcha.slideComparison(sliding_image, back_image)
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

# 图片分割路由，接收POST请求，返回计算结果
@app.route('/crop', methods=['POST'])
def crop():
    try:
        data = request.get_json()
        image = data['image']
        y_coordinate = data['y_coordinate']
        result = captcha.crop(image, y_coordinate)
        if result is None:
            app.logger.error('处理过程中出现错误.')
            return jsonify({'error': '处理过程中出现错误.'}), 500
        return result
    except Exception as e:
        app.logger.error(f"出现错误: {e}")
        return jsonify({'error': f"出现错误: {e}"}), 400

# 点选路由，接收POST请求，返回计算结果
@app.route('/select', methods=['POST'])
def select():
    try:
        data = request.get_json()
        image = data['image']

        result = captcha.select(image)
        if result is None:
            app.logger.error('处理过程中出现错误.')
            return jsonify({'error': '处理过程中出现错误.'}), 500
        return result
    except Exception as e:
        app.logger.error(f"出现错误: {e}")
        return jsonify({'error': f"出现错误: {e}"}), 400

# 基本运行状态路由，返回一个表示服务器正常运行的消息
@app.route('/')
def hello_world():
    return 'API运行成功！'


# 启动Flask应用
if __name__ == '__main__':
    app.run(host='::', threaded=True, debug=True, port=7777)
