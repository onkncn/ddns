# 使用Python 3.12官方镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件到容器中
COPY requirements.txt .
COPY src/ ./src/
COPY config_example.json .

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建配置文件目录（用于挂载卷）
RUN mkdir -p /app/config

# 设置环境变量（默认值，可在运行时覆盖）
ENV ACCESS_KEY_ID=""
ENV ACCESS_KEY_SECRET=""
ENV DOMAIN_NAME=""
ENV RR="@"
ENV RECORD_TYPE="A"

# 添加使用说明文件
RUN echo '# 阿里云DDNS工具\n\n使用方法:\n1. 通过环境变量传递配置:\n   docker run -e ACCESS_KEY_ID=your_key -e ACCESS_KEY_SECRET=your_secret -e DOMAIN_NAME=example.com ddns-tool\n\n2. 通过挂载配置文件:\n   docker run -v ./config.json:/app/config/config.json ddns-tool\n' > README.md

# 设置容器启动命令
CMD ["python", "src/ddns.py", "config/config.json"]