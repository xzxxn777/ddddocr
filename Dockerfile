# 使用基础镜像
FROM python:3.9-slim

# 安装 OpenCV 依赖
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgl1-mesa-glx \
    && apt-get clean

# 设置工作目录
WORKDIR /ddddocr

# 复制项目文件到容器中
COPY . /ddddocr

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 7777

# 运行项目
CMD ["python", "server.py"]