@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ====================================
echo   M3U8 视频下载器
echo ====================================
echo.

REM 检查虚拟环境是否存在
if not exist "venv\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在！
    echo 请先运行以下命令创建虚拟环境：
    echo    python -m venv venv
    echo    venv\Scripts\activate
    echo    pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM 激活虚拟环境并启动GUI
echo [*] 正在启动下载器...
echo.
venv\Scripts\python.exe m3u8_downloader_gui.py

if errorlevel 1 (
    echo.
    echo [错误] 程序运行失败！
    echo 请确保已安装所有依赖：
    echo    venv\Scripts\activate
    echo    pip install -r requirements.txt
    echo.
    pause
)
