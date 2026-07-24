@echo off
setlocal
set "BASEDIR=%~dp0"
pushd "%BASEDIR%" >nul 2>&1

set "PYEXE=%BASEDIR%venv\Scripts\python.exe"
set "PYARGS="
if exist "%PYEXE%" goto :have_python

py -3.13 -c "import sys" >nul 2>&1
if not errorlevel 1 (
  set "PYEXE=py"
  set "PYARGS=-3.13"
  goto :have_python
)
py -3.12 -c "import sys" >nul 2>&1
if not errorlevel 1 (
  set "PYEXE=py"
  set "PYARGS=-3.12"
  goto :have_python
)
python -c "import sys" >nul 2>&1
if not errorlevel 1 (
  set "PYEXE=python"
  goto :have_python
)

echo [Launcher] Python 3.12 or newer was not found.
echo Install Python, then follow the setup steps in README.md.
set "ERR=1"
goto :finish

:have_python
echo [Launcher] Using: %PYEXE% %PYARGS%
echo.
"%PYEXE%" %PYARGS% "%BASEDIR%airplane_shooter_advanced.py"
set "ERR=%ERRORLEVEL%"
echo.
if not "%ERR%"=="0" (echo [Launcher] Exited with code %ERR%) else (echo [Launcher] Game exited normally.)

:finish
echo Press any key to close...
pause >nul
popd >nul 2>&1
exit /b %ERR%
