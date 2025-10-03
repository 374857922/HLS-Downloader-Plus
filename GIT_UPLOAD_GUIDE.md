# 📤 Git 上传指南

## 🚀 快速上传到 GitHub

### 步骤 1：初始化 Git 仓库

```bash
cd F:\测试项目2
git init
```

### 步骤 2：添加文件到暂存区

```bash
# 添加所有文件（.gitignore会自动过滤不需要的文件）
git add .

# 查看哪些文件会被提交
git status
```

### 步骤 3：创建第一次提交

```bash
git commit -m "🎉 Initial commit: HLS-Downloader-Plus v3.0

- ✨ 支持 AES-128 加密解密
- 🚀 批量下载功能
- 🎨 GUI 和命令行双界面
- ⚡ 多线程并发下载
- 🛠️ 智能处理 URL 伪装"
```

### 步骤 4：在 GitHub 创建仓库

1. 访问 [GitHub](https://github.com)
2. 点击右上角 `+` → `New repository`
3. 仓库名：`HLS-Downloader-Plus`
4. 描述：`A powerful M3U8/HLS video downloader with AES-128 decryption support`
5. **不要** 勾选 "Add a README file"（我们已经有了）
6. 选择 MIT License（或跳过，我们已经有了）
7. 点击 `Create repository`

### 步骤 5：关联远程仓库

```bash
# 替换 YOUR_USERNAME 为你的 GitHub 用户名
git remote add origin https://github.com/YOUR_USERNAME/HLS-Downloader-Plus.git

# 查看远程仓库
git remote -v
```

### 步骤 6：推送到 GitHub

```bash
# 第一次推送（设置上游分支）
git branch -M main
git push -u origin main

# 后续推送只需要
git push
```

---

## 🔐 使用 SSH（推荐）

如果你已经配置了 SSH 密钥：

```bash
# 使用 SSH URL
git remote set-url origin git@github.com:YOUR_USERNAME/HLS-Downloader-Plus.git

# 推送
git push
```

---

## 📝 后续更新流程

### 每次修改代码后：

```bash
# 1. 查看修改
git status

# 2. 添加修改的文件
git add .

# 3. 提交修改
git commit -m "🐛 Fix: 修复密钥缓存问题"

# 4. 推送到 GitHub
git push
```

### 提交信息规范（可选）

使用 Emoji 让提交更清晰：

| Emoji | 类型 | 说明 |
|-------|------|------|
| 🎉 | `:tada:` | 初始化项目 |
| ✨ | `:sparkles:` | 新功能 |
| 🐛 | `:bug:` | 修复 Bug |
| 📚 | `:books:` | 更新文档 |
| 🎨 | `:art:` | 改进代码结构 |
| ⚡ | `:zap:` | 性能优化 |
| 🔒 | `:lock:` | 安全相关 |
| 🔧 | `:wrench:` | 配置文件 |

示例：
```bash
git commit -m "✨ Add: 支持 ByteRange 功能"
git commit -m "🐛 Fix: 修复 GUI 界面卡顿问题"
git commit -m "📚 Docs: 更新 README 安装说明"
```

---

## 🌿 分支管理（可选）

如果你想使用分支开发：

```bash
# 创建新分支
git checkout -b feature/byterange-support

# 开发并提交
git add .
git commit -m "✨ Add ByteRange support"

# 推送新分支
git push -u origin feature/byterange-support

# 在 GitHub 上创建 Pull Request

# 合并后切换回主分支
git checkout main
git pull
```

---

## 🏷️ 版本标签（可选）

为重要版本打标签：

```bash
# 创建标签
git tag -a v3.0 -m "Version 3.0: 加密解密版"

# 推送标签
git push origin v3.0

# 推送所有标签
git push --tags
```

---

## ⚠️ 注意事项

### 上传前检查清单：

- ✅ `.gitignore` 已创建（避免上传大文件）
- ✅ 删除或忽略测试视频文件（`鸢饱.mp4`）
- ✅ 删除或忽略 `downloads/` 目录
- ✅ 删除或忽略虚拟环境 `venv/`
- ✅ 敏感信息已移除（API密钥、密码等）
- ✅ README 中的用户名已替换

### 检查文件大小：

```bash
# 查看哪些文件会被上传
git ls-files

# 查看仓库大小
git count-objects -vH
```

### 如果误提交大文件：

```bash
# 从 Git 历史中删除文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch 鸢饱.mp4" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送（危险操作！）
git push origin --force --all
```

---

## 🎯 完整示例

```bash
# 1. 初始化
cd F:\测试项目2
git init

# 2. 配置用户信息（如果还没配置）
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 3. 添加并提交
git add .
git commit -m "🎉 Initial commit: HLS-Downloader-Plus v3.0"

# 4. 关联远程仓库
git remote add origin https://github.com/YOUR_USERNAME/HLS-Downloader-Plus.git

# 5. 推送
git branch -M main
git push -u origin main
```

---

## 📖 GitHub 仓库设置

### 推荐设置：

1. **About（关于）**
   - Description: `A powerful M3U8/HLS video downloader with AES-128 decryption support`
   - Website: 你的博客或文档站点（可选）
   - Topics: `m3u8`, `hls`, `video-downloader`, `aes-decryption`, `python`, `gui`

2. **README Badges（徽章）**
   - 已在 README 中添加了 Python 版本、License、Platform 徽章

3. **Issues（问题）**
   - 启用 Issues 让用户报告问题

4. **Discussions（讨论）**
   - 启用 Discussions 建立社区

5. **Releases（发布）**
   - 创建第一个 Release: `v3.0`
   - 上传编译好的版本（可选）

---

## 🎊 上传完成后

### 美化你的仓库：

1. **添加 Screenshots（截图）**
   ```bash
   # 在 README 中添加截图
   mkdir -p .github/screenshots
   # 将截图放到这个目录
   ```

2. **添加 Star 提醒**
   - 在 README 底部已添加

3. **分享你的项目**
   - Reddit: r/Python, r/opensource
   - Twitter / X
   - Hacker News

---

## 🆘 常见问题

### Q: 推送时要求输入用户名密码？

A: GitHub 已不支持密码认证，需要使用 Token：
1. GitHub Settings → Developer settings → Personal access tokens → Generate new token
2. 选择 `repo` 权限
3. 使用 Token 作为密码

或使用 SSH（推荐）：
```bash
ssh-keygen -t ed25519 -C "your.email@example.com"
# 将 ~/.ssh/id_ed25519.pub 内容添加到 GitHub SSH Keys
```

### Q: 推送被拒绝（rejected）？

A: 可能是远程有更新：
```bash
git pull --rebase origin main
git push
```

### Q: 想要取消某个提交？

A:
```bash
# 撤销最后一次提交（保留修改）
git reset HEAD~1

# 完全删除最后一次提交（危险！）
git reset --hard HEAD~1
```

---

**祝上传顺利！ 🎉**
