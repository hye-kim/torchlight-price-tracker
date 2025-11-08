# FurTorch - Torchlight Infinite Price Tracker

English revamp of FurTorch with comprehensive code improvements.

## What's New in v0.0.3 (Improved)

This version features a complete code refactoring with significant improvements:

- **Modular Architecture:** Code split into focused, maintainable modules
- **Type Safety:** Full type hints throughout the codebase
- **Better Error Handling:** Comprehensive exception handling with proper logging
- **Thread Safety:** Proper synchronization for concurrent operations
- **Performance Optimizations:** File I/O caching and optimized operations
- **Professional Logging:** Detailed logging to both console and file
- **Comprehensive Documentation:** Full docstrings for all public APIs

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for detailed documentation of all improvements.

## Features

- Real-time tracking of item drops in Torchlight: Infinite
- Automatic price updates from in-game market searches
- Income calculation per map and total
- Map timing and efficiency tracking
- Inventory state management with initialization flow
- Tax calculation support
- Configurable UI opacity
- Item filtering by category

## Installation

1. Ensure you have Python installed (version 3.7 or higher recommended)
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start Torchlight: Infinite
2. Run the tracker:
   ```bash
   python index.py
   ```
3. Click the "Initialize" button and follow the on-screen instructions to set up inventory tracking
4. Start playing - the tracker will automatically detect drops and calculate earnings!

## How It Works

The tracker monitors your game's log file to detect:
- Item drops and consumption
- Market price checks (when you search items in-game)
- Map entry and exit
- Inventory changes

It maintains an initial state of your inventory and tracks all changes, allowing it to accurately calculate your earnings by comparing drops against materials consumed.

## Project Structure

```
├── index.py                    # Main application entry point
├── index_original.py           # Backup of original code
├── src/                        # Source modules
│   ├── constants.py            # Constants and configuration values
│   ├── config_manager.py       # Configuration management
│   ├── file_manager.py         # File I/O operations
│   ├── log_parser.py           # Game log parsing
│   ├── inventory_tracker.py    # Inventory state tracking
│   ├── statistics_tracker.py   # Statistics and income tracking
│   └── game_detector.py        # Game process detection
├── config.json                 # User configuration
├── full_table.json            # Item database with prices
├── en_id_table.json           # English item name mappings
└── tracker.log                # Application log file
```

## Configuration

The tracker stores configuration in `config.json`:

```json
{
    "opacity": 1.0,     // Window opacity (0.1 to 1.0)
    "tax": 0,           // Tax calculation (0=no tax, 1=include tax)
    "user": ""          // User identifier
}
```

## Contributing

When you discover a drop item that doesn't exist in the database or prices have significantly changed, you can:
1. Submit an issue with the item details
2. Make changes to the data files and submit a pull request

## Development

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for:
- Detailed architecture documentation
- Code quality improvements
- Migration guide
- Testing recommendations
- Future enhancement opportunities

## Requirements

- Python 3.7+
- Windows OS (for game process detection)
- pywin32
- psutil
- tkinter (usually included with Python)

## License

This project builds upon the original FurTorch codebase.

## Acknowledgments

- Original FurTorch developers
- AI assistance for translation and code improvements
