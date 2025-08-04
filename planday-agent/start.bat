@echo off
REM =============================================================================
REM PlanDay 一键启动脚本 (Windows版本)
REM =============================================================================

setlocal enabledelayedexpansion

REM 颜色设置 (Windows 10+)
for /f %%A in ('echo prompt $E^| cmd') do set "ESC=%%A"
set "RED=%ESC%[91m"
set "GREEN=%ESC%[92m"
set "YELLOW=%ESC%[93m"
set "BLUE=%ESC%[94m"
set "CYAN=%ESC%[96m"
set "NC=%ESC%[0m"

REM 项目目录
set "PROJECT_ROOT=%~dp0"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"
set "BACKEND_DIR=%PROJECT_ROOT%"

echo %CYAN%
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                      🚀 PlanDay 启动器                        ║
echo ║                  AI 智能日程助手 - 一键启动                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo %NC%

echo %GREEN%[%time%] 开始启动 PlanDay 应用...%NC%

REM 检查依赖
echo %BLUE%[%time%] 检查系统依赖...%NC%

where python >nul 2>nul
if errorlevel 1 (
    echo %RED%[%time%] ❌ Python 未安装，请先安装 Python 3.8+%NC%
    pause
    exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
    echo %RED%[%time%] ❌ Node.js 未安装，请先安装 Node.js 16+%NC%
    pause
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo %RED%[%time%] ❌ npm 未安装，请先安装 npm%NC%
    pause
    exit /b 1
)

where uv >nul 2>nul
if errorlevel 1 (
    echo %YELLOW%[%time%] ⚠️  uv 未安装，尝试使用 pip 安装依赖...%NC%
    set "USE_UV=false"
) else (
    echo %GREEN%[%time%] ✅ uv 已安装%NC%
    set "USE_UV=true"
)

echo %GREEN%[%time%] ✅ 依赖检查完成%NC%

REM 设置环境变量
if not defined OPENAI_API_KEY (
    set "OPENAI_API_KEY=sk-zUbEOQKhP8qYdpBx3542494939Fe4bAf95Fd195c906d8695"
    echo %YELLOW%[%time%] ⚠️  使用默认 OPENAI_API_KEY%NC%
)

if not defined OPENAI_BASE_URL (
    set "OPENAI_BASE_URL=https://free.v36.cm/v1"
    echo %YELLOW%[%time%] ⚠️  使用默认 OPENAI_BASE_URL%NC%
)

if not defined MODEL_NAME (
    set "MODEL_NAME=gpt-4o-mini"
)

REM 安装后端依赖
echo %BLUE%[%time%] 安装后端依赖...%NC%
cd /d "%BACKEND_DIR%"

if "%USE_UV%"=="true" (
    uv sync
) else (
    pip install -r requirements.txt 2>nul || (
        echo %YELLOW%[%time%] requirements.txt 不存在，跳过 pip 安装%NC%
    )
)

if errorlevel 1 (
    echo %RED%[%time%] ❌ 后端依赖安装失败%NC%
    pause
    exit /b 1
)

echo %GREEN%[%time%] ✅ 后端依赖安装完成%NC%

REM 安装前端依赖
echo %BLUE%[%time%] 检查前端依赖...%NC%
cd /d "%FRONTEND_DIR%"

if not exist "node_modules" (
    echo %BLUE%[%time%] 安装前端依赖...%NC%
    npm install
    if errorlevel 1 (
        echo %RED%[%time%] ❌ 前端依赖安装失败%NC%
        pause
        exit /b 1
    )
) else (
    echo %GREEN%[%time%] ✅ 前端依赖已存在%NC%
)

REM 启动后端
echo %BLUE%[%time%] 启动后端服务...%NC%
cd /d "%BACKEND_DIR%"

if "%USE_UV%"=="true" (
    start "PlanDay Backend" cmd /c "uv run python run.py"
) else (
    start "PlanDay Backend" cmd /c "python run.py"
)

echo %GREEN%[%time%] ✅ 后端服务启动中...%NC%

REM 等待后端启动
timeout /t 5 /nobreak >nul

REM 启动前端
echo %BLUE%[%time%] 启动前端服务...%NC%
cd /d "%FRONTEND_DIR%"

start "PlanDay Frontend" cmd /c "npm start"

echo %GREEN%[%time%] ✅ 前端服务启动中...%NC%

REM 等待服务启动
echo %BLUE%[%time%] 等待服务完全启动...%NC%
timeout /t 10 /nobreak >nul

echo.
echo %GREEN%╔══════════════════════════════════════════════════════════════╗%NC%
echo %GREEN%║                     🎉 启动成功！                              ║%NC%
echo %GREEN%╠══════════════════════════════════════════════════════════════╣%NC%
echo %GREEN%║  前端地址: %CYAN%http://localhost:3000%GREEN%                         ║%NC%
echo %GREEN%║  后端地址: %CYAN%http://localhost:8000%GREEN%                         ║%NC%
echo %GREEN%║                                                              ║%NC%
echo %GREEN%║  🌐 浏览器将自动打开前端页面                                    ║%NC%
echo %GREEN%║  📱 如果没有自动打开，请手动访问上述地址                          ║%NC%
echo %GREEN%║                                                              ║%NC%
echo %GREEN%║  关闭此窗口不会停止服务                                         ║%NC%
echo %GREEN%║  要停止服务，请关闭对应的终端窗口                               ║%NC%
echo %GREEN%╚══════════════════════════════════════════════════════════════╝%NC%

REM 尝试打开浏览器
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
echo %CYAN%[%time%] 按任意键退出此窗口...%NC%
pause >nul

endlocal