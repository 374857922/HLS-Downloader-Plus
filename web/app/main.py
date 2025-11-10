#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HLS-Downloader-Plus Web后端主程序
基于FastAPI的现代化Web界面
"""

import os
import sys
import json
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn
import sqlite3
import uuid
import shutil
from fastapi import UploadFile, File

# 导入现有的下载器
sys.path.append(str(Path(__file__).parent.parent.parent))
from m3u8_downloader_gui import M3U8DownloaderGUI

app = FastAPI(title="HLS-Downloader-Plus Web API", version="4.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class DownloadTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    filename: Optional[str] = None
    output_dir: str = "downloads"
    max_workers: int = 10
    status: str = "pending"  # pending, downloading, completed, failed
    progress: float = 0.0
    speed: str = ""
    downloaded_size: str = ""
    total_size: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class Config(BaseModel):
    download_dir: str = "downloads"
    max_concurrent_downloads: int = 3
    default_threads: int = 10
    use_proxy: bool = False
    proxy_url: str = ""
    cookies_file: str = ""
    cookies_from_browser: str = ""
    theme: str = "dark"  # light, dark, auto

class BrowserCookieRequest(BaseModel):
    browser_spec: str

# 数据库管理
class DatabaseManager:
    def __init__(self, db_path: str = "data/tasks.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                filename TEXT,
                output_dir TEXT NOT NULL,
                max_workers INTEGER DEFAULT 10,
                status TEXT DEFAULT 'pending',
                progress REAL DEFAULT 0.0,
                speed TEXT DEFAULT '',
                downloaded_size TEXT DEFAULT '',
                total_size TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT
            )
        ''')
        
        # 配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 插入默认配置
        default_config = {
            "download_dir": "downloads",
            "max_concurrent_downloads": "3",
            "default_threads": "10",
            "use_proxy": "false",
            "proxy_url": "",
            "cookies_file": "",
            "cookies_from_browser": "",
            "theme": "dark"
        }
        
        for key, value in default_config.items():
            cursor.execute('INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)', (key, value))
        
        conn.commit()
        conn.close()
    
    def get_tasks(self) -> List[DownloadTask]:
        """获取所有任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        tasks = []
        for row in rows:
            task_dict = dict(zip(columns, row))
            tasks.append(DownloadTask(**task_dict))
        
        return tasks
    
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """获取单个任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description] if row else []
        conn.close()
        
        if row and columns:
            task_dict = dict(zip(columns, row))
            return DownloadTask(**task_dict)
        return None

    def get_task_by_url(self, url: str) -> Optional[DownloadTask]:
        """根据URL获取任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE url = ? ORDER BY created_at DESC LIMIT 1', (url,))
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description] if row else []
        conn.close()

        if row and columns:
            task_dict = dict(zip(columns, row))
            return DownloadTask(**task_dict)
        return None
    
    def create_task(self, task: DownloadTask) -> DownloadTask:
        """创建任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (id, url, filename, output_dir, max_workers, status, progress)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (task.id, task.url, task.filename, task.output_dir, task.max_workers, task.status, task.progress))
        
        conn.commit()
        conn.close()
        return task
    
    def update_task(self, task_id: str, **kwargs) -> bool:
        """更新任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        set_clause = ', '.join([f'{key} = ?' for key in kwargs.keys()])
        values = list(kwargs.values()) + [task_id]
        
        cursor.execute(f'UPDATE tasks SET {set_clause} WHERE id = ?', values)
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    def get_config(self) -> Config:
        """获取配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM config')
        config_dict = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        # 类型转换
        config_dict['max_concurrent_downloads'] = int(config_dict.get('max_concurrent_downloads', 3))
        config_dict['default_threads'] = int(config_dict.get('default_threads', 10))
        config_dict['use_proxy'] = config_dict.get('use_proxy', 'false').lower() == 'true'
        
        return Config(**config_dict)
    
    def update_config(self, config: Config) -> bool:
        """更新配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        config_dict = config.dict()
        for key, value in config_dict.items():
            cursor.execute('UPDATE config SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?', (str(value), key))
        
        conn.commit()
        conn.close()
        return True
    
    def save_config(self, key: str, value: str) -> bool:
        """保存单个配置项"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE config SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?', (str(value), key))
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

# 全局实例
db = DatabaseManager()

# WebSocket管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
    
    async def broadcast_progress(self, task_id: str, progress: float, message: str = ""):
        data = {
            "type": "progress", 
            "task_id": task_id,
            "progress": progress,
            "message": message
        }
        
        # 安全地广播到所有连接
        connections_to_remove = []
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    print(f"[DEBUG] WebSocket连接发送失败，准备移除: {e}")
                    connections_to_remove.append(connection)
        
        # 移除失效的连接
        for connection in connections_to_remove:
            await self.disconnect(connection)

manager = ConnectionManager()

# 下载任务管理器
class DownloadManager:
    def __init__(self):
        self.active_downloads: Dict[str, M3U8DownloaderGUI] = {}
        self.semaphore = asyncio.Semaphore(3)  # 最大并发数
    
    def _create_progress_callback(self, task_id: str, loop: asyncio.AbstractEventLoop):
        """创建进度回调函数"""
        def progress_callback(message: str, progress: float = None):
            print(f"[DEBUG] 进度回调: task={task_id}, message={message}, progress={progress}")
            try:
                # 更新数据库
                db.update_task(
                    task_id,
                    progress=progress or 0,
                    speed=message if "速度" in message else "",
                    error_message=message if ("错误" in message or "失败" in message) else None
                )
                print(f"[DEBUG] 数据库更新成功: task={task_id}")
                # 使用线程安全的方式进行WebSocket广播
                if loop and not loop.is_closed():
                    try:
                        asyncio.run_coroutine_threadsafe(
                            manager.broadcast_progress(task_id, progress or 0, message),
                            loop
                        )
                    except Exception as e:
                        print(f"[DEBUG] 广播进度失败: {e}")
                else:
                    print(f"[DEBUG] 事件循环不可用，跳过广播: task={task_id}")
            except Exception as e:
                print(f"[ERROR] 进度回调异常: task={task_id}, error={str(e)}")
        return progress_callback
    
    async def start_download(self, task: DownloadTask):
        """开始下载任务"""
        print(f"[DEBUG] 开始下载任务: {task.id}")
        async with self.semaphore:
            try:
                print(f"[DEBUG] 创建下载器，URL: {task.url}")
                # 更新任务状态
                db.update_task(task.id, status="downloading", started_at=datetime.now())
                try:
                    await manager.broadcast_progress(task.id, 0, "开始下载...")
                except Exception as e:
                    print(f"[DEBUG] WebSocket广播失败: {e}")
                    pass  # 忽略WebSocket连接错误
                
                # 创建下载器
                try:
                    event_loop = asyncio.get_running_loop()
                    # 从配置中读取cookie和代理设置
                    config = db.get_config()

                    downloader = M3U8DownloaderGUI(
                        url=task.url,
                        output_dir=task.output_dir,
                        output_name=task.filename or f"download_{task.id[:8]}",
                        max_workers=task.max_workers,
                        callback=self._create_progress_callback(task.id, event_loop),
                        use_proxy=config.use_proxy,
                        proxy_url=config.proxy_url if config.use_proxy else None,
                        cookies_file=config.cookies_file if config.cookies_file else None,
                        cookies_from_browser=config.cookies_from_browser if config.cookies_from_browser else None
                    )
                    print(f"[DEBUG] 下载器创建成功: {task.id}")
                    print(f"[DEBUG] 代理设置: use_proxy={config.use_proxy}, proxy_url={config.proxy_url}")
                    print(f"[DEBUG] Cookie设置: cookies_file={config.cookies_file}, cookies_from_browser={config.cookies_from_browser}")
                except Exception as e:
                    print(f"[ERROR] 创建下载器失败: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    db.update_task(task.id, status="failed", error_message=f"创建下载器失败: {str(e)}")
                    return
                
                self.active_downloads[task.id] = downloader
                print(f"[DEBUG] 下载器已注册: {task.id}")
                
                # 执行下载
                print(f"[DEBUG] 开始执行下载: {task.id}")
                try:
                    success = await asyncio.get_event_loop().run_in_executor(
                        None, downloader.download
                    )
                    print(f"[DEBUG] 下载执行完成，结果: {success}, 任务: {task.id}")
                    
                    if success:
                        db.update_task(
                            task.id,
                            status="completed",
                            progress=100.0,
                            completed_at=datetime.now()
                        )
                        print(f"[DEBUG] 任务标记为完成: {task.id}")
                        try:
                            await manager.broadcast_progress(task.id, 100, "下载完成！")
                        except Exception as e:
                            print(f"[DEBUG] 完成状态广播失败: {e}")
                            pass  # 忽略WebSocket连接错误
                    else:
                        print(f"[DEBUG] 下载失败，任务: {task.id}")
                        db.update_task(
                            task.id,
                            status="failed",
                            error_message="下载失败"
                        )
                        try:
                            await manager.broadcast_progress(task.id, task.progress, "下载失败")
                        except Exception as e:
                            print(f"[DEBUG] 失败状态广播失败: {e}")
                            pass  # 忽略WebSocket连接错误
                
                except Exception as download_error:
                    print(f"[ERROR] 下载执行异常: {str(download_error)}, 任务: {task.id}")
                    import traceback
                    traceback.print_exc()
                    db.update_task(
                        task.id,
                        status="failed",
                        error_message=f"执行下载时出错: {str(download_error)}"
                    )
                    try:
                        await manager.broadcast_progress(task.id, task.progress, f"错误: {str(download_error)}")
                    except Exception as e:
                        print(f"[DEBUG] 异常状态广播失败: {e}")
                        pass  # 忽略WebSocket连接错误
                
            except Exception as e:
                print(f"[ERROR] 下载任务处理异常: {str(e)}, 任务: {task.id}")
                import traceback
                traceback.print_exc()
                db.update_task(
                    task.id,
                    status="failed",
                    error_message=f"任务处理出错: {str(e)}"
                )
                try:
                    await manager.broadcast_progress(task.id, task.progress, f"错误: {str(e)}")
                except Exception as e:
                    print(f"[DEBUG] 异常状态广播失败: {e}")
                    pass  # 忽略WebSocket连接错误
            finally:
                # 清理
                if task.id in self.active_downloads:
                    del self.active_downloads[task.id]

download_manager = DownloadManager()

# API路由
@app.get("/api/tasks", response_model=List[DownloadTask])
async def get_tasks():
    """获取所有下载任务"""
    return db.get_tasks()

@app.get("/api/tasks/{task_id}", response_model=DownloadTask)
async def get_task(task_id: str):
    """获取单个任务"""
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

@app.post("/api/tasks", response_model=DownloadTask)
async def create_task(task: DownloadTask, background_tasks: BackgroundTasks):
    """创建下载任务"""
    print(f"[DEBUG] 收到创建任务请求: URL={task.url}, filename={task.filename}")
    
    # 验证URL
    if not task.url:
        print("[ERROR] URL为空")
        raise HTTPException(status_code=400, detail="URL不能为空")
    
    # 验证URL格式
    if not task.url.startswith(('http://', 'https://')):
        print(f"[ERROR] URL格式无效: {task.url}")
        raise HTTPException(status_code=400, detail="URL格式无效，必须以http://或https://开头")

    # 检查重复任务
    existing_task = db.get_task_by_url(task.url)
    if existing_task:
        print(f"[ERROR] URL重复: {task.url}, status={existing_task.status}")
        raise HTTPException(status_code=409, detail="该URL已在下载列表中，请勿重复添加")
    
    # 创建任务
    try:
        task.status = "pending"
        task.progress = 0.0
        db_task = db.create_task(task)
        print(f"[DEBUG] 数据库任务创建成功: {db_task.id}")
    except Exception as e:
        print(f"[ERROR] 创建数据库任务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")
    
    # 后台执行下载
    print(f"[DEBUG] 开始后台下载任务: {db_task.id}, URL: {db_task.url}")
    try:
        background_tasks.add_task(download_manager.start_download, db_task)
        print(f"[DEBUG] 下载任务已添加到后台队列: {db_task.id}")
    except Exception as e:
        print(f"[ERROR] 添加后台任务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.update_task(db_task.id, status="failed", error_message=f"创建后台任务失败: {str(e)}")
    
    return db_task

@app.put("/api/tasks/{task_id}")
async def update_task(task_id: str, status: str):
    """更新任务状态"""
    if status not in ["pending", "downloading", "completed", "failed"]:
        raise HTTPException(status_code=400, detail="无效的状态")
    
    success = db.update_task(task_id, status=status)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {"message": "任务更新成功"}

@app.put("/api/tasks/{task_id}/pause")
async def pause_task(task_id: str):
    """暂停单个任务"""
    success = db.update_task(task_id, status="paused")
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {"message": "任务已暂停"}

@app.put("/api/tasks/{task_id}/resume") 
async def resume_task(task_id: str, background_tasks: BackgroundTasks):
    """继续单个任务"""
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 更新任务状态为pending，然后重新启动
    db.update_task(task_id, status="pending")
    background_tasks.add_task(download_manager.start_download, task)
    
    return {"message": "任务已继续"}

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    success = db.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {"message": "任务删除成功"}

@app.get("/api/config")
async def get_config():
    """获取系统配置"""
    config = db.get_config()
    return {"success": True, "config": config}

@app.put("/api/config/model")
async def update_config_model(config: Config):
    """通过模型更新系统配置"""
    db.update_config(config)
    return {"success": True, "message": "配置更新成功"}

# WebSocket连接
@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await manager.connect(websocket)
        print("[DEBUG] WebSocket连接已建立")
        
        # 保持连接活跃
        while True:
            try:
                # 等待客户端消息或心跳
                data = await websocket.receive_text()
                # 可以在这里处理客户端发送的消息
                print(f"[DEBUG] 收到WebSocket消息: {data}")
            except Exception as e:
                print(f"[DEBUG] WebSocket接收消息异常: {e}")
                break
    except WebSocketDisconnect:
        print("[DEBUG] WebSocket客户端断开连接")
    except Exception as e:
        print(f"[DEBUG] WebSocket端点异常: {e}")
    finally:
        await manager.disconnect(websocket)
        print("[DEBUG] WebSocket连接已清理")

# 静态文件服务（HTML前端文件）
frontend_path = Path(__file__).parent / "../frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")

# 文件管理API
@app.get("/api/files")
async def get_files():
    """获取下载文件列表"""
    try:
        download_dir = Path(db.get_config().download_dir)
        if not download_dir.exists():
            return []
        
        files = []
        for file_path in download_dir.glob("*"):
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime,
                    "path": str(file_path)
                })
        
        return sorted(files, key=lambda x: x["modified"], reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """删除文件"""
    try:
        download_dir = Path(db.get_config().download_dir)
        file_path = download_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        file_path.unlink()
        return {"message": "文件删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

@app.get("/api/files/{filename}/download")
async def download_file(filename: str):
    """下载文件"""
    try:
        download_dir = Path(db.get_config().download_dir)
        file_path = download_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        from fastapi.responses import FileResponse
        return FileResponse(file_path, filename=filename)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")

# Cookie相关API
@app.post("/api/cookies/upload")
async def upload_cookies_file(file: UploadFile = File(...)):
    """上传Cookie文件"""
    try:
        # 确保cookies目录存在
        os.makedirs("data/cookies", exist_ok=True)
        
        # 保存上传的文件
        file_path = f"data/cookies/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 验证Cookie文件格式
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip().startswith('# Netscape HTTP Cookie File'):
                    os.remove(file_path)
                    return {"success": False, "message": "无效的Cookie文件格式"}
        except:
            os.remove(file_path)
            return {"success": False, "message": "Cookie文件读取失败"}
        
        # 保存文件路径到配置
        db.save_config("cookies_file", file_path)
        
        return {"success": True, "message": "Cookie文件上传成功", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传Cookie文件失败: {str(e)}")

@app.post("/api/cookies/browser")
async def import_browser_cookies(request: BrowserCookieRequest):
    """从浏览器导入Cookie"""
    try:
        browser_spec = request.browser_spec
        if not browser_spec:
            return {"success": False, "message": "请指定浏览器类型"}
        
        # 这里需要实现从浏览器导入Cookie的逻辑
        # 实际使用yt_dlp的Cookie加载功能
        from yt_dlp.cookies import load_cookies
        
        cookie_jar = load_cookies(None, browser_spec, None)
        if not cookie_jar:
            return {"success": False, "message": "无法从浏览器导入Cookie"}
        
        # 保存Cookie到文件
        cookie_file_path = "data/cookies/browser_cookies.txt"
        cookie_jar.save(cookie_file_path)
        
        # 更新配置
        db.save_config("cookies_from_browser", browser_spec)
        
        return {
            "success": True, 
            "message": f"从{browser_spec}导入Cookie成功", 
            "file_path": cookie_file_path,
            "cookie_count": len(cookie_jar)
        }
    except ImportError:
        return {"success": False, "message": "需要安装yt-dlp: pip install yt-dlp"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入浏览器Cookie失败: {str(e)}")



# 批量操作API
@app.post("/api/tasks/start")
async def start_all_downloads(background_tasks: BackgroundTasks):
    """开始所有待处理的下载任务"""
    try:
        # 获取所有等待中的任务
        tasks = db.get_tasks()
        pending_tasks = [task for task in tasks if task.status in ["pending", "failed"]]
        
        if not pending_tasks:
            return {"success": False, "message": "没有待处理的任务"}
        
        # 启动后台任务处理所有等待中的任务
        for task in pending_tasks:
            background_tasks.add_task(download_manager.start_download, task)
        
        return {"success": True, "message": f"已开始处理 {len(pending_tasks)} 个任务"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"开始任务失败: {str(e)}")

@app.post("/api/tasks/pause")
async def pause_all_downloads():
    """暂停所有下载任务"""
    try:
        tasks = db.get_tasks()
        downloading_tasks = [task for task in tasks if task.status == "downloading"]
        
        if not downloading_tasks:
            return {"success": False, "message": "没有正在下载的任务"}
        
        # 更新所有正在下载的任务状态为暂停
        for task in downloading_tasks:
            db.update_task(task.id, status="paused")
        
        return {"success": True, "message": f"已暂停 {len(downloading_tasks)} 个任务"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"暂停任务失败: {str(e)}")

@app.post("/api/tasks/resume")
async def resume_all_downloads(background_tasks: BackgroundTasks):
    """继续所有暂停的下载任务"""
    try:
        tasks = db.get_tasks()
        paused_tasks = [task for task in tasks if task.status == "paused"]
        
        if not paused_tasks:
            return {"success": False, "message": "没有暂停的任务"}
        
        # 重新启动暂停的任务
        for task in paused_tasks:
            db.update_task(task.id, status="pending")
            background_tasks.add_task(download_manager.start_download, task)
        
        return {"success": True, "message": f"已继续 {len(paused_tasks)} 个任务"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"继续任务失败: {str(e)}")

@app.delete("/api/tasks/clear/completed")
async def clear_completed_tasks():
    """清除所有已完成的任务"""
    try:
        tasks = db.get_tasks()
        completed_tasks = [task for task in tasks if task.status == "completed"]
        
        if not completed_tasks:
            return {"success": False, "message": "没有已完成的任务"}
        
        # 删除已完成的任务
        for task in completed_tasks:
            db.delete_task(task.id)
        
        return {"success": True, "message": f"已清除 {len(completed_tasks)} 个已完成任务"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除任务失败: {str(e)}")

@app.delete("/api/tasks/clear")
async def clear_all_tasks():
    """清空所有任务"""
    try:
        tasks = db.get_tasks()
        
        if not tasks:
            return {"success": False, "message": "任务列表已经为空"}
        
        # 删除所有任务
        for task in tasks:
            db.delete_task(task.id)
        
        return {"success": True, "message": f"已清空所有任务（共 {len(tasks)} 个）"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空任务失败: {str(e)}")

@app.post("/api/config")
async def update_config(config_data: Dict[str, str]):
    """更新配置"""
    try:
        for key, value in config_data.items():
            db.save_config(key, value)
        
        # 重新加载配置
        global_config = db.get_config()
        return {"success": True, "message": "配置更新成功", "config": global_config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

@app.post("/api/config/export")
async def export_config():
    """导出配置为JSON"""
    try:
        config_model = db.get_config()
        config_dict = config_model.dict()
        
        import io
        from fastapi.responses import StreamingResponse
        
        # 创建JSON字符串
        config_json = json.dumps(config_dict, indent=2, ensure_ascii=False)
        
        # 创建文件流
        buffer = io.StringIO(config_json)
        
        return StreamingResponse(
            io.BytesIO(buffer.getvalue().encode()),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=config.json"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出配置失败: {str(e)}")

@app.post("/api/config/import")
async def import_config(file: UploadFile = File(...)):
    """导入配置文件"""
    try:
        content = await file.read()
        config_data = json.loads(content.decode('utf-8'))
        
        # 验证配置数据
        if not isinstance(config_data, dict):
            return {"success": False, "message": "无效的配置文件格式"}
        
        # 保存配置
        for key, value in config_data.items():
            if key == 'cookies_file' and value and os.path.exists(value):
                # Cookie文件特殊处理
                continue
            db.save_config(key, value)
        
        return {"success": True, "message": "配置导入成功"}
    except json.JSONDecodeError:
        return {"success": False, "message": "配置文件JSON格式错误"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入配置失败: {str(e)}")

if __name__ == "__main__":
    # 确保必要的目录存在
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/cookies", exist_ok=True)
    
    print("🚀 HLS-Downloader-Plus Web服务启动中...")
    print("📍 访问地址: http://localhost:8080")
    print("📍 API文档: http://localhost:8080/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
