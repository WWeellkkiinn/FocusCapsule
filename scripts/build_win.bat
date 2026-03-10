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
set "POWERSHELL_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
set "RUNTIME_HOOK=scripts\pyi_rth_tkfix.py"
set "CHECK_TCL_SCRIPT=scripts\check_tcl.ps1"
set "SYNC_TCL_SCRIPT=scripts\sync_tcl_runtime.ps1"
set "APP_ICON=assets\FocusCapsule.ico"
set "OVERLAY_IMAGE=assets\overlay\rest_overlay.png"
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
if not exist "%CHECK_TCL_SCRIPT%" (
  echo check script not found: %CHECK_TCL_SCRIPT%
  exit /b 8
)
if not exist "%SYNC_TCL_SCRIPT%" (
  echo sync script not found: %SYNC_TCL_SCRIPT%
  exit /b 9
)
if not exist "%APP_ICON%" (
  echo app icon not found: %APP_ICON%
  exit /b 4
)
if not exist "%OVERLAY_IMAGE%" (
  echo overlay image not found: %OVERLAY_IMAGE%
  exit /b 7
)
if not exist "%POWERSHELL_EXE%" (
  echo powershell not found: %POWERSHELL_EXE%
  exit /b 10
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

"%POWERSHELL_EXE%" -NoProfile -ExecutionPolicy Bypass -Command "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); $OutputEncoding = [System.Text.UTF8Encoding]::new(); & '%CD%\%CHECK_TCL_SCRIPT%' -PythonExe '%PYTHON_EXE%'"
if errorlevel 1 exit /b 1

if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist FocusCapsule.spec del /f /q FocusCapsule.spec

"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

"%PYTHON_EXE%" -m PyInstaller --clean --noconfirm --onedir --distpath "%DIST_DIR%" --workpath "%BUILD_DIR%" --windowed --runtime-hook "%RUNTIME_HOOK%" --icon "%APP_ICON%" --add-data "%OVERLAY_IMAGE%;assets\overlay" --name FocusCapsule main.py
if errorlevel 1 exit /b 1

"%POWERSHELL_EXE%" -NoProfile -ExecutionPolicy Bypass -Command "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); $OutputEncoding = [System.Text.UTF8Encoding]::new(); & '%CD%\%SYNC_TCL_SCRIPT%' -PythonExe '%PYTHON_EXE%' -BundleInternalDir '%CD%\%DIST_DIR%\FocusCapsule\_internal'"
if errorlevel 1 exit /b 1

if exist FocusCapsule.spec del /f /q FocusCapsule.spec

echo build done: %DIST_DIR%\FocusCapsule\FocusCapsule.exe
exit /b 0
