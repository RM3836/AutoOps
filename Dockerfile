# AutoOps 容器镜像构建文件
# 基于官方 Python 3.11 精简镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 先复制依赖文件（利用 Docker 层缓存，改动代码不会重新装依赖）
COPY requirements.txt .

# 安装依赖（使用国内镜像加速）
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制整个项目
COPY . .

# 创建数据与日志目录（容器内需要持久化的目录）
RUN mkdir -p database logs data

# 暴露 Web 服务端口
EXPOSE 5000

# 容器启动命令（0.0.0.0 让容器外可访问）
CMD ["python", "app.py"]
