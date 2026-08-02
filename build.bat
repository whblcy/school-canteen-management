@echo off
setlocal

set PYTHON=C:\Users\lcy\AppData\Local\Python\pythoncore-3.14-64\python.exe
set SPEC=学校食堂食材管理系统.spec
set DIST=dist\学校食堂食材管理系统
set ZIP=release\学校食堂食材管理系统.zip

echo 正在清理旧构建...
rmdir /s /q build dist __pycache__ 2>nul

echo 正在使用 SPEC 文件打包...
"%PYTHON%" -m PyInstaller --clean "%SPEC%"

if not exist "%DIST%" (
    echo ? 打包失败，未生成输出目录
    pause
    exit /b 1
)

echo 打包完成！

echo 正在创建压缩包...
powershell -Command "Compress-Archive -Path '%DIST%' -DestinationPath '%ZIP%' -Force"

echo ? 压缩包已创建: %ZIP%
pause