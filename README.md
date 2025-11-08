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

## Contributing

When you discover a drop item that doesn't exist in the database or prices have significantly changed, you can:
1. Submit an issue with the item details
2. Make changes to the data files and submit a pull request

## Requirements

- Python 3.7+
- Windows OS (for game process detection)

## License

This project builds upon the original FurTorch codebase.

## Acknowledgments

- Original FurTorch developers
- AI assistance for translation and code improvements
