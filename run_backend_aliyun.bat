@echo off
chcp 65001 >nul
set "PATH=E:\anacodna;E:\anacodna\Library\bin;C:\Windows\System32;C:\Windows;C:\Windows\System32\Wbem;%PATH%"
cd /d "%~dp0backend"
"E:\anacodna\python.exe" main.py
