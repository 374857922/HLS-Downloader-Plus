#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M3U8视频下载器
支持下载m3u8格式的视频流并合并为MP4文件
"""

import os
import sys
import argparse
import requests
import m3u8
import http.cookiejar
from urllib.parse import urljoin, urlparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


class M3U8Downloader:
    def __init__(self, url, output_dir="downloads", output_name=None, max_workers=10, cookies=None, cookies_from_browser=None):
        """
        初始化M3U8下载器

        Args:
            url: m3u8播放列表URL
            output_dir: 输出目录
            output_name: 输出文件名（不含扩展名）
            max_workers: 最大并发下载数
        """
        self.url = url
        self.output_dir = Path(output_dir)
        self.max_workers = max_workers
        self.cookies_file = None
        self.cookies_from_browser = None
        self.cookies_from_browser_spec = None
        self.cookie_jar = None
        self.is_youtube = self._is_youtube_url(url)

        if cookies:
            cookie_path = Path(cookies).expanduser()
            if not cookie_path.exists():
                print(f"[!] 指定的 cookies 文件不存在: {cookie_path}")
                sys.exit(1)
            self.cookies_file = str(cookie_path)
            try:
                jar = http.cookiejar.MozillaCookieJar(self.cookies_file)
                jar.load(ignore_discard=True, ignore_expires=True)
                self.cookie_jar = jar
                print(f"[*] 已加载 cookies 文件: {self.cookies_file}")
            except Exception as exc:
                print(f"[!] 无法加载 cookies 文件: {exc}")
                sys.exit(1)

        if cookies_from_browser:
            try:
                self.cookies_from_browser = self._parse_cookies_from_browser(cookies_from_browser)
                self.cookies_from_browser_spec = cookies_from_browser.strip() if isinstance(cookies_from_browser, str) else None
                print(f"[*] 已配置浏览器 cookies: {self.cookies_from_browser_spec or self.cookies_from_browser}")
                try:
                    from yt_dlp.cookies import load_cookies
                    jar = load_cookies(None, self.cookies_from_browser, None)
                    if jar:
                        if self.cookie_jar is None:
                            self.cookie_jar = jar
                        else:
                            for cookie in jar:
                                self.cookie_jar.set_cookie(cookie)
                        print("[*] 已从浏览器导出 cookies")
                except ImportError:
                    print("[!] 提供了 --cookies-from-browser 但未安装 yt-dlp，无法自动导出 cookies")
                except Exception as exc:
                    print(f"[!] 浏览器 cookies 加载失败: {exc}")
            except ValueError as exc:
                print(f"[!] 无效的 --cookies-from-browser 参数: {exc}")
                sys.exit(1)

        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)

        # 设置输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.is_youtube:
            if output_name:
                self.output_name = output_name
            else:
                self.output_name = None
        else:
            if output_name:
                self.output_name = f"{output_name}_{timestamp}"
            else:
                # 从URL中提取文件名
                parsed_url = urlparse(url)
                base_name = Path(parsed_url.path).stem or "video"
                self.output_name = f"{base_name}_{timestamp}"

        # 创建临时目录存储ts分片（仅针对M3U8下载）
        self.temp_dir = None
        if not self.is_youtube:
            self.temp_dir = self.output_dir / f"{self.output_name}_temp"
            self.temp_dir.mkdir(exist_ok=True)

        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # 密钥缓存
        self.key_cache = {}

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

    @staticmethod
    def _is_youtube_url(url):
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        netloc = parsed.netloc.lower()
        return any(domain in netloc for domain in ("youtube.com", "youtu.be", "youtube-nocookie.com"))

    def download_m3u8(self):
        """下载并解析m3u8播放列表"""
        print(f"[*] 正在获取M3U8播放列表: {self.url}")
        try:
            response = requests.get(self.url, headers=self.headers, timeout=30, cookies=self.cookie_jar)
            response.raise_for_status()

            # 解析m3u8
            playlist = m3u8.loads(response.text)

            # 如果是主播放列表，选择第一个变体
            if playlist.is_variant:
                print("[*] 检测到多码率播放列表，选择第一个播放列表")
                variant_url = urljoin(self.url, playlist.playlists[0].uri)
                print(f"[*] 使用播放列表: {variant_url}")
                response = requests.get(variant_url, headers=self.headers, timeout=30, cookies=self.cookie_jar)
                response.raise_for_status()
                playlist = m3u8.loads(response.text)
                self.url = variant_url  # 更新基础URL

            return playlist
        except Exception as e:
            print(f"[!] 获取M3U8播放列表失败: {e}")
            sys.exit(1)

    def get_decrypt_key(self, key_obj):
        """
        获取解密密钥

        Args:
            key_obj: m3u8的Key对象

        Returns:
            (key_bytes, iv_bytes) 元组，如果没有加密则返回 (None, None)
        """
        if not key_obj or key_obj.method == 'NONE' or not key_obj.uri:
            return None, None

        # 检查缓存
        if key_obj.uri in self.key_cache:
            return self.key_cache[key_obj.uri]

        try:
            # 下载密钥
            key_url = urljoin(self.url, key_obj.uri)
            response = requests.get(key_url, headers=self.headers, timeout=30, cookies=self.cookie_jar)
            response.raise_for_status()
            key_bytes = response.content

            # 获取IV
            if key_obj.iv:
                # 移除'0x'前缀并转换为bytes
                iv_hex = key_obj.iv.replace('0x', '')
                iv_bytes = bytes.fromhex(iv_hex)
            else:
                # 如果没有指定IV，使用序列号作为IV（根据HLS规范）
                iv_bytes = None

            # 缓存密钥
            self.key_cache[key_obj.uri] = (key_bytes, iv_bytes)
            return key_bytes, iv_bytes

        except Exception as e:
            print(f"[!] 获取解密密钥失败: {e}")
            return None, None

    def decrypt_segment(self, data, key_bytes, iv_bytes, segment_index):
        """
        解密TS分片

        Args:
            data: 加密的数据
            key_bytes: 密钥
            iv_bytes: 初始化向量
            segment_index: 分片序号（用于生成默认IV）

        Returns:
            解密后的数据
        """
        if not key_bytes:
            return data

        try:
            # 如果没有指定IV，使用序列号
            if iv_bytes is None:
                iv_bytes = segment_index.to_bytes(16, byteorder='big')

            # AES-128-CBC解密
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
            decrypted_data = cipher.decrypt(data)

            # 移除PKCS7填充
            try:
                decrypted_data = unpad(decrypted_data, AES.block_size)
            except ValueError:
                # 如果解除填充失败，返回原始解密数据
                pass

            return decrypted_data

        except Exception as e:
            print(f"[!] 解密分片失败: {e}")
            return data

    def download_segment(self, segment_info):
        """
        下载单个ts分片

        Args:
            segment_info: (index, segment) 元组，segment是m3u8.Segment对象

        Returns:
            (index, success, file_path) 元组
        """
        index, segment = segment_info

        # 构建完整的URL
        segment_url = urljoin(self.url, segment.uri)

        # 生成本地文件名
        file_path = self.temp_dir / f"segment_{index:05d}.ts"

        # 如果文件已存在，跳过下载
        if file_path.exists():
            return (index, True, file_path)

        # 尝试下载，最多重试3次
        for attempt in range(3):
            try:
                response = requests.get(segment_url, headers=self.headers, timeout=30, cookies=self.cookie_jar)
                response.raise_for_status()

                data = response.content

                # 检查是否需要解密
                if segment.key:
                    key_bytes, iv_bytes = self.get_decrypt_key(segment.key)
                    if key_bytes:
                        data = self.decrypt_segment(data, key_bytes, iv_bytes, index)

                # 保存文件
                with open(file_path, 'wb') as f:
                    f.write(data)

                return (index, True, file_path)
            except Exception as e:
                if attempt == 2:  # 最后一次尝试
                    print(f"\n[!] 下载分片 {index} 失败: {e}")
                    return (index, False, None)

        return (index, False, None)

    def download_all_segments(self, playlist):
        """
        并发下载所有ts分片

        Args:
            playlist: m3u8播放列表对象
        """
        segments = [(i, seg) for i, seg in enumerate(playlist.segments)]
        total_segments = len(segments)

        # 检查是否有加密
        has_encryption = any(seg.key for seg in playlist.segments)
        if has_encryption:
            print(f"[*] 检测到加密内容，将自动解密")

        print(f"[*] 共有 {total_segments} 个分片需要下载")
        print(f"[*] 使用 {self.max_workers} 个线程并发下载")

        # 存储下载结果
        results = []

        # 使用线程池并发下载
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            futures = {executor.submit(self.download_segment, seg): seg for seg in segments}

            # 使用tqdm显示进度
            with tqdm(total=total_segments, desc="下载进度", unit="片") as pbar:
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    pbar.update(1)

        # 检查是否所有分片都下载成功
        failed = [r for r in results if not r[1]]
        if failed:
            print(f"\n[!] 有 {len(failed)} 个分片下载失败")
            return False

        print("[✓] 所有分片下载完成")
        return True

    def merge_segments(self):
        """合并所有ts分片为MP4文件"""
        output_file = self.output_dir / f"{self.output_name}.mp4"

        print(f"[*] 正在合并分片到: {output_file}")

        # 获取所有ts文件并排序
        ts_files = sorted(self.temp_dir.glob("segment_*.ts"))

        if not ts_files:
            print("[!] 没有找到任何ts分片文件")
            return False

        try:
            # 尝试使用ffmpeg合并（如果可用）
            if self.merge_with_ffmpeg(ts_files, output_file):
                return True

            # 如果ffmpeg不可用，使用二进制合并
            print("[*] FFmpeg不可用，使用二进制合并方式")
            return self.merge_binary(ts_files, output_file)

        except Exception as e:
            print(f"[!] 合并失败: {e}")
            return False

    def merge_with_ffmpeg(self, ts_files, output_file):
        """使用ffmpeg合并ts文件"""
        import subprocess

        try:
            # 创建文件列表
            filelist_path = self.temp_dir / "filelist.txt"
            with open(filelist_path, 'w', encoding='utf-8') as f:
                for ts_file in ts_files:
                    # 使用相对路径或绝对路径
                    f.write(f"file '{ts_file.absolute()}'\n")

            # 使用ffmpeg合并
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(filelist_path),
                '-c', 'copy',
                '-y',  # 覆盖已存在的文件
                str(output_file)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print("[✓] 使用FFmpeg合并完成")
                return True
            else:
                print(f"[!] FFmpeg合并失败: {result.stderr}")
                return False

        except FileNotFoundError:
            print("[!] 未找到FFmpeg，请确保FFmpeg已安装并添加到PATH")
            return False
        except Exception as e:
            print(f"[!] FFmpeg合并出错: {e}")
            return False

    def merge_binary(self, ts_files, output_file):
        """使用二进制方式合并ts文件"""
        try:
            with open(output_file, 'wb') as outfile:
                with tqdm(total=len(ts_files), desc="合并进度", unit="片") as pbar:
                    for ts_file in ts_files:
                        with open(ts_file, 'rb') as infile:
                            outfile.write(infile.read())
                        pbar.update(1)

            print("[✓] 二进制合并完成")
            return True
        except Exception as e:
            print(f"[!] 二进制合并失败: {e}")
            return False

    def cleanup(self):
        """清理临时文件"""
        if not self.temp_dir or not self.temp_dir.exists():
            return

        print("[*] 正在清理临时文件...")
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            print("[✓] 临时文件清理完成")
        except Exception as e:
            print(f"[!] 清理临时文件失败: {e}")

    def download_youtube(self):
        """使用 yt-dlp 命令行工具下载 YouTube 视频"""
        print(f"[*] 检测到 YouTube 视频，使用 yt-dlp 命令行下载最高画质: {self.url}")
        
        # 查找 yt-dlp 可执行文件
        import shutil
        py_dir = Path(sys.executable).parent
        yt_dlp_path = py_dir / 'yt-dlp'
        if sys.platform == 'win32':
            yt_dlp_path = yt_dlp_path.with_suffix('.exe')

        if not yt_dlp_path.exists():
            # 如果 venv 路径下不存在，则回退到在 PATH 中查找
            yt_dlp_path_which = shutil.which('yt-dlp')
            if not yt_dlp_path_which:
                print("[!] yt-dlp 命令未找到。请确保已在虚拟环境中安装 yt-dlp。")
                print("[!] 你可以运行 'venv\\Scripts\\pip.exe install yt-dlp' 来安装。")
                return False
            yt_dlp_path = Path(yt_dlp_path_which)
        
        print(f"[*] 使用 yt-dlp: {yt_dlp_path}")

        # 构建 yt-dlp 命令
        # 文件名模板: golaniyule0   20250214 0 [rG1I_YmRLt8].webm
        # 对应参数:   uploader    upload_date playlist_index id      ext
        output_template = self.output_dir / "%(uploader)s %(upload_date)s %(playlist_index)s [%(id)s].%(ext)s"
        
        cmd = [
            str(yt_dlp_path),
            '--ignore-errors',
            '--format', 'bestvideo+bestaudio/best',
            '--merge-output-format', 'mp4',
            '--output', str(output_template),
        ]

        if self.cookies_file:
            cmd.extend(['--cookies', self.cookies_file])
            print(f"[*] 使用 cookies 文件: {self.cookies_file}")
        
        if self.cookies_from_browser_spec:
            cmd.extend(['--cookies-from-browser', self.cookies_from_browser_spec])
            print(f"[*] 从浏览器导入 cookies: {self.cookies_from_browser_spec}")

        cmd.append(self.url)

        print(f"[*] 执行命令: {' '.join(cmd)}")

        try:
            # 使用 subprocess.Popen 实时输出
            import subprocess
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            rc = process.poll()
            if rc != 0:
                print(f"\n[!] yt-dlp 下载失败，退出码: {rc}")
                return False

        except FileNotFoundError:
            print("[!] yt-dlp 命令未找到。请确保它已安装并在您的系统PATH中。")
            return False
        except Exception as e:
            print(f"\n[!] YouTube 下载时发生错误: {e}")
            return False

        print(f"[✓] 下载完成")
        return True

    def download(self, keep_temp=False):
        """
        执行完整的下载流程

        Args:
            keep_temp: 是否保留临时文件
        """
        try:
            if self.is_youtube:
                return self.download_youtube()

            # 1. 下载并解析m3u8
            playlist = self.download_m3u8()

            # 2. 下载所有分片
            success = self.download_all_segments(playlist)
            if not success:
                print("[!] 分片下载未完全成功")
                return False

            # 3. 合并分片
            success = self.merge_segments()
            if not success:
                print("[!] 分片合并失败")
                return False

            # 4. 清理临时文件
            if not keep_temp:
                self.cleanup()
            else:
                print(f"[*] 临时文件保留在: {self.temp_dir}")

            output_file = self.output_dir / f"{self.output_name}.mp4"
            print(f"\n[✓] 下载完成: {output_file}")
            return True

        except KeyboardInterrupt:
            print("\n[!] 用户中断下载")
            return False
        except Exception as e:
            print(f"\n[!] 下载过程出错: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description='M3U8视频下载器 - 下载m3u8视频流并合并为MP4',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s -u https://example.com/video.m3u8
  %(prog)s -u https://example.com/video.m3u8 -o my_video -d ./videos
  %(prog)s -u https://example.com/video.m3u8 -w 20 --keep-temp
        """
    )

    parser.add_argument('-u', '--url', required=True, help='M3U8播放列表URL')
    parser.add_argument('-o', '--output', help='输出文件名（不含扩展名）')
    parser.add_argument('-d', '--dir', default='downloads', help='输出目录（默认: downloads）')
    parser.add_argument('-w', '--workers', type=int, default=10, help='并发下载线程数（默认: 10）')
    parser.add_argument('--keep-temp', action='store_true', help='保留临时文件')

    parser.add_argument('--cookies', help='Netscape 格式的 cookies 文件路径')
    parser.add_argument('--cookies-from-browser', help='从浏览器导入 cookies，格式: BROWSER[+KEYRING][:PROFILE][::CONTAINER]')
    args = parser.parse_args()

    # 创建下载器实例
    downloader = M3U8Downloader(
        url=args.url,
        output_dir=args.dir,
        output_name=args.output,
        max_workers=args.workers,
        cookies=args.cookies,
        cookies_from_browser=args.cookies_from_browser
    )

    # 执行下载
    success = downloader.download(keep_temp=args.keep_temp)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
