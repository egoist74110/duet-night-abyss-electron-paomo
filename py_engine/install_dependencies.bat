@echo off
echo ================================
echo Installing Python Dependencies
echo ================================
echo.

cd /d "%~dp0"

echo Installing packages from requirements.txt...
pip install -r requirements.txt

echo.
echo ================================
echo Installation Complete!
echo ================================
echo.
echo Note: For GPU support:
echo - NVIDIA GPU: Install CUDA Toolkit and cuDNN
echo - AMD GPU: OpenCL should work automatically
echo.
pause
