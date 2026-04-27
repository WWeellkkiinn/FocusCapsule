@echo off
setlocal

set "DEFAULT_PYTHON_EXE=C:\Users\asd13\anaconda3\envs\FocusCapsule\python.exe"
if not defined PYTHON_EXE (
  set "PYTHON_EXE=%DEFAULT_PYTHON_EXE%"
)
set "EXPECTED_PREFIX=C:\Users\asd13\anaconda3\envs\FocusCapsule"
set "APP_ICON=assets\FocusCapsule.ico"
set "DIST_DIR=dist_staging"
set "BUILD_DIR=build_staging"

if not exist "%PYTHON_EXE%" (
  echo python not found: %PYTHON_EXE%
  exit /b 2
)
if not exist "%APP_ICON%" (
  echo app icon not found: %APP_ICON%
  exit /b 4
)

:: Verify correct environment
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

cd /d "%~dp0\.."

if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%"  rmdir /s /q "%DIST_DIR%"
if exist FocusCapsule.spec del /f /q FocusCapsule.spec

"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

"%PYTHON_EXE%" -m PyInstaller ^
  --clean --noconfirm --onedir ^
  --distpath "%DIST_DIR%" --workpath "%BUILD_DIR%" ^
  --windowed --icon "%APP_ICON%" ^
  --add-data "focuscapsule\ui\bar.qml;focuscapsule\ui" ^
  --name FocusCapsule ^
  main.py
if errorlevel 1 exit /b 1

if exist FocusCapsule.spec del /f /q FocusCapsule.spec

echo build done: %DIST_DIR%\FocusCapsule\FocusCapsule.exe
exit /b 0
