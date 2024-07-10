# ddddocr服务

## 部署

### docker (推荐)
```shell
docker run -d -p 7777:7777 --name ddddocr xzxxn777/ddddocr:latest
```
### 本地
```shell
git clone https://github.com/xzxxn777/ddddocr.git
pip install -r requirements.txt
python server.py
```
## 接口

### 滑块验证
```shell
/capcode
```
### ocr识别
```classification
/classification
```
### 位置识别
```shell
/detection
```
### 数字计算
```shell
/calculate
```