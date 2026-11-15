@echo off
cd /d "%~dp0backend"
if not exist .venv (
  py -3 -m venv .venv
  if errorlevel 1 exit /b 1
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
