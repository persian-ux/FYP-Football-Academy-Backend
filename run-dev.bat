@echo off
setlocal

cd /d "%~dp0"

if exist ".venv-1\Scripts\python.exe" (
    set "PYTHON=.venv-1\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

"%PYTHON%" -m watchdog.watchmedo auto-restart ^
  --patterns="*.py" ^
  --ignore-patterns="*.pyc;*__pycache__*" ^
  --recursive ^
  -- python manage.py runserver 0.0.0.0:8000 --noreload