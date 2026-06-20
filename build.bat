@echo off
echo 正在打包学校食堂食材管理系统...
"C:\Users\lcy\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m PyInstaller --onefile --windowed --icon=app_icon.ico --name="学校食堂食材管理系统" --noconfirm main.py
echo 打包完成！
echo 输出文件: dist\学校食堂食材管理系统.exe
pause