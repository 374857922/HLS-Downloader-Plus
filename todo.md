# M3U8下载器 - 功能完善清单

## 📊 代码完善度评估

### ✅ 已完整支持的功能（覆盖90%常见场景）

1. **基础下载** - 标准HLS/M3U8播放列表 ✓
2. **AES-128加密** - 自动检测并解密 ✓
3. **多码率自动选择** - 检测Master Playlist并选择第一个 ✓
4. **并发下载** - 多线程加速 ✓
5. **智能合并** - FFmpeg优先，回退到二进制合并 ✓
6. **错误重试** - 最多3次重试 ✓
7. **代理支持** - HTTP/HTTPS代理（GUI版本）✓
8. **URL伪装处理** - 忽略扩展名，按内容处理 ✓

### ⚠️ 缺失的高级功能（影响<10%的特殊场景）

| 功能 | 影响场景 | 优先级 |
|------|---------|--------|
| **ByteRange支持** | 部分流使用字节范围下载单个大文件的片段 | 🟡 中 |
| **fMP4/CMAF格式** | 需要处理`EXT-X-MAP`初始化段 | 🟡 中 |
| **Discontinuity处理** | 广告插入、编码变化的流 | 🟢 低 |
| **实时流(Live)** | 正在直播的流（无`EXT-X-ENDLIST`）| 🟢 低 |
| **多音轨/字幕** | `EXT-X-MEDIA`标签的备用音轨 | 🟢 低 |
| **其他加密** | SAMPLE-AES, AES-CTR等 | 🟢 低 |
| **多码率手动选择** | 让用户选择最佳码率 | 🟢 低 |

---

## 🎯 优化建议（按优先级排序）

### 1. ByteRange支持（中优先级）

**场景**：部分流媒体服务将所有片段存储在一个大文件中，通过字节范围请求不同片段

**实现方案**：
```python
# 在download_segment方法中添加：
if segment.byterange:
    # 解析byterange：格式为 "length@offset" 或 "length"
    if '@' in segment.byterange:
        length, offset = segment.byterange.split('@')
        offset = int(offset)
    else:
        length = segment.byterange
        offset = 0  # 或使用上一个segment的结束位置

    # 设置Range头
    range_header = f'bytes={offset}-{offset + int(length) - 1}'
    headers = {**self.headers, 'Range': range_header}
    response = requests.get(segment_url, headers=headers, ...)
```

**修改文件**：
- `m3u8_downloader.py`
- `m3u8_downloader_batch.py`
- `m3u8_downloader_gui.py`

---

### 2. fMP4/CMAF格式支持（中优先级）

**场景**：现代流媒体服务（Netflix、YouTube等）使用fMP4格式，需要初始化段

**实现方案**：
```python
def download_init_section(self, playlist):
    """下载fMP4初始化段"""
    if not playlist.segment_map:
        return None

    init_segment = playlist.segment_map[0]
    init_url = urljoin(self.url, init_segment.uri)

    # 下载初始化段
    response = requests.get(init_url, headers=self.headers, timeout=30)
    response.raise_for_status()

    # 处理ByteRange
    if init_segment.byterange:
        # ... ByteRange处理逻辑
        pass

    return response.content

# 在merge方法中：
def merge_fmp4(self, ts_files, init_data, output_file):
    """合并fMP4格式"""
    with open(output_file, 'wb') as outfile:
        # 写入初始化段
        if init_data:
            outfile.write(init_data)

        # 写入所有片段
        for ts_file in ts_files:
            with open(ts_file, 'rb') as infile:
                outfile.write(infile.read())
```

**修改文件**：
- `m3u8_downloader.py`
- `m3u8_downloader_batch.py`
- `m3u8_downloader_gui.py`

---

### 3. 实时流(Live)支持（低优先级）

**场景**：下载正在直播的流（无`EXT-X-ENDLIST`标签）

**实现方案**：
```python
def download_live_stream(self, duration_minutes=None):
    """下载实时流"""
    downloaded_segments = set()
    start_time = datetime.now()

    while True:
        playlist = self.download_m3u8()

        if playlist.is_endlist:
            print("[*] 直播已结束")
            break

        # 下载新片段
        for i, segment in enumerate(playlist.segments):
            segment_id = (segment.uri, i)
            if segment_id not in downloaded_segments:
                self.download_segment((i, segment))
                downloaded_segments.add(segment_id)

        # 检查是否达到时长限制
        if duration_minutes:
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            if elapsed >= duration_minutes:
                break

        # 等待几秒后刷新
        time.sleep(playlist.target_duration or 2)
```

**修改文件**：
- `m3u8_downloader.py`（新增方法）

---

### 4. Discontinuity处理（低优先级）

**场景**：流中包含广告或编码变化时，会有`EXT-X-DISCONTINUITY`标签

**实现方案**：
```python
# m3u8库已经支持discontinuity属性
# 在合并时需要特别处理

def merge_with_discontinuity(self, segments):
    """处理不连续的片段"""
    current_batch = []
    all_batches = []

    for segment in segments:
        if segment.discontinuity:
            # 遇到不连续标记，先合并当前批次
            if current_batch:
                all_batches.append(current_batch)
            current_batch = [segment]
        else:
            current_batch.append(segment)

    if current_batch:
        all_batches.append(current_batch)

    # 使用FFmpeg合并各批次
    # FFmpeg能更好地处理不连续的片段
```

**建议**：使用FFmpeg合并可以自动处理大部分discontinuity问题，不需要特殊处理

---

### 5. 多码率手动选择（低优先级）

