@echo off
cd /d "%~dp0"
echo Starting AutoLayoutFixer...
call venv\Scripts\activate
python main.py
pause
