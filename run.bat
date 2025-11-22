@echo off
setlocal

set VENV_DIR=venv

if not exist %VENV_DIR% (
    echo [INFO] Creating virtual environment...
    python -m venv %VENV_DIR%
)

echo [INFO] Activating virtual environment...
call %VENV_DIR%\Scripts\activate

echo [INFO] Installing requirements...
pip install -r requirements.txt

echo [INFO] Running Note.com AI Writer...
python src/main.py

pause
