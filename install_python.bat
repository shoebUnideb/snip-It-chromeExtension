@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo Python Installer and Environment Setup
echo ===================================================
echo.

:: Set variables
set PYTHON_VERSION=3.11.5
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-amd64.exe
set DOWNLOAD_PATH=%TEMP%\python-%PYTHON_VERSION%-amd64.exe

:: Check if Python is already installed
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Python is already installed:
    python --version
    
    :: Check if pip is installed
    pip --version >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo Pip is already installed:
        pip --version
        goto :VERIFY_PATH
    ) else (
        echo Pip is not installed or not in PATH. Proceeding with installation...
    )
) else (
    echo Python is not installed or not in PATH. Proceeding with installation...
)

:: Download Python installer
echo.
echo Downloading Python %PYTHON_VERSION%...
echo URL: %PYTHON_URL%
echo.

powershell -Command "(New-Object Net.WebClient).DownloadFile('%PYTHON_URL%', '%DOWNLOAD_PATH%')"

if not exist "%DOWNLOAD_PATH%" (
    echo Failed to download Python installer.
    goto :ERROR
)

echo Download complete.
echo.

:: Install Python
echo Installing Python %PYTHON_VERSION%...
echo.

:: Run the installer with necessary arguments
:: /quiet - silent installation
:: PrependPath=1 - add Python to PATH
:: Include_pip=1 - include pip
"%DOWNLOAD_PATH%" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_test=0 Include_doc=0 Include_launcher=1 Include_tcltk=1

:: Check if the installation was successful
echo Waiting for installation to complete...
timeout /t 10 /nobreak >nul

:: Verify if Python was installed correctly
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Installation might not have completed successfully.
    echo Waiting a bit longer...
    timeout /t 30 /nobreak >nul
    
    python --version >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo Python installation failed. Please try again or install manually.
        goto :ERROR
    )
)

:: Verify Python installation
:VERIFY_PYTHON
echo.
echo Verifying Python installation...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo Python installation verification failed.
    goto :ERROR
)

:: Verify pip installation
echo.
echo Verifying pip installation...
pip --version
if %ERRORLEVEL% NEQ 0 (
    echo Pip installation verification failed.
    goto :ERROR
)

:: Verify PATH
:VERIFY_PATH
echo.
echo Verifying Python in PATH...
where python
if %ERRORLEVEL% NEQ 0 (
    echo Python is not in PATH. Attempting to add it...
    goto :ADD_TO_PATH
) else (
    echo Python is correctly set in PATH.
)

echo.
echo Verifying pip in PATH...
where pip
if %ERRORLEVEL% NEQ 0 (
    echo Pip is not in PATH. Attempting to add it...
    goto :ADD_TO_PATH
) else (
    echo Pip is correctly set in PATH.
)

goto :SUCCESS

:: Add Python to PATH if not already there
:ADD_TO_PATH
echo.
echo Adding Python to PATH manually...

:: Get Python installation directory
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    set PYTHON_DIR=%%~dpi
    goto :FOUND_PYTHON_DIR
)

:: If Python not found in PATH, try the default location
if not defined PYTHON_DIR (
    if exist "%ProgramFiles%\Python311\python.exe" (
        set PYTHON_DIR=%ProgramFiles%\Python311\
    ) else if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
        set PYTHON_DIR=%LocalAppData%\Programs\Python\Python311\
    )
)

:FOUND_PYTHON_DIR
if defined PYTHON_DIR (
    echo Found Python in: !PYTHON_DIR!
    
    :: Remove trailing backslash if present
    if "!PYTHON_DIR:~-1!"=="\" set PYTHON_DIR=!PYTHON_DIR:~0,-1!
    
    :: Add Python to user PATH
    echo Adding !PYTHON_DIR! to PATH...
    setx PATH "%PATH%;!PYTHON_DIR!;!PYTHON_DIR!\Scripts" /M
    
    echo PATH update attempted. You may need to restart your command prompt.
) else (
    echo Could not find Python installation directory.
    echo Please add Python to PATH manually.
    goto :ERROR
)

:: Success message
:SUCCESS
echo.
echo ===================================================
echo SUCCESS: Python and pip are installed and configured
echo ===================================================
echo.
echo Python version:
python --version
echo.
echo Pip version:
pip --version
echo.
echo Please restart your command prompt or computer 
echo to ensure all environment changes take effect.
echo.
goto :END

:: Error message
:ERROR
echo.
echo ===================================================
echo ERROR: Setup did not complete successfully
echo ===================================================
echo.
echo Please try:
echo 1. Running this script as administrator
echo 2. Installing Python manually from https://www.python.org/downloads/
echo 3. Adding Python to PATH manually
echo.

:END
pause