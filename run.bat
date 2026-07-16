@echo off
cd /d "%~dp0"
echo Starting AutoLayoutFixer...
if not exist venv\ (
    echo ERROR: venv not found! Please run setup first.
    pause
    exit /b 1
)
call venv\Scripts\activate
python main.py
pause
