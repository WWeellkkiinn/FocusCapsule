@echo off
setlocal

set "DEFAULT_PYTHON_EXE=C:\Users\asd13\anaconda3\envs\FocusCapsule\python.exe"
if not defined PYTHON_EXE (
  set "PYTHON_EXE=%DEFAULT_PYTHON_EXE%"
)
set "EXPECTED_PREFIX=C:\Users\asd13\anaconda3\envs\FocusCapsule"
set "EXPECTED_LIBRARY_BIN=%EXPECTED_PREFIX%\Library\bin"
set "EXPECTED_DLLS=%EXPECTED_PREFIX%\DLLs"
set "EXPECTED_SCRIPTS=%EXPECTED_PREFIX%\Scripts"
set "RUNTIME_HOOK=scripts\pyi_rth_tkfix.py"
set "APP_ICON=assets\FocusCapsule.ico"
set "DIST_DIR=dist"
set "BUILD_DIR=build"

if not exist "%PYTHON_EXE%" (
  echo python not found: %PYTHON_EXE%
  exit /b 2
)
if not exist "%RUNTIME_HOOK%" (
  echo runtime hook not found: %RUNTIME_HOOK%
  exit /b 3
)
if not exist "%APP_ICON%" (
  echo app icon not found: %APP_ICON%
  exit /b 4
)

set "PREFIX_FILE=%TEMP%\focuscapsule_python_prefix.txt"
if exist "%PREFIX_FILE%" del /f /q "%PREFIX_FILE%"
"%PYTHON_EXE%" -c "import pathlib, sys; pathlib.Path(r'%PREFIX_FILE%').write_text(sys.prefix, encoding='utf-8')"
if errorlevel 1 exit /b 6
set /p ACTUAL_PREFIX=<"%PREFIX_FILE%"
del /f /q "%PREFIX_FILE%" >nul 2>&1
if /i not "%ACTUAL_PREFIX%"=="%EXPECTED_PREFIX%" (
  echo unsupported python environment: %ACTUAL_PREFIX%
  echo expected: %EXPECTED_PREFIX%
  exit /b 5
)

set TCL_LIBRARY=
set TK_LIBRARY=
set TCLLIBPATH=
set PYTHONHOME=
set PYTHONPATH=
set "PATH=%EXPECTED_PREFIX%;%EXPECTED_LIBRARY_BIN%;%EXPECTED_DLLS%;%EXPECTED_SCRIPTS%;C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem;C:\Windows\System32\WindowsPowerShell\v1.0\"

cd /d "%~dp0\.."

if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist FocusCapsule.spec del /f /q FocusCapsule.spec

"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

"%PYTHON_EXE%" -m PyInstaller --clean --noconfirm --onedir --distpath "%DIST_DIR%" --workpath "%BUILD_DIR%" --windowed --runtime-hook "%RUNTIME_HOOK%" --icon "%APP_ICON%" --name FocusCapsule main.py
if errorlevel 1 exit /b 1

if exist FocusCapsule.spec del /f /q FocusCapsule.spec

echo build done: %DIST_DIR%\FocusCapsule\FocusCapsule.exe
exit /b 0
