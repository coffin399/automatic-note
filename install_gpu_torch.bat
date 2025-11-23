@echo off
setlocal

set VENV_DIR=venv

if not exist %VENV_DIR% (
    echo [ERROR] Virtual environment not found. Please run run.bat first.
    pause
    exit /b
)

echo [INFO] Activating virtual environment...
call %VENV_DIR%\Scripts\activate

echo [INFO] Uninstalling current PyTorch (CPU version)...
pip uninstall -y torch torchvision torchaudio

echo [INFO] Installing PyTorch with CUDA 12.1 support...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo.
echo [SUCCESS] PyTorch for GPU has been installed!
echo You can now run run.bat again.
pause
