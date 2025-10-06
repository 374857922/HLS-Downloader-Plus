#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M3U8视频下载器 - 批量下载版本
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import requests
from requests.cookies import RequestsCookieJar
import m3u8
import http.cookiejar
from urllib.parse import urljoin, urlparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


class M3U8DownloaderGUI:
    def __init__(self, url, output_dir, output_name=None, max_workers=10, callback=None, use_proxy=False, proxy_url=None, cookies_file=None, cookies_from_browser=None, preloaded_cookie_jar=None):
        """
        初始化M3U8下载器

        Args:
            url: m3u8播放列表URL
            output_dir: 输出目录
            output_name: 输出文件名（不含扩展名）
            max_workers: 最大并发下载数
            callback: 进度回调函数 callback(message, progress)
            use_proxy: 是否使用代理
            proxy_url: 代理地址（例如：http://127.0.0.1:7890）
        """
        self.url = url
        self.output_dir = Path(output_dir)
        self.max_workers = max_workers
        self.callback = callback
        self.cancel_flag = False
        self.cookies_file = None
        self.cookie_jar = None
        self.cookies_from_browser = None

        if cookies_file:
            cookie_path = Path(cookies_file).expanduser()
            if not cookie_path.exists():
                raise FileNotFoundError(f"Cookies 文件不存在: {cookie_path}")
            self.cookies_file = str(cookie_path)
            try:
                jar = http.cookiejar.MozillaCookieJar(self.cookies_file)
                jar.load(ignore_discard=True, ignore_expires=True)
                self._ensure_cookie_jar()
                for cookie in jar:
                    self.cookie_jar.set_cookie(cookie)
                self.log(f"[*] 已加载 cookies 文件: {self.cookies_file}")
            except Exception as exc:
                raise ValueError(f"无法加载 cookies 文件: {exc}") from exc

        if cookies_from_browser:
            self.cookies_from_browser_spec = cookies_from_browser.strip() if isinstance(cookies_from_browser, str) else None
            # For non-YouTube URLs, try to load cookies for use with 'requests'
            if not self._is_youtube_url(self.url):
                try:
                    self.cookies_from_browser = self._parse_cookies_from_browser(cookies_from_browser)
                    self.log(f"[*] 已配置浏览器 cookies: {cookies_from_browser}")
                    try:
                        from yt_dlp.cookies import load_cookies
                        jar = load_cookies(None, self.cookies_from_browser, None)
                        if jar:
                            self._ensure_cookie_jar()
                            for cookie in jar:
                                self.cookie_jar.set_cookie(cookie)
                            self.log("[*] 已从浏览器获取 cookies")
                    except ImportError:
                        self.log("[!] 提供了浏览器 cookies，但未安装 yt-dlp，无法自动获取")
                    except Exception as exc:
                        self.log(f"[!] 浏览器 cookies 加载失败: {exc}")
                except ValueError as exc:
                    raise ValueError(f"无效的浏览器 cookies 参数: {exc}") from exc

        if preloaded_cookie_jar:
            self._ensure_cookie_jar()
            for cookie in preloaded_cookie_jar:
                self.cookie_jar.set_cookie(cookie)
            self.log("[*] 已应用外部浏览器 cookies")
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 设置输出文件名
        # 如果指定了文件名，直接使用；否则使用时间戳
        if output_name and output_name.strip():
            self.output_name = output_name.strip()
        else:
            # 未指定文件名，使用时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            parsed_url = urlparse(url)
            base_name = Path(parsed_url.path).stem or "video"
            self.output_name = f"{base_name}_{timestamp}"

        # 创建临时目录存储ts分片
        self.temp_dir = None

        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # 设置代理
        self.proxies = None
        if use_proxy and proxy_url:
            self.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            self.log(f"[*] 使用代理: {proxy_url}")
        else:
            # 明确禁用代理，避免使用系统代理
            self.proxies = {
                'http': None,
                'https': None
            }
            self.log("[*] 已禁用代理")

        # 密钥缓存
        self.key_cache = {}

    def _ensure_cookie_jar(self):
        if self.cookie_jar is None:
            self.cookie_jar = RequestsCookieJar()
        return self.cookie_jar

    @staticmethod
    def _clone_cookie_jar(jar):
        if not jar:
            return None
        cloned = RequestsCookieJar()
        for cookie in jar:
            cloned.set_cookie(cookie)
        return cloned

    @staticmethod
    def _parse_cookies_from_browser(spec):
        if spec is None:
            raise ValueError('浏览器参数不能为空')
        spec = spec.strip()
        if not spec:
            raise ValueError('浏览器参数不能为空')

        container = None
        if '::' in spec:
            spec, container = spec.split('::', 1)

        profile = None
        browser_part = spec
        if ':' in browser_part:
            browser_part, profile = browser_part.split(':', 1)

        keyring = None
        if '+' in browser_part:
            browser, keyring = browser_part.split('+', 1)
        else:
            browser, keyring = browser_part, None

        def normalize(value):
            if value is None:
                return None
            value = value.strip()
            return value or None

        browser = normalize(browser)
        if not browser:
            raise ValueError('未指定浏览器名称')
        browser = browser.lower()

        keyring = normalize(keyring)
        if keyring:
            keyring = keyring.lower()

        profile = normalize(profile)
        container = normalize(container)

        return browser, profile, keyring, container

    def log(self, message, progress=None):
        """日志输出"""
        if self.callback:
            self.callback(message, progress)

    def download_m3u8(self):
        """下载并解析m3u8播放列表"""
        self.log("[*] 正在获取M3U8播放列表...")
        try:
            response = requests.get(self.url, headers=self.headers, proxies=self.proxies, timeout=30, cookies=self.cookie_jar)
            response.raise_for_status()

            # 解析m3u8
            playlist = m3u8.loads(response.text)

            # 如果是主播放列表，选择第一个变体
            if playlist.is_variant:
                self.log("[*] 检测到多码率播放列表，选择第一个")
                variant_url = urljoin(self.url, playlist.playlists[0].uri)
                response = requests.get(variant_url, headers=self.headers, proxies=self.proxies, timeout=30, cookies=self.cookie_jar)
                response.raise_for_status()
                playlist = m3u8.loads(response.text)
                self.url = variant_url

            return playlist
        except Exception as e:
            self.log(f"[!] 获取M3U8失败: {e}")
            return None

    def get_decrypt_key(self, key_obj):
        """获取解密密钥"""
        if not key_obj or key_obj.method == 'NONE' or not key_obj.uri:
            return None, None

        if key_obj.uri in self.key_cache:
            return self.key_cache[key_obj.uri]

        try:
            key_url = urljoin(self.url, key_obj.uri)
            response = requests.get(key_url, headers=self.headers, proxies=self.proxies, timeout=30, cookies=self.cookie_jar)
            response.raise_for_status()
            key_bytes = response.content

            if key_obj.iv:
                iv_hex = key_obj.iv.replace('0x', '')
                iv_bytes = bytes.fromhex(iv_hex)
            else:
                iv_bytes = None

            self.key_cache[key_obj.uri] = (key_bytes, iv_bytes)
            return key_bytes, iv_bytes
        except Exception as e:
            self.log(f"[!] 获取解密密钥失败: {e}")
            return None, None

    def decrypt_segment(self, data, key_bytes, iv_bytes, segment_index):
        """解密TS分片"""
        if not key_bytes:
            return data

        try:
            if iv_bytes is None:
                iv_bytes = segment_index.to_bytes(16, byteorder='big')

            cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
            decrypted_data = cipher.decrypt(data)

            try:
                decrypted_data = unpad(decrypted_data, AES.block_size)
            except ValueError:
                pass

            return decrypted_data
        except Exception as e:
            self.log(f"[!] 解密分片失败: {e}")
            return data

    def download_segment(self, segment_info):
        """下载单个ts分片"""
        if self.cancel_flag:
            return (segment_info[0], False, None)

        index, segment = segment_info
        segment_url = urljoin(self.url, segment.uri)
        file_path = self.temp_dir / f"segment_{index:05d}.ts"

        if file_path.exists():
            return (index, True, file_path)

        for attempt in range(3):
            if self.cancel_flag:
                return (index, False, None)
            try:
                response = requests.get(segment_url, headers=self.headers, proxies=self.proxies, timeout=30, cookies=self.cookie_jar)
                response.raise_for_status()

                data = response.content

                # 检查是否需要解密
                if segment.key:
                    key_bytes, iv_bytes = self.get_decrypt_key(segment.key)
                    if key_bytes:
                        data = self.decrypt_segment(data, key_bytes, iv_bytes, index)

                with open(file_path, 'wb') as f:
                    f.write(data)
                return (index, True, file_path)
            except Exception as e:
                if attempt == 2:
                    self.log(f"[!] 分片 {index} 下载失败: {e}")
                    return (index, False, None)
        return (index, False, None)

    def download_all_segments(self, playlist):
        """并发下载所有ts分片"""
        segments = [(i, seg) for i, seg in enumerate(playlist.segments)]
        total_segments = len(segments)

        # 检查是否有加密
        has_encryption = any(seg.key for seg in playlist.segments)
        if has_encryption:
            self.log("[*] 检测到加密内容，将自动解密")

        self.log(f"[*] 共 {total_segments} 个分片，使用 {self.max_workers} 线程下载")

        completed = 0
        failed = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.download_segment, seg): seg for seg in segments}

            for future in as_completed(futures):
                if self.cancel_flag:
                    executor.shutdown(wait=False)
                    return False

                result = future.result()
                completed += 1
                progress = int((completed / total_segments) * 100)

                if result[1]:
                    self.log(f"[*] 下载进度: {completed}/{total_segments}", progress)
                else:
                    failed.append(result[0])

        if failed:
            self.log(f"[!] {len(failed)} 个分片下载失败")
            return False

        self.log("[✓] 所有分片下载完成", 100)
        return True

    def merge_segments(self):
        """合并ts分片"""
        output_file = self.output_dir / f"{self.output_name}.mp4"
        self.log(f"[*] 正在合并到: {output_file.name}")

        ts_files = sorted(self.temp_dir.glob("segment_*.ts"))
        if not ts_files:
            self.log("[!] 没有找到ts文件")
            return False

        try:
            # 尝试FFmpeg
            if self.merge_with_ffmpeg(ts_files, output_file):
                return True
            # 二进制合并
            self.log("[*] 使用二进制合并")
            return self.merge_binary(ts_files, output_file)
        except Exception as e:
            self.log(f"[!] 合并失败: {e}")
            return False

    def merge_with_ffmpeg(self, ts_files, output_file):
        """使用ffmpeg合并"""
        import subprocess
        try:
            filelist_path = self.temp_dir / "filelist.txt"
            with open(filelist_path, 'w', encoding='utf-8') as f:
                for ts_file in ts_files:
                    f.write(f"file '{ts_file.absolute()}'\n")

            cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i',
                   str(filelist_path), '-c', 'copy', '-y', str(output_file)]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                self.log("[✓] FFmpeg合并完成")
                return True
            return False
        except:
            return False

    def merge_binary(self, ts_files, output_file):
        """二进制合并"""
        try:
            with open(output_file, 'wb') as outfile:
                for i, ts_file in enumerate(ts_files):
                    if self.cancel_flag:
                        return False
                    with open(ts_file, 'rb') as infile:
                        outfile.write(infile.read())
                    progress = int(((i + 1) / len(ts_files)) * 100)
                    self.log(f"[*] 合并进度: {i+1}/{len(ts_files)}", progress)
            self.log("[✓] 合并完成")
            return True
        except Exception as e:
            self.log(f"[!] 合并失败: {e}")
            return False

    def cleanup(self):
        """清理临时文件"""
        if not self.temp_dir or not self.temp_dir.exists():
            return

        self.log("[*] 清理临时文件...")
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            self.log("[✓] 临时文件已清理")
        except Exception as e:
            self.log(f"[!] 清理失败: {e}")

    def download(self):
        """执行下载"""
        try:
            # 判断是否为YouTube链接
            is_youtube = M3U8DownloaderGUI._is_youtube_url(self.url)
            if is_youtube:
                return self.download_youtube()

            # 原有的M3U8下载逻辑
            self.temp_dir = self.output_dir / f"{self.output_name}_temp"
            self.temp_dir.mkdir(exist_ok=True)
            playlist = self.download_m3u8()
            if not playlist:
                return False

            if not self.download_all_segments(playlist):
                return False

            if not self.merge_segments():
                return False

            self.cleanup()

            output_file = self.output_dir / f"{self.output_name}.mp4"
            self.log(f"\n[✓] 下载完成: {output_file}")
            return True

        except Exception as e:
            self.log(f"[!] 错误: {e}")
            return False

    def download_youtube(self):
        """使用 yt-dlp 命令行工具下载 YouTube 视频"""
        self.log(f"[*] 检测到 YouTube 视频，使用 yt-dlp 命令行下载: {self.url}")
        
        import shutil
        import subprocess
        import re

        # 查找 yt-dlp 可执行文件
        # 优先使用与当前 Python 解释器在同一目录下的 yt-dlp
        py_dir = Path(sys.executable).parent
        yt_dlp_path = py_dir / 'yt-dlp'
        if sys.platform == 'win32':
            yt_dlp_path = yt_dlp_path.with_suffix('.exe')

        if not yt_dlp_path.exists():
            # 如果 venv 路径下不存在，则回退到在 PATH 中查找
            yt_dlp_path_which = shutil.which('yt-dlp')
            if not yt_dlp_path_which:
                self.log("[!] yt-dlp 命令未找到。请确保已在虚拟环境中安装 yt-dlp。")
                self.log("[!] 你可以运行 'venv\\Scripts\\pip.exe install yt-dlp' 来安装。")
                return False
            yt_dlp_path = Path(yt_dlp_path_which)

        self.log(f"[*] 使用 yt-dlp: {yt_dlp_path}")

        # 检查 FFmpeg 是否可用，因为合并格式需要它
        if not shutil.which('ffmpeg'):
            self.log("[!] 警告: 未在系统中找到 FFmpeg。")
            self.log("[!] FFmpeg 对于合并高质量的视频和音频以及格式转换 (如 webm -> mp4) 是必需的。")
            self.log("[!] 如果下载失败或输出文件无法播放，请先安装 FFmpeg 并确保其在系统 PATH 中。")
            self.log("[!] FFmpeg 下载: https://ffmpeg.org/download.html")

        # 文件名模板
        if self.output_name:
            # 如果用户指定了文件名
            output_template = self.output_dir / f"{self.output_name}.%(ext)s"
        else:
            # 否则使用指定格式
            output_template = self.output_dir / "%(uploader)s %(upload_date)s %(playlist_index)s [%(id)s].%(ext)s"

        cmd = [
            str(yt_dlp_path),
            '--progress',
            '--ignore-errors',
            # 优先选择H.264 (avc) 和 AAC (mp4a) 编码，如果不可用则回退到最佳格式
            '--format', 'bestvideo[vcodec^=avc]+bestaudio[acodec^=mp4a]/bestvideo+bestaudio/best',
            # 在必要时将视频重新编码为 MP4，以获得最佳兼容性
            '--recode-video', 'mp4',
            '--output', str(output_template),
        ]

        # 添加代理
        if self.proxies and self.proxies.get('https'):
            cmd.extend(['--proxy', self.proxies['https']])
            self.log(f"[*] 为 yt-dlp 设置代理: {self.proxies['https']}")

        # 添加 cookies
        if self.cookies_file:
            cmd.extend(['--cookies', self.cookies_file])
            self.log(f"[*] yt-dlp 使用 cookies 文件: {self.cookies_file}")
        elif self.cookies_from_browser_spec:
            cmd.extend(['--cookies-from-browser', self.cookies_from_browser_spec])
            self.log(f"[*] yt-dlp 尝试从浏览器导入 cookies: {self.cookies_from_browser_spec}")


        cmd.append(self.url)
        self.log(f"[*] 执行命令: {' '.join(cmd)}")

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            progress_regex = re.compile(r"\[download\]\s+([0-9\.]+)%")

            while True:
                if self.cancel_flag:
                    self.log("[!] 用户请求取消，正在终止 yt-dlp 进程...")
                    process.terminate()
                    return False

                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    self.log(line)
                    match = progress_regex.search(line)
                    if match:
                        percent = float(match.group(1))
                        self.log("", progress=int(percent))
            
            rc = process.poll()
            if rc != 0:
                self.log(f"\n[!] yt-dlp 下载失败，退出码: {rc}")
                return False

        except FileNotFoundError:
            self.log("[!] yt-dlp 命令未找到。")
            return False
        except Exception as e:
            self.log(f"\n[!] YouTube 下载时发生错误: {e}")
            return False

        self.log(f"[✓] 下载完成", progress=100)
        return True

    @staticmethod
    def _is_youtube_url(url):
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        netloc = parsed.netloc.lower()
        return any(domain in netloc for domain in ("youtube.com", "youtu.be", "youtube-nocookie.com"))

    def cancel(self):
        """取消下载"""
        self.cancel_flag = True