**场景**：让用户选择下载哪个码率，而不是默认第一个

**实现方案**：
```python
def download_m3u8(self):
    """下载并解析m3u8播放列表"""
    # ... 现有代码 ...

    # 如果是主播放列表
    if playlist.is_variant:
        print("[*] 检测到多码率播放列表：")
        for i, p in enumerate(playlist.playlists):
            bandwidth = p.stream_info.bandwidth
            resolution = p.stream_info.resolution
            print(f"  [{i}] 码率: {bandwidth/1000:.0f}kbps, 分辨率: {resolution}")

        # 让用户选择（GUI版本可以用下拉框）
        choice = int(input("请选择码率 [0]: ") or "0")
        variant_url = urljoin(self.url, playlist.playlists[choice].uri)
        # ... 继续处理 ...
```

**修改文件**：
- `m3u8_downloader.py`（CLI版本用input）
- `m3u8_downloader_gui.py`（GUI版本用下拉框）

---

### 6. 其他加密方式支持（低优先级）

**场景**：SAMPLE-AES（音频采样加密）、AES-CTR等

**实现方案**：
```python
def decrypt_segment(self, data, key_bytes, iv_bytes, segment_index, method='AES-128'):
    """解密TS分片"""
    if not key_bytes:
        return data

    try:
        if iv_bytes is None:
            iv_bytes = segment_index.to_bytes(16, byteorder='big')

        # 根据加密方法选择解密模式
        if method == 'AES-128':
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        elif method == 'AES-CTR':
            cipher = AES.new(key_bytes, AES.MODE_CTR, nonce=iv_bytes[:8])
        elif method == 'SAMPLE-AES':
            # SAMPLE-AES比较复杂，需要特殊处理
            return self.decrypt_sample_aes(data, key_bytes, iv_bytes)
        else:
            print(f"[!] 不支持的加密方法: {method}")
            return data

        decrypted_data = cipher.decrypt(data)

        # 移除PKCS7填充（仅CBC模式）
        if method == 'AES-128':
            try:
                decrypted_data = unpad(decrypted_data, AES.block_size)
            except ValueError:
                pass

        return decrypted_data
    except Exception as e:
        print(f"[!] 解密分片失败: {e}")
        return data
```

**注意**：SAMPLE-AES非常复杂，需要解析TS包结构

---

### 7. 多音轨/字幕支持（低优先级）

**场景**：下载备用音轨或字幕流

**实现方案**：
```python
def list_alternative_media(self, playlist):
    """列出所有备用媒体流"""
    if not playlist.media:
        return []

    alternatives = []
    for media in playlist.media:
        alternatives.append({
            'type': media.type,  # AUDIO, SUBTITLES, VIDEO
            'language': media.language,
            'name': media.name,
            'uri': media.uri
        })

    return alternatives

def download_alternative_stream(self, media_uri):
    """下载备用流"""
    # 类似主流下载逻辑
    pass
```

**修改文件**：
- `m3u8_downloader.py`（新增功能）

---

## 📈 当前结论

**你的代码已经能处理绝大多数M3U8下载场景！** 包括：
- ✅ 普通视频网站的VOD内容
- ✅ AES加密的付费内容
- ✅ 各种URL伪装
- ✅ 多码率自适应流

**只有极少数特殊情况可能失败**：
- ❌ 使用ByteRange的大文件分片
- ❌ 新型fMP4/CMAF格式（Netflix、YouTube等）
- ❌ 正在直播的实时流

---

## 💡 实施建议

### 短期（推荐立即实施）
- 继续使用现有代码，覆盖90%的场景
- 遇到失败时分析M3U8内容，确定需要哪个功能

### 中期（遇到问题再实施）
- 如果遇到ByteRange场景，添加ByteRange支持
- 如果遇到fMP4格式，添加初始化段支持

### 长期（可选）
- 添加实时流支持（如果需要下载直播）
- 添加多码率选择（提升用户体验）
- 添加多音轨/字幕支持（完整性）

---

## 📝 已知问题

### 问题1：二进制合并可能导致播放问题
- **现象**：某些播放器无法正确识别
- **原因**：简单的二进制拼接不会重建TS包的PAT/PMT
- **解决**：优先使用FFmpeg合并，避免二进制合并

### 问题2：密钥URL可能失效
- **现象**：加密视频的密钥URL有时效性
- **原因**：服务器设置了auth_key等时效参数
- **解决**：尽快下载，或者保存M3U8文件中的密钥URL

### 问题3：某些网站有反爬限制
- **现象**：频繁请求被封禁
- **原因**：User-Agent检测、IP限流等
- **解决**：降低并发数、添加延迟、使用代理

---

## 🔧 技术债务

1. **错误处理**：可以更细化（区分网络错误、解密错误等）
2. **日志系统**：可以添加详细日志级别（DEBUG/INFO/ERROR）
3. **配置文件**：将User-Agent、超时时间等抽取到配置文件
4. **单元测试**：添加测试用例确保功能稳定性
5. **性能优化**：大文件下载可以考虑流式写入而非全部加载到内存

---

## 📚 参考资料

- [HLS RFC 8216](https://tools.ietf.org/html/rfc8216) - HLS协议标准
- [Python m3u8库文档](https://github.com/globocom/m3u8)
- [FFmpeg HLS支持](https://ffmpeg.org/ffmpeg-formats.html#hls-2)
- [AES加密模式说明](https://en.wikipedia.org/wiki/Block_cipher_mode_of_operation)

---

*最后更新：2025-10-03*
