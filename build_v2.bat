@echo off
setlocal

REM 优先使用项目自带的虚拟环境，否则回退到 PATH 中的 python
REM （原 build.bat 硬编码了 C:\Users\lcy\AppData\Local\Python\pythoncore-3.14-64，
REM   换机器/换环境即失效，这里改为可移植写法）
if exist venv\Scripts\python.exe (
    set PYTHON=venv\Scripts\python.exe
) else (
    set PYTHON=python
)

set SPEC=school-canteen-v2.spec
set DIST=dist\学校食堂食材管理系统V2
set ZIP=release\学校食堂食材管理系统V2.zip

echo 正在清理旧构建...
rmdir /s /q build dist __pycache__ 2>nul

echo 正在使用 SPEC 文件打包 V2...
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
