# 使用基础镜像
FROM python:3.9-slim

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