@echo off
setlocal

if not defined PYTHON_EXE (
  set PYTHON_EXE=python
)
set RUNTIME_HOOK=scripts\pyi_rth_tkfix.py

where "%PYTHON_EXE%" >nul 2>&1
if errorlevel 1 (
  echo python not found: %PYTHON_EXE%
  exit /b 2
)
if not exist "%RUNTIME_HOOK%" (
  echo runtime hook not found: %RUNTIME_HOOK%
  exit /b 3
)

set TCL_LIBRARY=
set TK_LIBRARY=
set TCLLIBPATH=
set PYTHONHOME=
set PYTHONPATH=

cd /d "%~dp0\.."

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist FocusCapsule.spec del /f /q FocusCapsule.spec

"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

"%PYTHON_EXE%" -m PyInstaller --clean --noconfirm --onedir --windowed --runtime-hook "%RUNTIME_HOOK%" --name FocusCapsule main.py
if errorlevel 1 exit /b 1

if exist FocusCapsule.spec del /f /q FocusCapsule.spec

echo build done: dist\FocusCapsule\FocusCapsule.exe
exit /b 0
