@echo off
setlocal

set PYTHON_EXE=C:\Users\asd13\anaconda3\envs\FocusCapsule\python.exe
set RUNTIME_HOOK=scripts\pyi_rth_tkfix.py

if not exist "%PYTHON_EXE%" (
  echo python not found: %PYTHON_EXE%
  exit /b 2
)
if not exist "%RUNTIME_HOOK%" (
  echo runtime hook not found: %RUNTIME_HOOK%
  exit /b 3
)

set "PATH=C:\Users\asd13\anaconda3\envs\FocusCapsule;C:\Users\asd13\anaconda3\envs\FocusCapsule\Library\bin;C:\Users\asd13\anaconda3\envs\FocusCapsule\DLLs;C:\Windows\System32;C:\Windows;C:\Windows\System32\Wbem"
set TCL_LIBRARY=
set TK_LIBRARY=
set TCLLIBPATH=
set PYTHONHOME=
set PYTHONPATH=

cd /d %~dp0\..

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist FocusCapsule.spec del /f /q FocusCapsule.spec

"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

"%PYTHON_EXE%" -m PyInstaller --clean --noconfirm --onedir --windowed --runtime-hook "%RUNTIME_HOOK%" --name FocusCapsule main.py
if errorlevel 1 exit /b 1

echo build done: dist\FocusCapsule\FocusCapsule.exe
exit /b 0
