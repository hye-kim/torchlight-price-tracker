# Torchlight Infinite Price Tracker

English revamp of FurTorch

## Features

- Real-time tracking of item drops in Torchlight: Infinite
- Automatic price updates from in-game market searches
- Income calculation per map and total
- Map timing and efficiency tracking
- Inventory state management with initialization flow
- Tax calculation support
- Item filtering by category

## Installation

### Option 1: Download Executable (Recommended for most users)

1. Go to the [Releases](../../releases) page
2. Download the latest `TorchlightInfiniteTracker.exe` file
3. Run the executable - no installation needed!

### Option 2: Run from Source (For developers)

1. Ensure you have Python installed (version 3.8 or higher recommended)
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the tracker:
   ```bash
   python index.py
   ```

## Usage

1. Start Torchlight: Infinite
2. Run the tracker:
   - **Executable**: Double-click `TorchlightInfiniteTracker.exe`
   - **From source**: Run `python index.py`
3. Click the "Initialize Tracker" button and follow the on-screen instructions to set up inventory tracking
4. Start playing - the tracker will automatically detect drops and calculate earnings!

## How It Works

The tracker monitors your game's log file to detect:
- Item drops and consumption
- Market price checks (when you search items in-game)
- Map entry and exit
- Inventory changes

It maintains an initial state of your inventory and tracks all changes, allowing it to accurately calculate your earnings by comparing drops against materials consumed.

## Building from Source

If you want to build your own executable:

1. See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for detailed instructions
2. Use the provided `build_release.bat` script on Windows
3. Or use GitHub Actions for automated builds

## Contributing

When you discover a drop item that doesn't exist in the database or prices have significantly changed, you can:
1. Submit an issue with the item details
2. Make changes to the data files and submit a pull request

## Requirements

### For Executable Users
- Windows OS (Windows 10 or later recommended)
- Torchlight: Infinite game installed

### For Running from Source
- Python 3.8+
- Windows OS (for game process detection)
- All dependencies from `requirements.txt`

## License

This project builds upon the original FurTorch codebase.

## Acknowledgments

- Original FurTorch developers
- AI assistance for translation and code improvements
