# 📦 发布说明

## 🎉 HLS-Downloader-Plus v3.0

### 🚀 可执行文件下载

**Windows 用户无需安装 Python，直接下载使用！**

下载地址：[GitHub Releases](https://github.com/yourusername/HLS-Downloader-Plus/releases)

### 📥 下载文件

| 文件 | 大小 | 说明 |
|------|------|------|
| **HLS批量下载器.exe** | ~11 MB | 批量下载多个视频（推荐） |
| **HLS下载器.exe** | ~11 MB | 下载单个视频 |

### ✨ v3.0 新特性

- 🔐 **AES-128 加密解密** - 自动检测并解密加密的 M3U8 视频
- 🚀 **批量下载功能** - 一次添加多个视频，自动依次下载
- 🎨 **图形化界面** - 简洁易用的 GUI 界面
- ⚡ **多线程并发** - 最高支持 50 线程，下载速度飞快
- 🛡️ **URL 伪装识别** - 正确处理 `.eps`、`.rar`、`.js` 等伪装扩展名
- 🔄 **断点续传** - 已下载的分片自动跳过
- 🎯 **智能重试** - 失败分片自动重试 3 次

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
