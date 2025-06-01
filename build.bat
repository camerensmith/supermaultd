@echo off
"C:\Users\camer\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\python.exe" -m PyInstaller --onefile --windowed --add-data "assets;assets" --add-data "data;data" --icon "assets/images/supermaultd.png" main.py
pause 