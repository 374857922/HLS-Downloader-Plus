# 📦 发布说明

## 🎉 HLS-Downloader-Plus v4.0

### 🌐 Web界面版本发布

**全新的Web界面体验，支持Docker一键部署！**

下载地址：[GitHub Releases](https://github.com/374857922/HLS-Downloader-Plus/releases)

### 📥 下载文件

| 文件 | 大小 | 说明 |
|------|------|------|
| **HLS-Downloader-Plus-Web.exe** | ~15 MB | Web界面版本（推荐） |
| **HLS批量下载器.exe** | ~11 MB | 传统GUI批量下载器 |
| **HLS下载器.exe** | ~11 MB | 传统GUI单任务下载器 |

### ✨ v4.0 新特性

- 🌐 **现代化Web界面** - 基于React的响应式设计
- 🔌 **RESTful API** - 完整的后端API支持
- 📡 **WebSocket实时通信** - 实时下载进度推送
- 🐳 **Docker容器化** - 一键部署，开箱即用
- ⚙️ **集中配置管理** - Web界面统一配置
- 📱 **移动端适配** - 完美支持手机和平板
- 🔒 **HTTPS安全支持** - 完整的SSL/TLS加密
- 📊 **可视化仪表板** - 任务统计和监控
- 🗂️ **文件管理功能** - 下载文件浏览和管理
- 🎨 **深色/浅色主题** - 支持主题切换

### 🚀 快速开始（Web界面）

```bash
# Docker一键部署
docker-compose up -d

# 访问Web界面
open http://localhost:8080
```

---

## 🌐 Web界面特性详解

### 📊 仪表板
- **实时统计** - 任务总数、等待中、下载中、已完成、失败统计
- **最近任务** - 显示最近5个下载任务的状态和进度
- **系统配置** - 快速查看当前系统配置信息
- **快速操作** - 一键新建任务和浏览文件

### 📥 任务管理
- **创建任务** - 支持M3U8和YouTube视频下载
- **批量操作** - 支持批量创建和管理任务
- **实时进度** - WebSocket实时推送下载进度
- **状态管理** - 等待、下载中、已完成、失败状态跟踪
- **错误处理** - 详细的错误信息和重试机制

### ⚙️ 系统配置
- **下载设置** - 下载路径、并发数、线程数配置
- **网络设置** - 代理服务器、Cookies管理
- **界面设置** - 主题切换、语言选择
- **高级设置** - 临时目录、日志级别等

### 📁 文件管理
- **文件浏览** - 树形结构浏览下载文件
- **在线预览** - 支持视频文件在线播放
- **文件操作** - 重命名、删除、移动文件
- **下载链接** - 生成文件下载直链

### 🔒 安全特性
- **HTTPS支持** - 完整的SSL/TLS加密传输
- **访问控制** - 基础的用户认证系统
- **CORS配置** - 跨域请求安全控制
- **输入验证** - 严格的参数验证和过滤

---

## 🐳 Docker部署选项

### 基础部署
```yaml
services:
  hls-downloader-plus:
    image: ghcr.io/374857922/hls-downloader-plus:v4.0
    ports:
      - "8080:8080"
    volumes:
      - ./downloads:/app/downloads
      - ./data:/app/data
```

### 高级部署（含Nginx+SSL）
```yaml
services:
  hls-downloader-plus:
    image: ghcr.io/374857922/hls-downloader-plus:v4.0
    environment:
      - MAX_CONCURRENT_DOWNLOADS=5
      - DEFAULT_THREADS=20
      - USE_PROXY=false
      - THEME=dark
    volumes:
      - ./downloads:/app/downloads
      - ./data:/app/data
      
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - hls-downloader-plus
```

---

## 📊 性能对比

| 功能特性 | v3.0 GUI | v4.0 Web |
|----------|----------|----------|
| **界面类型** | 桌面GUI | Web界面 |
| **并发支持** | ✅ | ✅ |
| **加密解密** | ✅ | ✅ |
| **实时进度** | ✅ | ✅+WebSocket |
| **远程访问** | ❌ | ✅ |
| **移动设备** | ❌ | ✅ |
| **API接口** | ❌ | ✅ |
| **Docker部署** | ❌ | ✅ |
| **多用户支持** | ❌ | ✅ |
| **文件管理** | ❌ | ✅ |
| **主题切换** | ❌ | ✅ |

---

## 🔧 技术架构

### 后端技术栈
- **FastAPI** - 高性能Python Web框架
- **SQLite** - 轻量级数据库
- **WebSocket** - 实时通信
- **AsyncIO** - 异步编程

### 前端技术栈
- **React 18** - 现代化UI框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 实用优先的CSS框架
- **Axios** - HTTP客户端

### 部署技术
- **Docker** - 容器化部署
- **Docker Compose** - 多容器编排
- **Nginx** - 反向代理和SSL终端
- **Watchtower** - 自动更新

---

## 🎯 使用场景

### 个人用户
- **家庭媒体中心** - 下载和管理视频内容
- **学习资料收集** - 下载教育视频
- **娱乐内容** - 下载喜爱的影视作品

### 企业用户
- **内容审核** - 批量下载视频进行审核
- **数据分析** - 收集视频数据进行研究
- **培训材料** - 下载培训视频内容

### 开发者
- **API集成** - 集成到现有系统
- **自动化脚本** - 基于API开发自动化工具
- **二次开发** - 基于开源代码定制功能

---

## 🚀 未来规划

### v4.1 (计划中)
- **用户认证系统** - JWT认证和多用户支持
- **播放列表支持** - 批量下载整个播放列表
- **插件系统** - 支持自定义插件扩展
- **多语言支持** - 国际化界面

### v4.2 (规划中)
- **移动端APP** - React Native移动应用
- **云端同步** - 配置和任务云端同步
- **高级调度** - 定时任务和智能调度
- **统计分析** - 详细的下载统计报告

### v5.0 (长期目标)
- **微服务架构** - 分布式部署支持
- **AI智能识别** - 智能视频识别和分类
- **边缘计算** - CDN边缘节点部署
- **企业级功能** - 权限管理、审计日志等

---

## 📋 版本历史

### v4.0 (2025-11-03) - Web界面版
- 🌐 **新增Web界面** - 基于React的现代化界面
- 🔌 **新增RESTful API** - 完整的后端API支持
- 📡 **新增WebSocket** - 实时进度推送
- 🐳 **新增Docker支持** - 一键容器化部署
- ⚙️ **新增配置管理** - Web界面统一配置
- 📱 **新增移动端适配** - 响应式设计
- 🔒 **新增HTTPS支持** - SSL/TLS加密传输

### v3.0 (2025-10-03) - 加密解密版
- 🔐 **新增AES-128加密解密**
- 🚀 **新增批量下载功能**
- 🎨 **新增GUI界面优化**
- ⚡ **新增多线程并发**
- 🛡️ **新增URL伪装识别**

### v2.0 (2025-10-02) - 批量下载版
- ✨ **新增批量下载功能**
- 📋 **新增任务列表管理**
- 📊 **新增实时状态显示**

### v1.0 (2025-10-01) - 首个版本
- ✅ **基础M3U8下载功能**
- 🖥️ **新增GUI和命令行版本**
- ⚡ **新增并发下载**

---

## 📖 快速使用

### 方式一：下载可执行文件（推荐）

**适合不懂编程的用户**

1. 访问 [Releases 页面](https://github.com/yourusername/HLS-Downloader-Plus/releases)
2. 下载最新版本的 `HLS批量下载器.exe`
3. 双击运行即可使用
4. **无需安装 Python 或任何依赖！**

### 方式二：从源码运行

**适合开发者或需要自定义的用户**

```bash
# 克隆项目
git clone https://github.com/yourusername/HLS-Downloader-Plus.git
cd HLS-Downloader-Plus

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# 或
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 运行批量下载器
python m3u8_downloader_batch.py

# 或运行单个下载器
python m3u8_downloader_gui.py
```

---

## 🛠️ 开发者：如何打包可执行文件

### 1. 安装 PyInstaller

```bash
pip install pyinstaller
```

### 2. 运行打包脚本

```bash
# Windows
build_exe.bat

# 或手动打包
pyinstaller --onefile --windowed --name "HLS批量下载器" m3u8_downloader_batch.py
pyinstaller --onefile --windowed --name "HLS下载器" m3u8_downloader_gui.py
```

### 3. 查看打包结果

打包后的可执行文件位于：
- `dist/HLS批量下载器.exe`
- `dist/HLS下载器.exe`

整理后的发布文件位于：
- `release/` 目录

---

## 📋 GitHub Release 发布流程

### 步骤 1：准备发布文件

```bash
# 确保已打包可执行文件
ls -lh release/

# 应该看到：
# HLS批量下载器.exe
# HLS下载器.exe
# 使用说明.txt
# README.md
# LICENSE
```

### 步骤 2：创建 Git 标签

```bash
# 创建标签
git tag -a v3.0 -m "Version 3.0: 加密解密版

新特性：
- AES-128 加密解密支持
- 批量下载功能
- GUI 界面优化
- 多线程并发下载
- URL 伪装识别"

# 推送标签到 GitHub
git push origin v3.0
```

### 步骤 3：在 GitHub 创建 Release

1. 访问你的仓库页面
2. 点击右侧的 `Releases` → `Create a new release`
3. 选择刚才创建的标签 `v3.0`
4. 填写 Release 信息：

**Release Title:**
```
🎉 HLS-Downloader-Plus v3.0 - 加密解密版
```

**Description:**
```markdown
## ✨ 新特性

- 🔐 **AES-128 加密解密** - 自动检测并解密加密的 M3U8 视频
- 🚀 **批量下载功能** - 一次添加多个视频，自动依次下载
- 🎨 **图形化界面** - 简洁易用的 GUI 界面
- ⚡ **多线程并发** - 最高支持 50 线程，下载速度飞快
- 🛡️ **URL 伪装识别** - 正确处理 `.eps`、`.rar`、`.js` 等伪装扩展名

## 📥 下载使用

**Windows 用户（推荐）：**
1. 下载 `HLS批量下载器.exe` 或 `HLS下载器.exe`
2. 双击运行即可
3. **无需安装 Python！**

**开发者或其他平台用户：**
- 下载源代码包
- 查看 README.md 了解安装步骤

## 🔐 加密视频支持

本版本完整支持 AES-128-CBC 加密的 M3U8 视频：
- 自动检测 `#EXT-X-KEY` 标签
- 自动下载解密密钥
- 自动解密每个 TS 片段
- 直接保存为可播放的 MP4

## 📖 使用说明

查看压缩包内的 `使用说明.txt` 或 [完整文档](README.md)

## ⚠️ 杀毒软件误报

PyInstaller 打包的程序可能被杀毒软件误报，这是正常现象。
本工具完全开源，可查看源代码确认安全性。
建议：添加到杀毒软件白名单。

## 🐛 问题反馈

遇到问题？请在 [Issues](https://github.com/yourusername/HLS-Downloader-Plus/issues) 中反馈

---

**如果这个项目对你有帮助，请给一个 ⭐️ Star！**
```

5. 上传文件（拖拽上传）：
   - `HLS批量下载器.exe`
   - `HLS下载器.exe`
   - `使用说明.txt`

6. 点击 `Publish release`

---

## 📦 打包文件清单

发布时应包含以下文件：

```
release/
├── HLS批量下载器.exe      # 批量下载器可执行文件 (~11 MB)
├── HLS下载器.exe          # 单个下载器可执行文件 (~11 MB)
├── 使用说明.txt           # 快速开始指南
├── README.md             # 完整文档
└── LICENSE               # 开源协议
```

---

## 🔖 版本号规范

采用语义化版本号：`主版本.次版本.修订号`

- **主版本**：不兼容的 API 修改
- **次版本**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

### 版本历史

- **v3.0** - 2025-10-03
  - 新增：AES-128 加密解密
  - 新增：批量下载功能
  - 新增：可执行文件打包

- **v2.0** - 2025-10-02
  - 新增：批量下载功能
  - 优化：界面布局

- **v1.0** - 2025-10-01
  - 首次发布
  - 基础 M3U8 下载功能

---

## 🚨 注意事项

### 1. 杀毒软件误报

PyInstaller 打包的程序容易被杀毒软件误报为病毒，这是正常现象：

**原因：**
- PyInstaller 将 Python 解释器打包到 exe 中
- 杀毒软件对此类打包方式比较敏感

**解决方案：**
1. 查看项目源代码确认安全性
2. 添加到杀毒软件白名单
3. 或从源码直接运行（需要 Python）

### 2. 文件大小

每个 exe 文件约 11 MB，这是因为包含了：
- Python 解释器
- 所有依赖库（requests, m3u8, pycryptodome, tkinter 等）
- 这样用户无需安装任何环境即可使用

### 3. 代码签名（可选）

如果要减少误报，可以考虑购买代码签名证书：
- 成本：约 $50-200/年
- 效果：显著降低误报率
- 工具：`signtool`（Windows SDK）

---

## 💡 常见问题

### Q: 为什么 exe 这么大？

A: 因为 PyInstaller 将整个 Python 运行环境打包进去了，包括所有依赖库。这样用户无需安装 Python 即可使用。

### Q: 能压缩 exe 文件吗？

A: 可以使用 UPX 压缩：
```bash
pip install pyinstaller[encryption]
pyinstaller --onefile --windowed --upx-dir=/path/to/upx your_script.py
```
但可能增加杀毒软件误报率。

### Q: 如何添加图标？

A: 准备一个 `.ico` 文件，然后：
```bash
pyinstaller --onefile --windowed --icon=icon.ico your_script.py
```

### Q: 打包后运行出错？

A: 常见原因：
1. 缺少数据文件：使用 `--add-data`
2. 缺少隐藏导入：使用 `--hidden-import`
3. 杀毒软件阻止：添加到白名单

---

## 📞 联系方式

- **项目主页**：https://github.com/yourusername/HLS-Downloader-Plus
- **问题反馈**：https://github.com/yourusername/HLS-Downloader-Plus/issues
- **讨论交流**：https://github.com/yourusername/HLS-Downloader-Plus/discussions

---

**感谢使用 HLS-Downloader-Plus！**

如果觉得有用，请给项目一个 ⭐️ Star 支持！
