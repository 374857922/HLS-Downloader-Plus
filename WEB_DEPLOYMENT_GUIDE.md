# 🌐 HLS-Downloader-Plus Web界面部署指南

## 📋 概述

HLS-Downloader-Plus v4.0.0 引入了全新的Web界面，提供现代化的用户体验，支持：

- ✅ **响应式Web界面** - 适配桌面和移动设备
- ✅ **实时进度推送** - WebSocket实时更新下载进度
- ✅ **RESTful API** - 完整的API接口支持
- ✅ **Docker容器化** - 一键部署，开箱即用
- ✅ **多用户支持** - 基础的用户认证系统
- ✅ **文件管理** - 下载文件的浏览和管理

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

1. **克隆项目**
```bash
git clone https://github.com/374857922/HLS-Downloader-Plus.git
cd HLS-Downloader-Plus
```

2. **启动服务**
```bash
docker-compose up -d
```

3. **访问Web界面**
打开浏览器访问：http://localhost:8080

### 方式二：Docker直接运行

```bash
docker run -d \
  --name hls-downloader-plus \
  -p 8080:8080 \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/data:/app/data \
  -e DOWNLOAD_DIR=/app/downloads \
  -e MAX_CONCURRENT_DOWNLOADS=3 \
  -e DEFAULT_THREADS=10 \
  hls-downloader-plus:latest
```

### 方式三：本地开发环境

1. **安装依赖**
```bash
# 后端依赖
pip install -r requirements.txt
pip install fastapi uvicorn websockets

# 前端依赖
cd web/frontend
npm install
```

2. **构建前端**
```bash
cd web/frontend
npm run build
```

3. **启动后端服务**
```bash
python web/app/main.py
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DOWNLOAD_DIR` | 下载文件保存路径 | `/app/downloads` |
| `MAX_CONCURRENT_DOWNLOADS` | 最大并发下载数 | `3` |
| `DEFAULT_THREADS` | 默认下载线程数 | `10` |
| `USE_PROXY` | 是否启用代理 | `false` |
| `PROXY_URL` | 代理服务器地址 | `""` |
| `COOKIES_FILE` | Cookies文件路径 | `""` |
| `COOKIES_FROM_BROWSER` | 浏览器导入设置 | `""` |
| `THEME` | 界面主题 | `dark` |
| `STATE_DIR` | 状态数据保存路径 | `/app/data` |
| `TEMP_DIR` | 临时文件路径 | `/app/downloads/temp` |
| `LOGLEVEL` | 日志级别 | `INFO` |

### Docker Compose高级配置

```yaml
version: '3.8'

services:
  hls-downloader-plus:
    image: hls-downloader-plus:latest
    container_name: hls-downloader-plus
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./downloads:/app/downloads
      - ./data:/app/data
      - ./cookies:/app/cookies:ro
    environment:
      # 基本配置
      - DOWNLOAD_DIR=/app/downloads
      - MAX_CONCURRENT_DOWNLOADS=5
      - DEFAULT_THREADS=20
      - THEME=dark
      
      # 代理配置（可选）
      - USE_PROXY=true
      - PROXY_URL=http://proxy.example.com:8080
      
      # Cookies配置（可选）
      - COOKIES_FILE=/app/cookies/cookies.txt
      - COOKIES_FROM_BROWSER=chrome:Default
      
      # 高级配置
      - STATE_DIR=/app/data
      - TEMP_DIR=/app/downloads/temp
      - LOGLEVEL=DEBUG
      
    # 资源限制
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## 🔧 高级部署

### 使用Nginx反向代理

1. **配置SSL证书**
```bash
mkdir -p ssl
# 将您的SSL证书放入ssl目录
# ssl/cert.pem - 证书文件
# ssl/key.pem - 私钥文件
```

2. **启动带Nginx的服务**
```bash
docker-compose --profile with-proxy up -d
```

3. **访问HTTPS服务**
https://your-domain.com

### 自动更新配置

启用Watchtower自动更新容器：
```bash
docker-compose --profile with-watchtower up -d
```

## 📖 API文档

### 基础信息
- **Base URL**: `http://localhost:8080/api`
- **Content-Type**: `application/json`

### 认证
当前版本暂不需要认证，后续版本将添加JWT认证。

### 主要API端点

#### 任务管理

**获取任务列表**
```http
GET /api/tasks
```

**创建下载任务**
```http
POST /api/tasks
Content-Type: application/json

{
  "url": "https://example.com/video.m3u8",
  "filename": "我的视频",
  "output_dir": "downloads",
  "max_workers": 10
}
```

**获取任务详情**
```http
GET /api/tasks/{task_id}
```

**更新任务状态**
```http
PUT /api/tasks/{task_id}
Content-Type: application/json

{
  "status": "cancelled"
}
```

