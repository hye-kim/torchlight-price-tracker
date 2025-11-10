# Building Executable

This guide explains how to create an executable file for the Torchlight Infinite Price Tracker.

## Windows Requirements

- Windows operating system (Windows 10 or later recommended)
- Python 3.8 or higher installed ([Download Python](https://www.python.org/downloads/))
- All dependencies listed in `requirements.txt`

## Linux/Mac Requirements

- Linux or macOS operating system
- Python 3.8 or higher installed
- All dependencies listed in `requirements.txt`

## Method 1: Using the Build Script (Recommended)

### Windows

1. **Clone or download this repository** to your Windows machine

2. **Open Command Prompt** in the project directory
   - Navigate to the project folder
   - Or open the folder in File Explorer, then type `cmd` in the address bar

3. **Run the build script**:
   ```batch
   build_release.bat
   ```

4. **Wait for the build to complete**
   - The script will automatically clean previous build artifacts
   - Install all dependencies
   - Build the executable using PyInstaller
   - This may take 2-5 minutes

5. **Find your executable**:
   - Location: `dist\TorchlightInfiniteTracker.exe`
   - This is a standalone executable that can be distributed

### Linux/Mac

1. **Clone or download this repository** to your machine

2. **Open Terminal** in the project directory
   - Navigate to the project folder

3. **Run the build script**:
   ```bash
   bash build_release.sh
   ```

4. **Wait for the build to complete**
   - The script will automatically clean previous build artifacts
   - Install all dependencies
   - Build the executable using PyInstaller
   - This may take 2-5 minutes

5. **Find your executable**:
   - Location: `dist/TorchlightInfiniteTracker`
   - This is a standalone executable that can be distributed

## Method 2: Manual Build

If you prefer to build manually:

### Step 1: Install Dependencies

Windows:
```batch
pip install -r requirements.txt
pip install pyinstaller
```

Linux/Mac:
```bash
pip3 install -r requirements.txt
pip3 install pyinstaller
```

### Step 2: Clean Previous Build Artifacts (IMPORTANT)

**Always clean build artifacts before rebuilding** to ensure the latest `config.json` is bundled:

Windows:
```batch
rmdir /s /q build
rmdir /s /q dist
```

Linux/Mac:
```bash
rm -rf build dist
```

### Step 3: Build the Executable

Windows:
```batch
pyinstaller torchlight_tracker.spec --clean
```

Linux/Mac:
```bash
pyinstaller torchlight_tracker.spec --clean
```

### Step 4: Locate the Executable

Windows: `dist\TorchlightInfiniteTracker.exe`
Linux/Mac: `dist/TorchlightInfiniteTracker`

## Method 3: Using GitHub Actions (Automated)

You can use GitHub Actions to automatically build the executable on every commit or release:

1. The `.github/workflows/build-windows-exe.yml` workflow is already configured
2. Push your code to GitHub
3. Go to the "Actions" tab in your repository
4. The workflow will automatically build the .exe
5. Download the artifact from the completed workflow

## Distribution

Once built, you can distribute the executable:

1. **Single-file distribution**: Just share `TorchlightInfiniteTracker.exe`
   - All dependencies are bundled into this single file
   - Users just double-click to run

2. **With data files**: For first-time users, you may want to include:
   - `TorchlightInfiniteTracker.exe`
   - `config.json` (optional - will be auto-created if missing)
   - `README.md` (optional - for user reference)

## Troubleshooting

### "Python is not recognized as a command"

- Make sure Python is installed and added to PATH during installation
- Reinstall Python and check "Add Python to PATH" option

### Build fails with module errors

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Try updating pip: `python -m pip install --upgrade pip`
- Install PyInstaller again: `pip install --upgrade pyinstaller`

### Antivirus flags the executable

- This is common with PyInstaller executables
- Add an exception in your antivirus software
- Users may need to do the same when running the app

### Executable is very large

- This is normal - PyInstaller bundles Python and all dependencies
- Typical size: 50-100 MB
- Consider using UPX compression (enabled in spec file) to reduce size

## Creating a Release

To create an official release:

1. Build the executable following the steps above
2. Test the executable on a clean Windows system
3. Create a release on GitHub:
   - Go to "Releases" → "Draft a new release"
   - Upload the `TorchlightInfiniteTracker.exe` file
   - Add release notes describing features and changes
   - Publish the release

## Notes

- The executable is platform-specific (build on the OS you want to distribute for)
- Windows builds create `.exe` files, Linux/Mac builds create standalone executables
- The first run may be slower as it extracts bundled files
- Subsequent runs will be faster
- **Important**: When updating `config.json`, always rebuild the executable with clean build artifacts to ensure the latest config is bundled

## Support

If you encounter issues during the build process, please:
1. Check the error messages carefully
2. Ensure you're using a compatible Python version (3.8+)
3. Try building in a fresh Python virtual environment
4. Open an issue on GitHub with the error details
