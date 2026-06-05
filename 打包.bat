@echo off
chcp 65001 >nul
echo ========================================
echo    打包 AI 同声传译助手
echo ========================================
echo.

echo [1/3] 安装打包工具...
pip install pyinstaller

echo.
echo [2/3] 打包中...
pyinstaller --onefile --windowed --name "AI同声传译助手" launcher.py

echo.
echo [3/3] 复制依赖文件...
xcopy /E /I backend dist\backend
xcopy /E /I frontend dist\frontend
copy 启动.bat dist\

echo.
echo ========================================
echo    打包完成！
echo ========================================
echo.
echo    生成文件在 dist 目录中
echo.
pause
