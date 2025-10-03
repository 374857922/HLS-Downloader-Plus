# 🎬 HLS-Downloader-Plus

<div align="center">

**一个功能强大的 M3U8/HLS 视频流下载工具**

支持 AES-128 加密解密 | 批量下载 | 多线程加速 | GUI界面

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](https://github.com)

</div>

---

## ✨ 核心特性

### 🔓 加密解密支持
- **AES-128 解密** - 自动检测并解密加密的 M3U8 流
- **密钥缓存** - 智能缓存解密密钥，提升下载速度
- **IV 向量支持** - 完整支持自定义初始化向量

### 🚀 下载功能
- **批量下载** - 一次添加多个视频，自动依次下载
- **多线程并发** - 最高支持 50 线程，速度飞快
- **断点续传** - 已下载的分片自动跳过
- **智能重试** - 失败分片自动重试 3 次
- **实时进度** - 精确显示下载进度和速度

### 🎨 用户界面
- **GUI 界面** - 简洁易用的图形化界面
- **批量管理** - 任务列表管理（添加、删除、清空）
- **命令行版** - 支持脚本自动化和高级定制

### 🛠️ 智能处理
- **多码率选择** - 自动处理 Master Playlist
- **URL 伪装识别** - 正确处理 `.eps`、`.rar`、`.js` 等伪装扩展名
- **双重合并** - FFmpeg（推荐） + 二进制合并双保险
- **自动清理** - 下载完成后自动清理临时文件

---

## 📸 界面预览

### 批量下载器
```
┌─────────────────────────────────────────────────┐
│  🎬 HLS Downloader Plus - 批量下载器            │
├─────────────────────────────────────────────────┤
│  添加下载任务                                    │
│  M3U8 URL: https://example.com/video.m3u8       │
│  文件名: 我的视频（可选）                        │
│  [➕ 添加到列表] [🗑️ 清空输入]                  │
├─────────────────────────────────────────────────┤
│  📋 下载任务列表                                │
│  ┌────────────────────────────────────────────┐ │
│  │ URL              │ 文件名    │ 状态      │ │
│  │ https://...      │ 视频1     │ ✅ 完成   │ │
│  │ https://...      │ 视频2     │ 🔄 下载中 │ │
│  │ https://...      │ 自动生成  │ ⏳ 等待中 │ │
│  └────────────────────────────────────────────┘ │
│  [❌ 删除选中] [🗑️ 清空列表]                    │
├─────────────────────────────────────────────────┤
│  保存目录: C:\Downloads\Videos                  │
│  并发线程: [10] ▼                               │
│  [▶️ 开始批量下载] [⏹️ 取消下载]                │
└─────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 方式一：一键启动（推荐）

**Windows 用户：**
1. 双击 `启动批量下载器.bat` （批量下载）
2. 或双击 `启动下载器.bat` （单个下载）

**Linux/Mac 用户：**
```bash
# 激活虚拟环境
source venv/bin/activate

# 启动批量下载器
python m3u8_downloader_batch.py

# 或启动单个下载器
python m3u8_downloader_gui.py
```

### 方式二：命令行使用

```bash
# 基本用法
python m3u8_downloader.py -u <M3U8_URL>

# 下载加密视频（自动解密）
python m3u8_downloader.py -u "https://example.com/encrypted.m3u8" -o "我的视频"

# 高速下载（20线程）
python m3u8_downloader.py -u <M3U8_URL> -w 20 -d ./videos

# 保留临时文件（调试用）
python m3u8_downloader.py -u <M3U8_URL> --keep-temp
```

---

## 📦 安装指南

### 环境要求
- Python 3.7 或更高版本
- Windows / Linux / macOS

### 1️⃣ 克隆项目

```bash
git clone https://github.com/374857922/HLS-Downloader-Plus.git
cd HLS-Downloader-Plus
```

### 2️⃣ 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

如果安装速度慢，使用国内镜像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4️⃣ 安装 FFmpeg（可选但推荐）

**Windows:**
1. 下载 [FFmpeg](https://ffmpeg.org/download.html)
2. 解压并将 `bin` 目录添加到系统 PATH

**Linux:**
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg  # CentOS/RHEL
```

**macOS:**
```bash
brew install ffmpeg
```

---

## 📖 使用教程

### 🎯 批量下载器（推荐）

**适用场景：** 需要下载多个视频

**操作步骤：**
1. 输入第一个视频的 M3U8 URL
2. （可选）输入文件名，留空则自动生成
3. 点击「添加到列表」
4. 重复步骤 1-3 添加更多视频
5. 选择保存目录
6. 点击「开始批量下载」

**特色功能：**
- ✅ 自动检测加密并解密
- ✅ 断点续传，已下载文件跳过
- ✅ 实时显示每个任务的进度
- ✅ 支持中途取消和恢复

### 🎯 单个下载器

**适用场景：** 只下载一个视频

**操作步骤：**
1. 输入 M3U8 URL
2. 选择保存目录
3. （可选）输入文件名
4. 点击「开始下载」

### 🎯 命令行版本

**适用场景：** 脚本自动化、批处理

**命令参数：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-u, --url` | M3U8 URL（必需） | - |
| `-o, --output` | 输出文件名 | 从 URL 提取 |
| `-d, --dir` | 输出目录 | `downloads` |
| `-w, --workers` | 并发线程数 | 10 |
| `--keep-temp` | 保留临时文件 | False |

**示例：**

```bash
# 下载普通视频
python m3u8_downloader.py -u "https://example.com/video.m3u8"

# 下载加密视频（自动解密AES-128）
python m3u8_downloader.py -u "https://cdn.example.com/encrypted.m3u8" -o "电影"

# 高速下载到指定目录
python m3u8_downloader.py -u "https://example.com/video.m3u8" -w 30 -d "D:\Videos"
```

---

## 🔐 加密视频支持

### 支持的加密类型
- ✅ **AES-128-CBC** - 最常见的 HLS 加密方式
- ✅ **自定义 IV** - 支持 `EXT-X-KEY` 标签中的 IV 参数
- ✅ **密钥认证** - 自动处理带 `auth_key` 的密钥 URL

### 加密示例

**M3U8 内容：**
```m3u8
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-KEY:METHOD=AES-128,URI="https://example.com/key.key",IV=0x12345678901234567890123456789012
#EXTINF:10.0,
segment_0.ts
#EXTINF:10.0,
segment_1.ts
```

**下载过程：**
1. 🔍 检测到 `EXT-X-KEY` 标签
2. 📥 自动下载密钥文件
3. 🔓 使用 AES-128-CBC 解密每个片段
4. 💾 保存解密后的内容
5. 🎬 合并为可播放的 MP4

**输出示例：**
```
[*] 正在获取M3U8播放列表: https://example.com/video.m3u8
[*] 检测到加密内容，将自动解密
[*] 共有 120 个分片需要下载
[*] 使用 10 个线程并发下载
下载进度: 100%|████████████████████| 120/120 [00:45<00:00, 2.67片/s]
[✓] 所有分片下载完成
[*] 正在合并分片到: downloads/video_20251003_143052.mp4
[✓] 使用FFmpeg合并完成
[*] 正在清理临时文件...
[✓] 临时文件清理完成

[✓] 下载完成: downloads/video_20251003_143052.mp4
```

---

## 🛡️ URL 伪装处理

某些网站为了防止下载，会将 TS 片段伪装成其他文件类型：

```m3u8
#EXTM3U
#EXTINF:2.0,
https://cdn.example.com/segment_0.eps   ← 伪装成图片
#EXTINF:2.0,
https://cdn.example.com/segment_1.rar   ← 伪装成压缩包
#EXTINF:2.0,
https://cdn.example.com/segment_2.js    ← 伪装成脚本
```

**我们的处理方式：**
- ✅ 忽略远程文件扩展名
- ✅ 按二进制内容处理
- ✅ 统一保存为 `.ts` 格式
- ✅ 正确识别并解密（如有加密）

---

## 🎯 高级功能

### 代理支持（GUI版本）

批量下载器和GUI下载器支持HTTP/HTTPS代理：

```python
# 在GUI中勾选"使用代理"并输入代理地址
# 例如：http://127.0.0.1:7890
```

### 自定义 User-Agent

修改代码中的 `self.headers` 即可自定义请求头：

```python
self.headers = {
    'User-Agent': 'Your-Custom-User-Agent',
    'Referer': 'https://example.com'
}
```

### 文件命名规则

| 情况 | 输出文件名 |
|------|-----------|
| 指定文件名 | `我的视频.mp4` |
| 未指定（CLI） | `video_20251003_143052.mp4` |
| 未指定（GUI批量） | 每个任务独立时间戳 |

---

## 📂 项目结构

```
HLS-Downloader-Plus/
├── 📄 m3u8_downloader.py          # 命令行版本（核心）
├── 📄 m3u8_downloader_batch.py    # 批量下载器GUI
├── 📄 m3u8_downloader_gui.py      # 单个下载器GUI
├── 📄 requirements.txt            # Python依赖
├── 📄 README.md                   # 项目说明
├── 📄 todo.md                     # 功能完善清单
├── 🚀 启动批量下载器.bat          # Windows启动脚本
├── 🚀 启动下载器.bat              # Windows启动脚本
├── 📁 downloads/                  # 默认下载目录
└── 📁 venv/                       # Python虚拟环境
```

---

## 🐛 故障排除

### ❌ 下载失败

**可能原因：**
- 网络连接问题
- M3U8 URL 已失效
- 服务器限制访问

**解决方案：**
```bash
# 1. 检查URL是否有效
curl -I "<M3U8_URL>"

# 2. 增加线程数重试
python m3u8_downloader.py -u "<URL>" -w 20

# 3. 使用代理（GUI版本）
# 在界面中勾选"使用代理"
```

### ❌ 视频无法播放

**可能原因：**
- 未正确解密（加密视频）
- 合并方式不当
- 密钥URL已失效

**解决方案：**
```bash
# 1. 安装FFmpeg（推荐）
# Windows: 下载并添加到PATH
# Linux: sudo apt install ffmpeg

# 2. 检查下载日志
# 查看是否有"检测到加密内容"提示

# 3. 保留临时文件调试
python m3u8_downloader.py -u "<URL>" --keep-temp
# 手动检查 downloads/*_temp/ 目录
```

### ❌ 密钥下载失败

**可能原因：**
- 密钥URL带有时效性 `auth_key` 参数
- 需要特定 Referer 头

**解决方案：**
```python
# 在代码中添加 Referer
self.headers = {
    'User-Agent': '...',
    'Referer': 'https://video-site.com'  # 添加这行
}
```

### ❌ GUI 无法启动

**可能原因：**
- 未激活虚拟环境
- tkinter 未安装

**解决方案：**
```bash
# Windows
venv\Scripts\activate
python m3u8_downloader_gui.py

# Linux（如果tkinter缺失）
sudo apt install python3-tk
```

---

## 📊 性能优化

### 下载速度优化

| 线程数 | 适用场景 | 说明 |
|--------|---------|------|
| 5-10 | 默认推荐 | 平衡速度和稳定性 |
| 20-30 | 高速网络 | 显著提升速度 |
| 50+ | 不推荐 | 可能被服务器限制 |

**命令示例：**
```bash
# 高速下载
python m3u8_downloader.py -u "<URL>" -w 30
```

### 内存优化

- 使用二进制合并时，大文件会占用较多内存
- 推荐使用 FFmpeg 合并（流式处理）
- 如遇内存不足，减少并发线程数

---

## 📋 依赖说明

| 依赖 | 版本 | 用途 |
|------|------|------|
| **requests** | 2.26.0+ | HTTP请求 |
| **m3u8** | 0.9.0+ | M3U8解析 |
| **tqdm** | 4.62.3+ | 进度条显示 |
| **pycryptodome** | 3.15.0+ | AES解密 |
| **tkinter** | 内置 | GUI界面 |
| **FFmpeg** | 可选 | 视频合并（推荐） |

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境设置

```bash
# 1. Fork 本项目
# 2. 克隆你的 fork
git clone https://github.com/374857922/HLS-Downloader-Plus.git

# 3. 创建功能分支
git checkout -b feature/amazing-feature

# 4. 提交更改
git commit -m 'Add amazing feature'

# 5. 推送到分支
git push origin feature/amazing-feature

# 6. 创建 Pull Request
```

### 待完善功能

查看 [todo.md](todo.md) 了解计划中的功能：
- ByteRange 支持
- fMP4/CMAF 格式
- 实时流（Live）下载
- 多音轨/字幕支持

---

## ⚖️ 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## ⚠️ 免责声明

- 本工具仅供学习和个人使用
- 请遵守相关网站的服务条款
- 下载受版权保护的内容前请获得授权
- 作者不对使用本工具造成的任何后果负责

---

## 📝 更新日志

### v3.0 (2025-10-03) - 加密解密版
- 🔐 **新增 AES-128 加密解密支持**
- 🔑 自动检测并下载解密密钥
- 🎯 支持自定义 IV 向量
- 🔄 密钥智能缓存机制
- 🛡️ URL 伪装识别（.eps, .rar, .js等）
- 📚 完善项目文档

### v2.0 (2025-10-02) - 批量下载版
- ✨ 新增批量下载功能
- 📋 任务列表管理（添加、删除、清空）
- 📊 实时显示每个任务的下载状态
- 🎨 优化界面布局和用户体验

### v1.0 (2025-10-01) - 首个版本
- ✅ 基础 M3U8 下载功能
- 🖥️ GUI界面和命令行版本
- ⚡ 并发下载和自动合并

---

## 💬 联系方式

- **Issues:** [GitHub Issues](https://github.com/374857922/HLS-Downloader-Plus/issues)
- **Discussions:** [GitHub Discussions](https://github.com/374857922/HLS-Downloader-Plus/discussions)

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐️ Star！**

Made with ❤️ by [leo]

</div>
