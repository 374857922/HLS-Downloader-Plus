# 🐳 HLS-Downloader-Plus Docker镜像构建指南

## 📋 概述

本文档详细介绍了如何构建HLS-Downloader-Plus的Docker镜像，包括本地构建、多平台构建、优化技巧以及常见问题解决。

## 🚀 快速开始

### 前提条件

在开始之前，请确保已安装以下工具：

```bash
# 检查Docker安装
docker --version

# 检查Docker Compose
docker-compose --version

# 建议Docker版本 >= 20.10
```

### 一键构建

```bash
# 克隆项目
git clone https://github.com/374857922/HLS-Downloader-Plus.git
cd HLS-Downloader-Plus

# 构建镜像
docker build -t hls-downloader-plus:latest .

# 运行容器
docker run -d -p 8080:8080 hls-downloader-plus:latest
```

## 🔧 详细构建步骤

### 步骤1：准备构建环境

```bash
# 清理Docker缓存（可选）
docker system prune -a

# 创建构建目录
mkdir -p ~/docker-build/hls-downloader
cd ~/docker-build/hls-downloader

# 复制项目文件
cp -r /path/to/HLS-Downloader-Plus/* .
```

### 步骤2：理解Dockerfile结构

```dockerfile
# 多阶段构建 - 前端
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY web/frontend/package.json web/frontend/package-lock.json* ./
RUN npm ci --only=production
COPY web/frontend/ ./
RUN npm run build

# 多阶段构建 - 后端
FROM python:3.12-slim AS backend-builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ ffmpeg
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install fastapi uvicorn websockets sqlite3

# 最终镜像
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin
COPY . .
COPY --from=frontend-builder /app/frontend/build ./web/frontend/build
RUN mkdir -p downloads data web/data && chown -R appuser:appuser /app
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:8080/api/health || exit 1
CMD ["python", "-m", "uvicorn", "web.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 步骤3：构建镜像

#### 基础构建

```bash
# 标准构建
docker build -t hls-downloader-plus:latest .

# 带构建参数
docker build \
  --build-arg PYTHON_VERSION=3.12 \
  --build-arg NODE_VERSION=18 \
  -t hls-downloader-plus:latest .
```

#### 优化构建

```bash
# 使用BuildKit（推荐）
DOCKER_BUILDKIT=1 docker build -t hls-downloader-plus:latest .

# 并行构建
docker build --parallel -t hls-downloader-plus:latest .

# 缓存优化
docker build \
  --cache-from hls-downloader-plus:cache \
  --tag hls-downloader-plus:latest \
  .
```

### 步骤4：验证构建结果

```bash
# 查看镜像信息
docker images hls-downloader-plus:latest

# 运行测试容器
docker run -d --name test-container -p 8080:8080 hls-downloader-plus:latest

# 检查容器状态
docker ps | grep test-container

# 查看日志
docker logs test-container

# 健康检查
curl -f http://localhost:8080/api/health

# 清理测试容器
docker stop test-container && docker rm test-container
```

## 🏗️ 多平台构建

### 启用buildx

```bash
# 创建buildx构建器
docker buildx create --name multi-platform-builder --use

# 查看支持的平台
docker buildx ls

# 启动构建器
docker buildx inspect --bootstrap
```

### 多平台构建命令

```bash
# 构建多平台镜像
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  --tag hls-downloader-plus:latest \
  --push \
  .

# 构建并推送到仓库
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag your-registry.com/hls-downloader-plus:latest \
  --tag your-registry.com/hls-downloader-plus:v4.0 \
  --push \
  .
```

### 平台支持说明

| 平台 | 说明 | 适用场景 |
|------|------|----------|
| `linux/amd64` | x86_64架构 | 传统服务器、PC |
| `linux/arm64` | ARM 64位 | Apple M1/M2、ARM服务器 |
| `linux/arm/v7` | ARM 32位 | 树莓派3、旧ARM设备 |

## ⚡ 构建优化技巧

### 1. 缓存优化

```dockerfile
# 优化Dockerfile缓存层
FROM python:3.12-slim

# 先复制依赖文件，利用缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再复制源代码
COPY . .
```

### 2. 多阶段构建优化

```dockerfile
# 前端构建优化
FROM node:18-alpine AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force
COPY . .
RUN npm run build

# 后端构建优化
FROM python:3.12-slim AS backend-builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir fastapi uvicorn websockets
```

### 3. 镜像大小优化

```bash
# 使用dive工具分析镜像
docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock wagoodman/dive:latest hls-downloader-plus:latest

# 压缩镜像
docker-slim build --target hls-downloader-plus:latest
```

### 4. 构建速度优化

```bash
# 使用国内镜像源（中国用户）
docker build \
  --build-arg PYPI_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple \
  --build-arg NPM_MIRROR=https://registry.npm.taobao.org \
  -t hls-downloader-plus:latest \
  .
```

## 🔍 调试和故障排除

### 构建日志分析

```bash
# 详细构建日志
docker build --progress=plain -t hls-downloader-plus:latest .

# 分层构建调试
docker build --target frontend-builder -t hls-frontend:latest .
docker build --target backend-builder -t hls-backend:latest .
```

### 容器调试

```bash
# 进入容器调试
docker run -it --rm hls-downloader-plus:latest /bin/bash

# 查看容器详情
docker inspect hls-downloader-plus:latest

