@echo off
setlocal

set ROOT=%~dp0
set VENV=%ROOT%.venv
set TMPDIR=%ROOT%.tmp

if not exist "%TMPDIR%" mkdir "%TMPDIR%"
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
  echo Python 3.12+ was not found.
  exit /b 1
)
goto :install

:create_venv
echo Creating virtual environment...
%PYTHON% -m venv "%VENV%"
set PYTHON=%VENV%\Scripts\python.exe

:install
echo Installing dependencies...
"%PYTHON%" -m pip install --upgrade pip
"%PYTHON%" -m pip install -r "%ROOT%requirements.txt"

start "" http://127.0.0.1:5000
"%PYTHON%" "%ROOT%main.py"