class BatchApplication(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("M3U8 批量下载器")
        self.geometry("900x750")

        # 变量
        self.dir_var = tk.StringVar(value=r"G:\BaiduNetdiskDownload\片片")
        self.threads_var = tk.StringVar(value="10")
        self.url_input_var = tk.StringVar()
        self.filename_input_var = tk.StringVar()
        self.cookies_file_var = tk.StringVar()
        self.cookies_browser_var = tk.StringVar(value="chrome:Default")
        self.browser_cookie_jar = None

        # 代理设置
        self.use_proxy_var = tk.BooleanVar(value=False)
        self.proxy_url_var = tk.StringVar(value="http://127.0.0.1:7890")

        # 任务列表
        self.tasks = []  # [(url, filename), ...]
        self.current_downloader = None
        self.download_thread = None
        self.is_downloading = False

        self.setup_styles()
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        # --- 黑金配色方案 ---
        self.BG_COLOR = "#1B1B1B"          # 炭黑背景
        self.FG_COLOR = "#EAEAEA"          # 米白文字
        HEADER_COLOR = "#FFFFFF"         # 纯白标题
        ENTRY_BG = "#2C2C2C"             # 深灰控件背景
        DISABLED_FG = "#777777"          # 禁用状态灰色
        ACCENT_COLOR = "#D4AF37"         # 主色调 - 金色
        BORDER_COLOR = "#3E3E3E"         # 柔和的深灰边框
        
        self.SUCCESS_COLOR = "#2ecc71"     # 成功 - 绿色
        self.ERROR_COLOR = "#e74c3c"       # 失败 - 红色
        self.WAITING_COLOR = "#f39c12"     # 等待 - 橙黄
        self.DOWNLOADING_COLOR = ACCENT_COLOR # 下载中 - 金色

        FONT_NORMAL = ("Segoe UI", 10)
        FONT_BOLD = ("Segoe UI", 10, "bold")
        FONT_TITLE = ("Segoe UI", 12, "bold")

        self.configure(bg=self.BG_COLOR)

        # --- 基础控件样式 ---
        self.style.configure('.', background=self.BG_COLOR, foreground=self.FG_COLOR, font=FONT_NORMAL, borderwidth=0, focusthickness=0)
        self.style.configure('TFrame', background=self.BG_COLOR)
        self.style.configure('TLabel', background=self.BG_COLOR, foreground=self.FG_COLOR, font=FONT_NORMAL)
        self.style.configure('TCheckbutton', background=self.BG_COLOR, foreground=self.FG_COLOR, font=FONT_NORMAL, indicatorbackground=ENTRY_BG)
        self.style.map('TCheckbutton',
            foreground=[('active', HEADER_COLOR)],
            indicatorbackground=[('selected', ACCENT_COLOR), ('active', ENTRY_BG)])

        # --- LabelFrame ---
        self.style.configure('TLabelframe', background=self.BG_COLOR, bordercolor=BORDER_COLOR, relief="solid", borderwidth=1)
        self.style.configure('TLabelframe.Label', background=self.BG_COLOR, foreground=ACCENT_COLOR, font=FONT_TITLE)

        # --- 输入框 ---
        self.style.configure('TEntry', fieldbackground=ENTRY_BG, foreground=self.FG_COLOR, insertcolor=self.FG_COLOR, bordercolor=BORDER_COLOR, lightcolor=BORDER_COLOR, darkcolor=BORDER_COLOR)
        self.style.map('TEntry',
            fieldbackground=[('disabled', self.BG_COLOR), ('!disabled', ENTRY_BG)],
            foreground=[('disabled', DISABLED_FG)])

        # --- 按钮 ---
        self.style.configure('TButton', background=ENTRY_BG, foreground=ACCENT_COLOR, font=FONT_BOLD, padding=(10, 5), borderwidth=0)
        self.style.map('TButton',
            background=[('active', '#3E3E3E'), ('disabled', '#444444')],
            foreground=[('disabled', DISABLED_FG), ('active', '#E0B840')])
        
        self.style.configure('Small.TButton', padding=(5, 2), font=("Segoe UI", 8))

        # --- 进度条 ---
        self.style.configure('TProgressbar', thickness=15, background=ACCENT_COLOR, troughcolor=ENTRY_BG, borderwidth=0)

        # --- Treeview (任务列表) ---
        self.style.configure('Treeview',
            background=ENTRY_BG,
            fieldbackground=ENTRY_BG,
            foreground=self.FG_COLOR,
            rowheight=25,
            font=FONT_NORMAL)
        self.style.map('Treeview', background=[('selected', ACCENT_COLOR)])
        self.style.configure('Treeview.Heading',
            background=self.BG_COLOR,
            foreground=HEADER_COLOR,
            font=FONT_BOLD,
            relief='flat')
        self.style.map('Treeview.Heading', background=[('active', BORDER_COLOR)])

        # --- 滚动条 ---
        self.style.configure('Vertical.TScrollbar', background=self.BG_COLOR, troughcolor=ENTRY_BG, arrowcolor=self.FG_COLOR, borderwidth=0)
        self.style.map('Vertical.TScrollbar',
            arrowcolor=[('pressed', HEADER_COLOR)],
            background=[('pressed', ACCENT_COLOR), ('active', BORDER_COLOR)])

    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # ===== 添加任务区域 =====
        task_input_frame = ttk.LabelFrame(main_frame, text=" 添加下载任务 ", padding="15")
        task_input_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        # URL输入
        ttk.Label(task_input_frame, text="M3U8 URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(task_input_frame, textvariable=self.url_input_var, width=70).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))

        # 文件名输入
        ttk.Label(task_input_frame, text="文件名 (可选):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(task_input_frame, textvariable=self.filename_input_var, width=70).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))

        # 添加按钮
        btn_frame = ttk.Frame(task_input_frame)
        btn_frame.grid(row=2, column=1, sticky='e', pady=(10,0))
        ttk.Button(btn_frame, text="添加到列表", command=self.add_task, width=15).pack(side=tk.LEFT, padx=(0,10))
        ttk.Button(btn_frame, text="清空输入", command=self.clear_input, width=15).pack(side=tk.LEFT)

        task_input_frame.columnconfigure(1, weight=1)

        # ===== 任务列表区域 =====
        task_list_frame = ttk.LabelFrame(main_frame, text=" 下载任务列表 ", padding="15")
        task_list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))

        # 创建任务列表（Treeview）
        columns = ("url", "filename", "status")
        self.task_tree = ttk.Treeview(task_list_frame, columns=columns, show="headings", height=8)

        self.task_tree.heading("url", text="URL")
        self.task_tree.heading("filename", text="文件名")
        self.task_tree.heading("status", text="状态")

        self.task_tree.column("url", width=400, anchor=tk.W)
        self.task_tree.column("filename", width=200, anchor=tk.W)
        self.task_tree.column("status", width=100, anchor=tk.CENTER)

        # 滚动条
        scrollbar = ttk.Scrollbar(task_list_frame, orient=tk.VERTICAL, command=self.task_tree.yview, style='Vertical.TScrollbar')
        self.task_tree.configure(yscroll=scrollbar.set)

        self.task_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # --- 任务状态标签 ---
        self.task_tree.tag_configure('waiting', foreground=self.WAITING_COLOR)
        self.task_tree.tag_configure('downloading', foreground=self.DOWNLOADING_COLOR)
        self.task_tree.tag_configure('done', foreground=self.SUCCESS_COLOR)
        self.task_tree.tag_configure('failed', foreground=self.ERROR_COLOR)

        # 任务管理按钮
        task_btn_frame = ttk.Frame(task_list_frame)
        task_btn_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky='w')
        ttk.Button(task_btn_frame, text="删除选中", command=self.delete_selected, width=12).pack(side=tk.LEFT, padx=(0,10))
        ttk.Button(task_btn_frame, text="清空列表", command=self.clear_all_tasks, width=12).pack(side=tk.LEFT)

        task_list_frame.columnconfigure(0, weight=1)
        task_list_frame.rowconfigure(0, weight=1)

        # ===== 保存目录 =====
        save_dir_frame = ttk.LabelFrame(main_frame, text=" 保存目录 ", padding="15")
        save_dir_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        save_dir_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(save_dir_frame, textvariable=self.dir_var).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(save_dir_frame, text="浏览", command=self.browse_dir, width=8, style='Small.TButton').grid(row=0, column=1, padx=(10, 0))

        # ===== 高级设置 =====
        settings_frame = ttk.LabelFrame(main_frame, text=" 高级设置 ", padding="15")
        settings_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        settings_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(3, weight=1)

        # Threads
        ttk.Label(settings_frame, text="并发线程:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(settings_frame, textvariable=self.threads_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        # Proxy
        self.proxy_check = ttk.Checkbutton(settings_frame, text="启用代理", variable=self.use_proxy_var, command=self.toggle_proxy)
        self.proxy_check.grid(row=0, column=2, sticky=tk.W, padx=(20, 10))
        self.proxy_entry = ttk.Entry(settings_frame, textvariable=self.proxy_url_var)
        self.proxy_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(10, 0))
        self.proxy_entry.config(state='disabled')

        # Cookies
        ttk.Label(settings_frame, text="Cookies 文件:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        ttk.Entry(settings_frame, textvariable=self.cookies_file_var).grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0), padx=(10,0))
        ttk.Button(settings_frame, text="浏览", command=self.browse_cookies_file, width=6, style='Small.TButton').grid(row=1, column=3, padx=(5,0), pady=(10, 0))

        ttk.Label(settings_frame, text="浏览器导入:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Entry(settings_frame, textvariable=self.cookies_browser_var).grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0), padx=(10,0))
        ttk.Button(settings_frame, text="清空", command=self.clear_cookies_inputs, width=6, style='Small.TButton').grid(row=2, column=3, padx=(5,0), pady=(5, 0))
        
        # ===== 控制按钮 =====
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, columnspan=2, pady=10)

        self.start_btn = ttk.Button(control_frame, text="开始批量下载", command=self.start_batch_download, width=18)
        self.start_btn.pack(side=tk.LEFT, padx=10)

        self.cancel_btn = ttk.Button(control_frame, text="取消下载", command=self.cancel_download, state=tk.DISABLED, width=18)
        self.cancel_btn.pack(side=tk.LEFT, padx=10)

        # ===== 进度条 =====
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5, ipady=5)
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress = ttk.Progressbar(progress_frame, length=850, mode='determinate')
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # ===== 日志输出 =====
        log_frame = ttk.LabelFrame(main_frame, text=" 日志输出 ", padding="15")
        log_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=100,
            bg=self.BG_COLOR, fg=self.FG_COLOR, font=("Consolas", 9), relief="flat", borderwidth=5, insertbackground=self.FG_COLOR)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置权重
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)

    def toggle_proxy(self):
        """切换代理启用状态"""
        if self.use_proxy_var.get():
            self.proxy_entry.config(state='normal')
        else:
            self.proxy_entry.config(state='disabled')

    def add_task(self):
        """添加任务到列表"""
        url = self.url_input_var.get().strip()
        filename = self.filename_input_var.get().strip()

        if not url:
            messagebox.showerror("错误", "请输入M3U8 URL")
            return

        # 添加到任务列表
        self.tasks.append((url, filename if filename else ""))

        # 添加到Treeview
        display_filename = filename if filename else "自动生成"
        self.task_tree.insert("", tk.END, values=(url, display_filename, "等待中"), tags=('waiting',))

        # 清空输入框
        self.clear_input()
        self.log_output(f"[+] 已添加任务: {url}")

    def clear_input(self):
        """清空输入框"""
        self.url_input_var.set("")
        self.filename_input_var.set("")

    def delete_selected(self):
        """删除选中的任务"""
        if self.is_downloading:
            messagebox.showwarning("警告", "下载进行中，无法删除任务")
            return

        selected = self.task_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要删除的任务")
            return

        for item in selected:
            # 获取索引
            index = self.task_tree.index(item)
            # 从列表删除
            if 0 <= index < len(self.tasks):
                del self.tasks[index]
            # 从Treeview删除
            self.task_tree.delete(item)

        self.log_output("[*] 已删除选中任务")

    def clear_all_tasks(self):
        """清空所有任务"""
        if self.is_downloading:
            messagebox.showwarning("警告", "下载进行中，无法清空列表")
            return

        if len(self.tasks) == 0:
            return

        if messagebox.askyesno("确认", "确定要清空所有任务吗？"):
            self.tasks.clear()
            for item in self.task_tree.get_children():
                self.task_tree.delete(item)
            self.log_output("[*] 已清空所有任务")

    def browse_dir(self):
        """选择目录"""
        directory = filedialog.askdirectory(initialdir=self.dir_var.get())
        if directory:
            self.dir_var.set(directory)

    def browse_cookies_file(self):
        """选择 cookies 文件"""
        filetypes = [("Cookies 文件", '*.txt *.cookies *.cookie'), ("所有文件", '*.*')]
        file_path = filedialog.askopenfilename(title="选择 Cookies 文件", filetypes=filetypes)
        if file_path:
            self.cookies_file_var.set(file_path)

    def clear_cookies_inputs(self):
        """清空 cookies 相关输入"""
        self.cookies_file_var.set("")
        self.cookies_browser_var.set("")
        self.browser_cookie_jar = None

    def load_cookies_from_browser(self):
        """从浏览器获取 cookies 并应用到批量任务"""
        spec = self.cookies_browser_var.get().strip()
        if not spec:
            messagebox.showerror("错误", "请先填写浏览器导入参数")
            return
        try:
            parsed = M3U8DownloaderGUI._parse_cookies_from_browser(spec)
        except ValueError as exc:
            messagebox.showerror("错误", f"浏览器参数无效: {exc}")
            return
        try:
            from yt_dlp.cookies import load_cookies
        except ImportError:
            messagebox.showerror("错误", "未安装 yt-dlp，无法获取浏览器 cookies")
            return
        try:
            jar = load_cookies(None, parsed, None)
        except Exception as exc:
            messagebox.showerror("错误", f"提取浏览器 cookies 失败: {exc}")
            return
        if not jar or len(jar) == 0:
            messagebox.showerror("错误", "未从浏览器读取到任何 cookies")
            return
        requests_jar = M3U8DownloaderGUI._clone_cookie_jar(jar)
        if not requests_jar or len(requests_jar) == 0:
            messagebox.showerror("错误", "读取到的 cookies 无效")
            return
        self.browser_cookie_jar = requests_jar
        self.log_output(f"[*] 已加载浏览器 cookies，共 {len(requests_jar)} 条")
        messagebox.showinfo("成功", f"已从浏览器加载 {len(requests_jar)} 条 cookies")

    def log_output(self, message):
        """输出日志"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

    def log_message(self, message, progress=None):
        """下载器回调函数"""
        self.log_output(message)
        if progress is not None:
            self.progress['value'] = progress
        self.update_idletasks()

    def start_batch_download(self):
        """开始批量下载"""
        if len(self.tasks) == 0:
            messagebox.showinfo("提示", "请先添加下载任务")
            return

        output_dir = self.dir_var.get().strip()
        if not output_dir:
            messagebox.showerror("错误", "请选择保存目录")
            return

        try:
            threads = int(self.threads_var.get())
            if threads < 1 or threads > 50:
                raise ValueError
        except:
            messagebox.showerror("错误", "线程数必须是1-50之间的整数")
            return

        # 清空日志
        self.log_text.delete(1.0, tk.END)
        self.progress['value'] = 0

        # 禁用按钮
        self.start_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.is_downloading = True

        # 在新线程中执行批量下载
        self.download_thread = threading.Thread(target=self.run_batch_download, daemon=True)
        self.download_thread.start()

    def run_batch_download(self):
        """执行批量下载"""
        output_dir = self.dir_var.get().strip()
        threads = int(self.threads_var.get())
        cookies_file = self.cookies_file_var.get().strip() or None
        cookies_browser = self.cookies_browser_var.get().strip() or None
        base_cookie_jar = self.browser_cookie_jar

        total_tasks = len(self.tasks)
        success_count = 0
        fail_count = 0

        for index, (url, filename) in enumerate(self.tasks, 1):
            if not self.is_downloading:
                self.log_output("\n[!] 批量下载已取消")
                break

            # 更新任务状态
            self.update_task_status(index - 1, "下载中", "downloading")

            self.log_output(f"\n{'='*60}")
            self.log_output(f"[*] 开始下载任务 {index}/{total_tasks}")
            self.log_output(f"[*] URL: {url}")
            if filename:
                self.log_output(f"[*] 文件名: {filename}")
            self.log_output(f"{'='*60}\n")

            # 创建下载器
            try:
                task_cookie_jar = M3U8DownloaderGUI._clone_cookie_jar(base_cookie_jar)
                self.current_downloader = M3U8DownloaderGUI(
                    url=url,
                    output_dir=output_dir,
                    output_name=filename if filename else None,
                    max_workers=threads,
                    callback=self.log_message,
                    use_proxy=self.use_proxy_var.get(),
                    proxy_url=self.proxy_url_var.get(),
                    cookies_file=cookies_file,
                    cookies_from_browser=cookies_browser,
                    preloaded_cookie_jar=task_cookie_jar
                )
            except (FileNotFoundError, ValueError) as exc:
                fail_count += 1
                self.update_task_status(index - 1, "失败", "failed")
                self.log_output(f"[x] 任务 {index} 初始化失败: {exc}\n")
                continue
            except Exception as exc:
                fail_count += 1
                self.update_task_status(index - 1, "失败", "failed")
                self.log_output(f"[x] 任务 {index} 初始化失败: {exc}\n")
                continue

            # 执行下载
            try:
                success = self.current_downloader.download()
                if success:
                    success_count += 1
                    self.update_task_status(index - 1, "完成", "done")
                    self.log_output(f"[✓] 任务 {index} 下载成功\n")
                else:
                    fail_count += 1
                    self.update_task_status(index - 1, "失败", "failed")
                    self.log_output(f"[✗] 任务 {index} 下载失败\n")
            except Exception as e:
                fail_count += 1
                self.update_task_status(index - 1, "失败", "failed")
                self.log_output(f"[✗] 任务 {index} 出错: {e}\n")

            self.progress['value'] = 0

        # 下载完成
        self.log_output(f"\n{'='*60}")
        self.log_output(f"[*] 批量下载完成!")
        self.log_output(f"[*] 总任务数: {total_tasks}")
        self.log_output(f"[✓] 成功: {success_count}")
        self.log_output(f"[✗] 失败: {fail_count}")
        self.log_output(f"{'='*60}\n")

        # 恢复按钮状态
        self.after(0, self.download_finished)

        # 显示完成提示
        if fail_count == 0:
            self.after(0, lambda: messagebox.showinfo("完成", f"批量下载完成！\n成功: {success_count}"))
        else:
            self.after(0, lambda: messagebox.showwarning("完成", f"批量下载完成！\n成功: {success_count}\n失败: {fail_count}"))

    def update_task_status(self, index, status, tag):
        """更新任务状态"""
        def _update():
            try:
                items = self.task_tree.get_children()
                if 0 <= index < len(items):
                    item = items[index]
                    values = self.task_tree.item(item)['values']
                    self.task_tree.item(item, values=(values[0], values[1], status), tags=(tag,))
            except Exception as e:
                print(f"Error updating task status: {e}")
        self.after(0, _update)


    def cancel_download(self):
        """取消下载"""
        if self.is_downloading:
            if messagebox.askyesno("确认", "确定要取消当前的下载任务吗？"):
                if self.current_downloader:
                    self.current_downloader.cancel()
                self.is_downloading = False
                self.log_output("\n[!] 正在取消下载...")

    def download_finished(self):
        """下载完成"""
        self.start_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.is_downloading = False

    def on_closing(self):
        if self.is_downloading:
            if messagebox.askyesno("退出", "下载仍在进行中，确定要退出吗？"):
                if self.current_downloader:
                    self.current_downloader.cancel()
                self.is_downloading = False
                self.destroy()
        else:
            self.destroy()


def main():
    app = BatchApplication()
    # 在主循环开始前应用样式
    app.setup_styles()
    app.mainloop()


if __name__ == '__main__':
    main()