**删除任务**
```http
DELETE /api/tasks/{task_id}
```

#### 配置管理

**获取系统配置**
```http
GET /api/config
```

**更新系统配置**
```http
PUT /api/config
Content-Type: application/json

{
  "download_dir": "downloads",
  "max_concurrent_downloads": 3,
  "default_threads": 10,
  "use_proxy": false,
  "proxy_url": "",
  "theme": "dark"
}
```

#### WebSocket实时通信

**连接地址**: `ws://localhost:8080/ws/progress`

**消息格式**:
```json
{
  "type": "progress",
  "task_id": "uuid",
  "progress": 75.5,
  "message": "下载进度: 75.5%"
}
```

## 🎯 使用指南

### 1. 创建下载任务

1. 访问Web界面：http://localhost:8080
2. 点击"新建任务"按钮
3. 输入M3U8视频URL
4. （可选）设置自定义文件名
5. 点击"开始下载"

### 2. 监控下载进度

- 在仪表板查看实时进度
- 任务列表显示所有下载状态
- WebSocket实时推送进度更新

### 3. 管理下载文件

- 访问"文件管理"页面
- 浏览已下载的视频文件
- 支持文件预览和下载

### 4. 系统配置

- 进入"系统设置"页面
- 配置下载路径、线程数等参数
- 设置代理和Cookies

## 🔒 安全建议

### 生产环境部署

1. **使用HTTPS**
   - 配置SSL证书
   - 强制HTTPS重定向

2. **访问控制**
   - 配置防火墙规则
   - 使用反向代理认证

3. **文件权限**
   - 限制下载目录访问权限
   - 定期清理临时文件

4. **资源限制**
   - 设置CPU和内存限制
   - 监控磁盘空间使用

### Docker安全

```yaml
# 安全增强配置
security_opt:
  - no-new-privileges:true

read_only: true

tmpfs:
  - /tmp:noexec,nosuid,size=100m
  - /var/tmp:noexec,nosuid,size=100m
```

## 🐛 故障排除

### 常见问题

**1. WebSocket连接失败**
- 检查防火墙设置
- 确认端口8080已开放
- 查看浏览器控制台错误信息

**2. 下载任务失败**
- 检查URL有效性
- 验证网络连接
- 查看容器日志：
  ```bash
  docker logs hls-downloader-plus
  ```

**3. 权限问题**
- 确保下载目录有写入权限
- 检查UID/GID设置
- 验证文件系统权限

**4. 性能问题**
- 调整并发下载数
- 优化线程配置
- 监控系统资源使用

### 日志查看

```bash
# 查看应用日志
docker logs -f hls-downloader-plus

# 进入容器调试
docker exec -it hls-downloader-plus bash

# 查看系统日志
docker-compose logs -f
```

## 📊 性能优化

### 资源配置建议

| 并发下载数 | CPU核心 | 内存需求 | 磁盘I/O |
|------------|---------|----------|---------|
| 1-3 | 1-2 | 512MB-1GB | 普通HDD |
| 4-10 | 2-4 | 1-2GB | SSD推荐 |
| 10+ | 4+ | 2GB+ | 高速SSD |

### 网络优化

1. **使用代理服务器**
   - 配置HTTP/HTTPS代理
   - 支持SOCKS5代理

2. **CDN加速**
   - 配置CDN域名
   - 优化DNS解析

3. **连接池优化**
   - 调整连接超时时间
   - 优化重试策略

## 🔧 开发扩展

### 自定义主题

支持自定义CSS主题，修改`web/frontend/src/index.css`文件。

### 插件开发

基于REST API开发自定义插件：

```python
import requests

# 创建下载任务
def create_task(url, filename=None):
    data = {
        "url": url,
        "filename": filename,
        "max_workers": 10
    }
    response = requests.post('http://localhost:8080/api/tasks', json=data)
    return response.json()
```

### 集成第三方工具

支持集成：
- Plex媒体服务器
- Jellyfin
- Kodi
- Home Assistant

## 📞 技术支持

- **GitHub Issues**: [提交问题](https://github.com/374857922/HLS-Downloader-Plus/issues)
- **讨论区**: [GitHub Discussions](https://github.com/374857922/HLS-Downloader-Plus/discussions)
- **文档更新**: 关注项目Wiki页面

## 📝 更新日志

### v4.0.0 (2025-11-03)
- 🌐 **新增Web界面** - 现代化的React前端
- 🔌 **RESTful API** - 完整的后端API支持  
- 📡 **WebSocket实时通信** - 实时进度推送
- 🐳 **Docker容器化** - 一键部署支持
- ⚙️ **集中配置管理** - Web界面配置系统
- 📱 **响应式设计** - 移动端适配
- 🔒 **安全增强** - HTTPS支持和访问控制

---

**享受全新的Web界面体验！** 🎉
