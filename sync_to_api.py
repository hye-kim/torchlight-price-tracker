#!/usr/bin/env python3
"""
Utility script to sync local price data to the Torchlight Price Tracker API.
Use this to migrate your existing local data to the API.
"""

import json
import logging
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.api_client import APIClient
from src.constants import FULL_TABLE_FILE, CONFIG_FILE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load configuration from config.json."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def load_local_data() -> dict:
    """Load local full_table.json data."""
    try:
        with open(FULL_TABLE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Loaded {len(data)} items from {FULL_TABLE_FILE}")
            return data
    except FileNotFoundError:
        logger.error(f"{FULL_TABLE_FILE} not found")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse {FULL_TABLE_FILE}: {e}")
        return {}


def main():
    """Main sync function."""
    print("=" * 60)
    print("Torchlight Price Tracker - API Sync Utility")
    print("=" * 60)
    print()

    # Load configuration
    config = load_config()
    if not config:
        print("ERROR: Could not load config.json")
        return 1

    api_url = config.get('api_url')
    if not api_url:
        print("ERROR: api_url not configured in config.json")
        return 1

    api_timeout = config.get('api_timeout', 10)

    print(f"API URL: {api_url}")
    print(f"Timeout: {api_timeout}s")
    print()

    # Initialize API client
    client = APIClient(api_url, timeout=api_timeout)

    # Check API health
    print("Checking API connectivity...")
    if not client.health_check():
        print("ERROR: Could not connect to API")
        print("Please check:")
        print("  1. API URL is correct")
        print("  2. API server is running")
        print("  3. Network connection is available")
        return 1

    print("✓ API is accessible")
    print()

    # Load local data
    print("Loading local data...")
    local_data = load_local_data()
    if not local_data:
        print("ERROR: No local data to sync")
        return 1

    print(f"✓ Found {len(local_data)} items to sync")
    print()

    # Get current API stats
    print("Checking current API state...")
    stats = client.get_stats()
    if stats:
        print(f"  Current API items: {stats.get('total_items', 0)}")
        print(f"  Item types: {stats.get('total_types', 0)}")
        print()

    # Confirm sync
    response = input(f"Ready to sync {len(local_data)} items to API. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Sync cancelled")
        return 0

    print()
    print("Starting sync...")
    print("-" * 60)

    # Sync data
    synced_count = client.sync_local_to_api(local_data)

    print("-" * 60)
    print()

    if synced_count == len(local_data):
        print(f"✓ SUCCESS: All {synced_count} items synced successfully!")
    elif synced_count > 0:
        print(f"⚠ PARTIAL: {synced_count}/{len(local_data)} items synced")
        print(f"  {len(local_data) - synced_count} items failed")
    else:
        print("✗ FAILED: No items were synced")
        return 1

    # Show final stats
    print()
    print("Final API state:")
    final_stats = client.get_stats()
    if final_stats:
        print(f"  Total items: {final_stats.get('total_items', 0)}")
        print(f"  Item types: {final_stats.get('total_types', 0)}")
        print(f"  Average price: {final_stats.get('average_price', 0):.2f}")

        most_expensive = final_stats.get('most_expensive_item')
        if most_expensive:
            print(f"  Most expensive: {most_expensive.get('name')} ({most_expensive.get('price'):.2f})")

    print()
    print("=" * 60)
    print("Sync complete!")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
