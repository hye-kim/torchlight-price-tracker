#!/bin/bash
# Build script for creating executable on Linux/Mac
# Run this with: bash build_release.sh

echo "========================================"
echo "Torchlight Infinite Tracker - Build Script"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python from https://www.python.org/"
    exit 1
fi

echo "Installing dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo "Installing PyInstaller..."
pip3 install pyinstaller
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install PyInstaller"
    exit 1
fi

echo ""
echo "Cleaning previous build artifacts..."
if [ -d "build" ]; then
    echo "Removing build directory..."
    rm -rf build
fi
if [ -d "dist" ]; then
    echo "Removing dist directory..."
    rm -rf dist
fi

echo ""
echo "Building executable..."
pyinstaller torchlight_tracker.spec --clean
if [ $? -ne 0 ]; then
    echo "ERROR: Build failed"
    exit 1
fi

echo ""
echo "========================================"
echo "Build completed successfully!"
echo "========================================"
echo ""
echo "The executable can be found in: dist/TorchlightInfiniteTracker"
echo ""
echo "You can now distribute this executable to users."
echo ""
