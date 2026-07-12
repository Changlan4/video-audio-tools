@echo off
chcp 65001 >nul
echo ====================================
echo   视频音频工具 - PyInstaller 打包
echo ====================================
echo.

pyinstaller --onefile --windowed --add-data "scripts;scripts" --name "视频音频工具" --clean main.py

echo.
echo 打包完成！exe 在 dist\视频音频工具.exe
echo.
pause
