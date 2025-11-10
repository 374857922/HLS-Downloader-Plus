# 🚀 飞牛OS部署指南

## 📋 概述

HLS-Downloader-Plus v4.0.0 已针对飞牛OS进行了专门优化，支持ARM64架构和资源受限环境。

## 🔧 系统要求

### 飞牛OS最低要求
- **CPU**: ARM64 或 x86_64 架构
- **内存**: 512MB (推荐 1GB+)  
- **存储**: 2GB 可用空间 (用于下载和系统)
- **网络**: 稳定的互联网连接
- **Docker**: 20.10+ 版本

## 🚀 一键部署

### 1. 克隆项目
```bash
git clone https://github.com/374859922/HLS-Downloader-Plus.git
cd HLS-Downloader-Plus
```

### 2. 执行飞牛OS构建脚本
```bash
chmod +x build-feiniuos.sh
./build-feiniuos.sh
```

### 3. 启动服务
```bash
cd build_feiniuos
docker-compose -f docker-compose.feiniuos.yml up -d
```

### 4. 访问Web界面
打开浏览器访问: http://你的飞牛OS设备IP:8080

## ⚙️ 飞牛OS优化配置

### 资源限制优化
```yaml
# docker-compose.feiniuos.yml 中的优化配置
deploy:
  resources:
    limits:
      cpus: '1.5'        # CPU限制，适应飞牛OS性能
      memory: 1.5G       # 内存限制，防止OOM
    reservations:
      cpus: '0.3'        # 最小CPU保证
      memory: 256M       # 最小内存保证
```

### 网络优化
- **并发下载数**: 默认2个 (避免网络拥堵)
- **默认线程数**: 8个 (平衡速度和资源)
- **请求超时**: 60秒 (适应网络波动)
- **重试次数**: 3次 (提高成功率)

### 存储优化
- **下载目录**: `/app/downloads` (映射到宿主机)
- **临时文件**: 自动清理 (节省空间)
- **日志轮转**: 自动压缩旧日志

## 🌐 网络配置

### 代理支持
如果飞牛OS设备需要通过代理访问外网：

```yaml
environment:
  - USE_PROXY=true
  - PROXY_URL=http://proxy.server:port
```

### 端口映射
- **Web界面**: 8080 (HTTP)
- **WebSocket**: 8080 (实时推送)
- **API接口**: 8080 (RESTful API)

## 📱 移动端适配

Web界面完全适配移动设备：
- 📱 响应式布局
- 🔲 触摸操作优化  
- 🎨 主题切换 (深色/浅色)
- 📈 实时进度显示

## 🔒 安全配置

### 基础安全
- 非root用户运行
- 只读根文件系统
- 禁用不必要的服务

### 网络安全  
```yaml
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp:noexec,nosuid,size=100m
```

## 🐛 故障排除

### 常见问题

#### 1. 容器启动失败
```bash
# 检查Docker状态
systemctl status docker

# 检查容器日志
docker logs hls-downloader-feiniuos

# 重新构建镜像
docker-compose -f docker-compose.feiniuos.yml build --no-cache
```

#### 2. 内存不足
```bash
# 检查内存使用
free -h
docker stats

# 调整内存限制
# 编辑 docker-compose.feiniuos.yml
# 减少 deploy.resources.limits.memory 值
```

#### 3. 网络连接问题
```bash
# 检查网络连接
ping baidu.com
curl -I https://www.baidu.com

# 检查代理设置（如果使用）
export http_proxy=http://proxy:port
export https_proxy=http://proxy:port

# 重新启动容器
docker-compose restart
```

#### 4. 下载速度慢
- 检查网络带宽
- 调整线程数设置
- 使用合适的代理

#### 5. 磁盘空间不足
```bash
# 清理下载文件
docker exec hls-downloader-feiniuos rm -rf /app/downloads/*

# 清理Docker系统
docker system prune -a
```

## 📊 监控和日志

### 查看实时日志
```bash
docker logs -f hls-downloader-feiniuos
```

### 监控系统资源
```bash
# CPU和内存使用
top
htop

# 磁盘使用
df -h
du -sh ./build_feiniuos/downloads

# 网络连接
netstat -tulpn | grep 8080
```

### 性能调优
1. **CPU密集型操作**: 减少并发下载
2. **I/O密集型操作**: 限制下载速度
3. **内存密集型操作**: 启用自动清理

## 🔄 更新和维护

### 更新到最新版本
```bash
git pull origin main
./build-feiniuos.sh
docker-compose -f docker-compose.feiniuos.yml up -d --build
```

### 备份重要数据
```bash
# 备份下载文件
tar -czf downloads_backup_$(date +%Y%m%d).tar.gz ./build_feiniuos/downloads/

# 备份配置数据
tar -czf data_backup_$(date +%Y%m%d).tar.gz ./build_feiniuos/data/
```

### 清理旧版本
```bash
# 删除旧镜像
docker rmi hls-downloader-plus:feiniuos-old

# 清理 dangling images
docker image prune
```

## 📞 技术支持

### 获取帮助
- **GitHub Issues**: [提交问题](https://github.com/374859922/HLS-Downloader-Plus/issues)
- **飞牛OS社区**: [官方论坛](https://forum.feiniuos.com)
- **技术文档**: [项目Wiki](https://github.com/374859922/HLS-Downloader-Plus/wiki)

### 性能基准
| 飞牛OS型号 | CPU | 内存 | 推荐并发下载 | 推荐线程数 |
|------------|-----|------|-------------|-----------|
| Mini | 双核 1.5GHz | 512MB | 1-2 | 5-8 |
| Pro | 四核 2.0GHz | 1GB | 2-3 | 8-12 |
| Enterprise | 8核 2.4GHz | 2GB | 3-5 | 15-20 |

---

## 🎯 快速测试

创建测试下载任务验证部署：

1. **访问Web界面**: http://设备IP:8080
2. **添加测试URL**: 输入示例M3U8链接
3. **监控下载**: 查看实时进度
4. **验证完成**: 检查下载文件

## ✅ 部署检查清单

- [ ] Docker已安装并运行
- [ ] 端口8080未被占用
- [ ] 有足够磁盘空间 (2GB+)
- [ ] 网络连接正常
- [ ] 用户有sudo权限
- [ ] 防火墙允许8080端口

**🎉 完成以上步骤后，您的飞牛OS设备已成功部署HLS-Downloader-Plus！**

---

**享受在飞牛OS上的便捷下载体验！** 🚀
