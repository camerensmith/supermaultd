@echo off
"C:\Users\camer\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe" -m pyinstaller --add-data "assets;assets" --add-data "data;data" --collect-all entities --collect-all scenes --collect-all ui --collect-all utils --onedir --contents-directory "." main.py
pause 