@echo off
setlocal enabledelayedexpansion
echo 正在批量删除MP4文件名前缀 [1] ...
echo.

:: 遍历当前文件夹所有 MP4 文件
for %%f in (*.mp4) do (
    set "oldName=%%~nf"
    set "ext=%%~xf"
    
    :: 只删除【开头】的 [1]，不影响中间/结尾的 [1]
    if "!oldName:~0,3!"=="[1]" (
        set "newName=!oldName:~3!!ext!"
        ren "%%f" "!newName!"
        echo 已重命名：%%f → !newName!
    )
)

echo.
echo ==========================
echo 全部处理完成！
echo ==========================
pause
