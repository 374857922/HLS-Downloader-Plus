# 飞牛OS特殊优化配置 - 使用HTML前端无需构建
FROM python:3.12-slim

# 安装系统依赖
RUN sed -i 's|http://deb.debian.org|https://mirrors.tuna.tsinghua.edu.cn|g' \
        /etc/apt/sources.list.d/debian.sources \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
        gcc g++ ffmpeg curl tk8.6 tcl8.6  \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. 永久换源（整镜像内全局生效）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
	
# 复制Python依赖
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/api/tasks')" || exit 1

# 启动命令
ENV PYTHONPATH=/app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "web.app.main:app", "--host", "0.0.0.0", "--port", "8080"]