@echo off
chcp 65001 >nul
echo ========================================
echo    HLS-Downloader-Plus 打包工具
echo ========================================
echo.

REM 激活虚拟环境
call venv\Scripts\activate.bat

echo [1/4] 清理旧的打包文件...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec" del /q *.spec

echo.
echo [2/4] 打包批量下载器...
pyinstaller --onefile --windowed ^
    --name "HLS批量下载器" ^
    --icon=NONE ^
    --add-data "README.md;." ^
    m3u8_downloader_batch.py

if errorlevel 1 (
    echo 批量下载器打包失败！
    pause
    exit /b 1
)

echo.
echo [3/4] 打包单个下载器...
pyinstaller --onefile --windowed ^
    --name "HLS下载器" ^
    --icon=NONE ^
    --add-data "README.md;." ^
    m3u8_downloader_gui.py

if errorlevel 1 (
    echo 单个下载器打包失败！
    pause
    exit /b 1
)

echo.
echo [4/4] 整理打包结果...
if not exist "release" mkdir release
copy "dist\HLS批量下载器.exe" "release\"
copy "dist\HLS下载器.exe" "release\"
copy "README.md" "release\"
copy "LICENSE" "release\"

echo.
echo ========================================
echo    打包完成！
echo ========================================
echo.
echo 可执行文件位置：
echo   - release\HLS批量下载器.exe
echo   - release\HLS下载器.exe
echo.
echo 测试提示：
echo   1. 双击运行 release\HLS批量下载器.exe
echo   2. 输入一个M3U8 URL测试下载
echo.
pause
