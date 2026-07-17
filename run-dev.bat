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

set "MYSQL_DATABASE=sportsphere_db"
set "MYSQL_USER=root"
set "MYSQL_PASSWORD=persianbhatti"
set "MYSQL_HOST=127.0.0.1"
set "MYSQL_PORT=3306"

echo Checking database connection...
"%PYTHON%" check_db.py

echo Starting Django backend...
echo Using Python: %PYTHON%
"%PYTHON%" manage.py migrate --noinput
"%PYTHON%" manage.py runserver 0.0.0.0:8000 2>nul