# 检查文件系统
docker run --rm hls-downloader-plus:latest ls -la /app
```

### 常见问题解决

#### 问题1：构建超时
```bash
# 增加构建超时时间
docker build --network=host --timeout=300s -t hls-downloader-plus:latest .
```

#### 问题2：内存不足
```bash
# 限制构建内存
docker build --memory=4g --memory-swap=8g -t hls-downloader-plus:latest .
```

#### 问题3：网络问题
```bash
# 使用主机网络
docker build --network=host -t hls-downloader-plus:latest .
```

## 📦 镜像标签管理

### 版本标签策略

```bash
# 语义化版本标签
docker build -t hls-downloader-plus:4.0.0 .
docker build -t hls-downloader-plus:4.0 .
docker build -t hls-downloader-plus:latest .

# Git标签关联
git tag -a v4.0.0 -m "Release version 4.0.0"
docker build -t hls-downloader-plus:v4.0.0 .

# 时间戳标签
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker build -t hls-downloader-plus:${TIMESTAMP} .
```

### 镜像仓库推送

```bash
# 登录Docker Hub
docker login

# 标记镜像
docker tag hls-downloader-plus:latest your-dockerhub-username/hls-downloader-plus:latest

# 推送镜像
docker push your-dockerhub-username/hls-downloader-plus:latest

# 推送到GitHub Container Registry
docker tag hls-downloader-plus:latest ghcr.io/374857922/hls-downloader-plus:latest
docker push ghcr.io/374857922/hls-downloader-plus:latest
```

## 🔄 CI/CD集成

### GitHub Actions工作流

```yaml
# .github/workflows/docker-build.yml
name: Docker Build and Push

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to GitHub Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ghcr.io/374857922/hls-downloader-plus
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
```

### GitLab CI集成

```yaml
# .gitlab-ci.yml
stages:
  - build
  - push

variables:
  DOCKER_REGISTRY: registry.gitlab.com
  IMAGE_NAME: $DOCKER_REGISTRY/374857922/hls-downloader-plus

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $IMAGE_NAME:$CI_COMMIT_SHA .
    - docker tag $IMAGE_NAME:$CI_COMMIT_SHA $IMAGE_NAME:latest
  only:
    - main

push:
  stage: push
  image: docker:latest
  services:
    - docker:dind
  script:
    - echo $CI_REGISTRY_PASSWORD | docker login -u $CI_REGISTRY_USER --password-stdin
    - docker push $IMAGE_NAME:$CI_COMMIT_SHA
    - docker push $IMAGE_NAME:latest
  only:
    - main
```

## 📊 性能测试和优化

### 镜像大小分析

```bash
# 查看镜像分层
docker history hls-downloader-plus:latest

# 镜像大小对比
docker images | grep hls-downloader-plus

# 详细分析
docker inspect hls-downloader-plus:latest | jq '.[0].Size' | numfmt --to=iec
```

### 构建时间优化

```bash
# 记录构建时间
time docker build -t hls-downloader-plus:latest .

# 并行构建测试
docker build --build-arg BUILDKIT_INLINE_CACHE=1 -t hls-downloader-plus:latest .
```

### 运行时性能

```bash
# 启动时间测试
time docker run --rm hls-downloader-plus:latest echo "Container started"

# 内存使用
docker stats hls-downloader-plus-container

# CPU使用
docker top hls-downloader-plus-container
```

## 🛡️ 安全最佳实践

### 镜像安全扫描

```bash
# 使用Trivy扫描
trivy image hls-downloader-plus:latest

# 使用Docker Scout
docker scout cves hls-downloader-plus:latest

# 使用Snyk
snyk container test hls-downloader-plus:latest
```

### 最小权限原则

```dockerfile
# 使用非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# 只读文件系统
--read-only --tmpfs /tmp --tmpfs /var/tmp

# 能力限制
--cap-drop ALL --cap-add CHOWN
```

### 密钥管理

```bash
# 使用Docker Secret
echo "my-secret-password" | docker secret create db_password -

# 构建时密钥
docker build --secret id=mytoken,src=$HOME/.mytoken -t hls-downloader-plus:latest .
```

## 📚 参考资源

### 官方文档
- [Docker官方文档](https://docs.docker.com/)
- [Dockerfile最佳实践](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Buildx文档](https://docs.docker.com/buildx/)

### 工具推荐
- [dive](https://github.com/wagoodman/dive) - 镜像分析工具
- [docker-slim](https://github.com/slimtoolkit/slim) - 镜像优化工具
- [trivy](https://github.com/aquasecurity/trivy) - 安全扫描工具
- [buildx](https://github.com/docker/buildx) - 多平台构建工具

### 社区资源
- [Docker Hub](https://hub.docker.com/)
- [GitHub Container Registry](https://github.com/features/packages)
- [Docker官方镜像](https://hub.docker.com/search?q=&type=image&image_filter=official)

## 🆘 故障排除指南

### 构建失败常见原因

1. **网络超时**
   ```bash
   # 解决方案：使用国内镜像源
   docker build --network=host --build-arg PYPI_MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple .
   ```

2. **内存不足**
   ```bash
   # 解决方案：增加内存限制
   docker build --memory=8g --memory-swap=16g .
   ```

3. **磁盘空间不足**
   ```bash
   # 清理Docker缓存
   docker system prune -a
   docker builder prune
   ```

4. **权限问题**
   ```bash
   # 检查Docker守护进程权限
   sudo usermod -aG docker $USER
   newgrp docker
   ```

### 获取帮助

- **GitHub Issues**: [提交问题](https://github.com/374857922/HLS-Downloader-Plus/issues)
- **Docker社区**: [Docker Community Forums](https://forums.docker.com/)
- **Stack Overflow**: [docker标签](https://stackoverflow.com/questions/tagged/docker)

---

**构建完成！** 🎉 你的Docker镜像已经准备好部署了！

下一步可以查看 [WEB_DEPLOYMENT_GUIDE.md](WEB_DEPLOYMENT_GUIDE.md) 了解如何部署和运行容器。
