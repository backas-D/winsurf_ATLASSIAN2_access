@echo off
setlocal

echo ========================================
echo  ATLASSIAN2 Access - Production Server
echo ========================================
echo.

set ROOT=%~dp0
set VENV=%ROOT%.venv
set TMPDIR=%ROOT%.tmp
set LOGDIR=%ROOT%logs

if not exist "%TMPDIR%" mkdir "%TMPDIR%"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

set TEMP=%TMPDIR%
set TMP=%TMPDIR%

if exist "%VENV%\Scripts\python.exe" (
  set PYTHON=%VENV%\Scripts\python.exe
) else (
  for %%P in (
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
  ) do (
    if exist %%~P (
      set PYTHON=%%~P
      goto :create_venv
    )
  )
  where py >nul 2>nul
  if %errorlevel%==0 (
    set PYTHON=py -3
    goto :create_venv
  )
  echo [ERROR] Python 3.12+ was not found.
  pause
  exit /b 1
)
goto :install

:create_venv
echo [INFO] Creating virtual environment...
%PYTHON% -m venv "%VENV%"
set PYTHON=%VENV%\Scripts\python.exe

:install
echo [INFO] Installing/Updating dependencies...
"%PYTHON%" -m pip install --upgrade pip --quiet
"%PYTHON%" -m pip install -r "%ROOT%requirements.txt" --quiet

echo.
echo [INFO] Checking .env configuration...
if not exist "%ROOT%.env" (
  echo [WARNING] .env file not found!
  echo [WARNING] Please create .env file with required configuration.
  echo [WARNING] See .env.example or ignore.env for reference.
  pause
  exit /b 1
)

echo [INFO] Starting production server...
echo [INFO] Server will be accessible at:
echo        - Local:    http://127.0.0.1:5000
echo        - Network:  http://[YOUR_IP]:5000
echo        - External: http://[PUBLIC_IP]:5000
echo.
echo [INFO] Press Ctrl+C to stop the server
echo [INFO] Logs will be saved to: %LOGDIR%
echo.
echo ========================================
echo.

set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set LOGFILE=%LOGDIR%\production_%TIMESTAMP%.log

start "" http://127.0.0.1:5000
"%PYTHON%" -m waitress --host=0.0.0.0 --port=5000 --threads=4 main:app 2>&1 | "%PYTHON%" -u -c "import sys; [print(line, end='', file=open(r'%LOGFILE%', 'a', encoding='utf-8')) or print(line, end='') for line in sys.stdin]"

echo.
echo [INFO] Server stopped.
pause
