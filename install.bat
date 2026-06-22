@echo off
setlocal EnableExtensions

cd /d "%~dp0"

echo.
echo ==========================================
echo   ChatGPT Archive Builder - Installer
echo ==========================================
echo.
echo This will create a local Python virtual environment
echo and install the required dependencies.
echo.

set PYTHON_CMD=
set PYTHON_MANAGER_URL=https://www.python.org/ftp/python/pymanager/python-manager-26.2.msix
set PYTHON_MANAGER_MSIX=%TEMP%\python-manager-26.2.msix

call :detect_python

if not "%PYTHON_CMD%"=="" goto python_found

echo Python was not found.
echo.
echo The installer can download and install the official Python Install Manager.
echo.
echo Download source:
echo %PYTHON_MANAGER_URL%
echo.
echo This installs Python support for your Windows user account.
echo The app dependencies will still be installed locally inside this project folder.
echo.

choice /c YN /m "Download and install Python Install Manager now?"

if errorlevel 2 (
    echo.
    echo Installation cancelled.
    echo.
    pause
    exit /b 1
)

echo.
echo Downloading Python Install Manager...
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_MANAGER_URL%' -OutFile '%PYTHON_MANAGER_MSIX%'"

if not exist "%PYTHON_MANAGER_MSIX%" (
    echo.
    echo Failed to download Python Install Manager.
    echo.
    pause
    exit /b 1
)

echo.
echo Installing Python Install Manager...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-AppxPackage -Path '%PYTHON_MANAGER_MSIX%'"

echo.
echo Checking Python again...
call :detect_python

if "%PYTHON_CMD%"=="" (
    echo.
    echo Python Install Manager was installed, but Python is not visible in this command window yet.
    echo.
    echo Close this window, then double-click install.bat again.
    echo Windows is being Windows. Naturally.
    echo.
    pause
    exit /b 0
)

:python_found
echo Using Python command:
echo %PYTHON_CMD%
echo.

%PYTHON_CMD% --version

echo.
if exist ".venv\Scripts\python.exe" (
    echo Existing virtual environment found.
) else (
    echo Creating virtual environment...
    echo This may take a minute on slower computers. Please wait.
    %PYTHON_CMD% -m venv .venv
)

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Failed to create the virtual environment.
    echo.
    pause
    exit /b 1
)

echo.
echo Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip

echo.
echo Installing dependencies...
echo This can also take a little while the first time.
".venv\Scripts\python.exe" -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Dependency installation failed.
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   Installation complete!
echo ==========================================
echo.
echo Next step:
echo Double-click start.bat to launch ChatGPT Archive Builder.
echo.
pause
exit /b 0


:detect_python
set PYTHON_CMD=

where py >nul 2>nul
if not errorlevel 1 (
    py -3 --version >nul 2>nul
    if not errorlevel 1 (
        set PYTHON_CMD=py -3
        exit /b 0
    )
)

if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\py.exe" (
    "%LOCALAPPDATA%\Microsoft\WindowsApps\py.exe" -3 --version >nul 2>nul
    if not errorlevel 1 (
        set PYTHON_CMD="%LOCALAPPDATA%\Microsoft\WindowsApps\py.exe" -3
        exit /b 0
    )
)

where python >nul 2>nul
if not errorlevel 1 (
    python --version >nul 2>nul
    if not errorlevel 1 (
        set PYTHON_CMD=python
        exit /b 0
    )
)

exit /b 0