@echo off
chcp 65001 >nul
set "PATH=C:\Program Files\nodejs;C:\Windows\System32;C:\Windows;C:\Windows\System32\Wbem;%PATH%"
cd /d "%~dp0frontend"
"C:\Program Files\nodejs\node.exe" ".\node_modules\vite\bin\vite.js" --host 127.0.0.1
