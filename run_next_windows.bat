@echo off
cd /d "%~dp0frontend"
if not exist .env.local copy .env.example .env.local
if not exist node_modules (
  call npm install
  if errorlevel 1 exit /b 1
)
call npm run dev
