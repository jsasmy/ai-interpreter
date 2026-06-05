@echo off
chcp 65001 >nul
title AI 同声传译助手

echo ========================================
echo    AI 同声传译助手 启动中...
echo ========================================
echo.

:: 启动后端
echo [1/2] 启动后端服务 (端口 9000)...
cd /d "%~dp0backend"
start /b "Backend" python main.py
timeout /t 3 /nobreak >nul

:: 启动前端
echo [2/2] 启动前端服务 (端口 3001)...
cd /d "%~dp0frontend"
start /b "Frontend" npm run dev
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo    启动完成！
echo ========================================
echo.
echo    前端地址: http://localhost:3001
echo    后端地址: http://localhost:9000
echo.
echo    正在打开浏览器...
start http://localhost:3001

echo.
echo    按任意键停止所有服务...
pause >nul

:: 停止服务
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
echo    服务已停止
pause
