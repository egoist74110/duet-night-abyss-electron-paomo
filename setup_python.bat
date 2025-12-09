@echo off
setlocal enabledelayedexpansion

echo ================================
echo Embedded Python Setup
echo ================================
echo.

cd /d "%~dp0"

REM Python版本配置
set PYTHON_VERSION=3.11.7
set PYTHON_EMBED_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip
set PYTHON_DIR=python
set GET_PIP_URL=https://bootstrap.pypa.io/get-pip.py

REM 检查python目录是否存在
if exist %PYTHON_DIR% (
    echo [INFO] Python directory already exists
    goto :install_deps
)

echo [STEP 1/4] Creating Python directory...
mkdir %PYTHON_DIR%

echo [STEP 2/4] Downloading Python embeddable package...
echo URL: %PYTHON_EMBED_URL%
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_EMBED_URL%' -OutFile 'python.zip'}"

if not exist python.zip (
    echo [ERROR] Failed to download Python
    echo Please download manually from: %PYTHON_EMBED_URL%
    pause
    exit /b 1
)

echo [STEP 3/4] Extracting Python...
powershell -Command "Expand-Archive -Path 'python.zip' -DestinationPath '%PYTHON_DIR%' -Force"
del python.zip

REM 修改python311._pth文件以启用site-packages
echo [INFO] Configuring Python paths...
(
    echo python311.zip
    echo .
    echo .
    echo # Uncomment to run site.main^(^) automatically
    echo import site
) > %PYTHON_DIR%\python311._pth

echo [STEP 4/4] Installing pip...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%GET_PIP_URL%' -OutFile 'get-pip.py'}"
%PYTHON_DIR%\python.exe get-pip.py
del get-pip.py

:install_deps
echo.
echo ================================
echo Installing Python Dependencies
echo ================================
echo.

REM 安装依赖
%PYTHON_DIR%\python.exe -m pip install --upgrade pip
%PYTHON_DIR%\python.exe -m pip install -r py_engine\requirements.txt

echo.
echo ================================
echo Setup Complete!
echo ================================
echo.
echo Python is now embedded in the project.
echo Location: %CD%\%PYTHON_DIR%
echo.
echo You can now run: npm run dev
echo.
pause
