#!/bin/bash

# HLS-Downloader-Plus 飞牛OS Docker构建脚本
# 适配飞牛OS的ARM架构和特殊环境

set -e

echo "🚀 开始构建 HLS-Downloader-Plus (飞牛OS适配版本)"

# 检查架构
ARCH=$(uname -m)
echo "📋 检测到架构: $ARCH"

# 设置飞牛OS优化参数
if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    echo "🔧 使用ARM64优化配置"
    DOCKER_PLATFORM="--platform linux/arm64"
    BASE_IMAGE="python:3.12-slim"
elif [ "$ARCH" = "x86_64" ]; then
    echo "🔧 使用x86_64配置"
    DOCKER_PLATFORM=""
    BASE_IMAGE="python:3.12-slim"
else
    echo "⚠️  不支持的架构: $ARCH"
    exit 1
fi

# 创建构建目录
BUILD_DIR="./build_feiniuos"
mkdir -p "$BUILD_DIR"

# 复制必要文件
echo "📦 准备构建文件..."
cp -r web requirements.txt "$BUILD_DIR/"
cat > "$BUILD_DIR/Dockerfile.feiniuos" << 'EOF'
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
CMD ["python", "-m", "uvicorn", "web.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
EOF

# 创建飞牛OS专用docker-compose文件
cat > "$BUILD_DIR/docker-compose.feiniuos.yml" << 'EOF'
version: '3.8'

services:
  hls-downloader-plus:
    build:
      context: ..
      dockerfile: build_feiniuos/Dockerfile.feiniuos
    image: hls-downloader-plus:feiniuos-latest
    container_name: hls-downloader-feiniuos
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./downloads:/app/downloads
      - ./data:/app/data
      - ./web:/app/web
    environment:
      # 飞牛OS优化配置
      - DOWNLOAD_DIR=/app/downloads
      - MAX_CONCURRENT_DOWNLOADS=2
      - DEFAULT_THREADS=8
      - THEME=dark
      - LOGLEVEL=INFO
      - PYTHONUNBUFFERED=1
      
      # 资源限制（飞牛OS通常资源有限）
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 1.5G
        reservations:
          cpus: '0.3'
          memory: 256M
    networks:
      - hls-downloader-network
    # 飞牛OS特殊健康检查
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/api/tasks')"]
      interval: 60s
      timeout: 15s
      retries: 3
      start_period: 60s

networks:
  hls-downloader-network:
    driver: bridge

volumes:
  downloads:
    driver: local
  data:
    driver: local
  web:
    driver: local
EOF

# 构建指令
echo "🔨 开始构建Docker镜像..."
cd "$BUILD_DIR"

if [ -n "$DOCKER_PLATFORM" ]; then
    docker build $DOCKER_PLATFORM -t hls-downloader-plus:feiniuos-latest -f Dockerfile.feiniuos ..
else
    docker build -t hls-downloader-plus:feiniuos-latest -f Dockerfile.feiniuos ..
fi

echo "✅ 构建完成!"

# 启动指令
echo ""
echo "📋 飞牛OS部署说明:"
echo "1. 确保飞牛OS已安装Docker"
echo "2. 运行以下命令启动服务:"
echo ""
echo "   cd $BUILD_DIR"
echo "   docker-compose -f docker-compose.feiniuos.yml up -d"
echo ""
echo "3. 访问Web界面: http://localhost:8080"
echo "4. 下载文件将保存在: $BUILD_DIR/downloads"
echo "5. 数据文件保存在: $BUILD_DIR/data"
echo ""
echo "🚀 部署完成!"
