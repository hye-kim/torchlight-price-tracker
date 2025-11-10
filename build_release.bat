@echo off
REM Build script for creating Windows executable
REM Run this on a Windows machine with Python installed

echo ========================================
echo Torchlight Infinite Tracker - Build Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

echo.
echo Cleaning previous build artifacts...
if exist build (
    echo Removing build directory...
    rmdir /s /q build
)
if exist dist (
    echo Removing dist directory...
    rmdir /s /q dist
)

echo.
echo Building executable...
pyinstaller torchlight_tracker.spec --clean
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo The executable can be found in: dist\TorchlightInfiniteTracker.exe
echo.
echo You can now distribute this .exe file to users.
echo They will need the following files in the same directory:
echo   - TorchlightInfiniteTracker.exe
echo.
pause
