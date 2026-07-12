@echo off
echo 正在打包学校食堂食材管理系统...
"C:\Users\lcy\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m PyInstaller --windowed --icon=app_icon.ico --name="学校食堂食材管理系统" --noconfirm main.py
echo 打包完成！
echo 正在创建压缩包...
powershell -Command "Compress-Archive -Path 'dist\学校食堂食材管理系统' -DestinationPath 'release\学校食堂食材管理系统.zip' -Force"
echo 压缩包已创建: release\学校食堂食材管理系统.zip
pause