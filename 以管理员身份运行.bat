@echo off
chcp 65001 >nul
:: 以管理员身份运行应用程序
:: 这样可以获得窗口置顶的权限

echo ========================================
echo   DNA Automator - 管理员模式启动
echo ========================================
echo.
echo 正在以管理员权限启动应用...
echo 这样可以确保窗口置顶功能正常工作
echo.

:: 检查是否已经是管理员权限
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] 已获得管理员权限
    echo.
    echo 正在启动应用...
    npm run dev
) else (
    echo [提示] 需要管理员权限
    echo 请在弹出的UAC对话框中点击"是"
    echo.
    pause
    
    :: 请求管理员权限并重新运行
    powershell -Command "Start-Process cmd -ArgumentList '/c chcp 65001 >nul & cd /d %CD% && npm run dev && pause' -Verb RunAs"
)
