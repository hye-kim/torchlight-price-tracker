"""
API client for Torchlight Price Tracker API.
Handles all HTTP communication with the remote API.
"""
import logging
import time
from collections import deque
from threading import Lock
from typing import Any, Dict, Optional

import requests

from .constants import (
    API_CACHE_TTL,
    API_RATE_LIMIT_CALLS,
    API_RATE_LIMIT_WINDOW,
    API_RETRY_BASE_DELAY,
)

logger = logging.getLogger(__name__)


class APIClient:
    """Client for interacting with the Torchlight Price Tracker API."""

    def __init__(self, base_url: str, timeout: int = 10, max_retries: int = 3):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the API (e.g., "https://torchlight-price-tracker.onrender.com")
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self._cache: Dict[str, Any] = {}
        self._cache_lock = Lock()
        self._cache_timestamp: Optional[float] = None
        self._cache_ttl = API_CACHE_TTL

        # Rate limiting
        self._rate_limit_calls = API_RATE_LIMIT_CALLS
        self._rate_limit_window = API_RATE_LIMIT_WINDOW
        self._request_timestamps: deque = deque()
        self._rate_limit_lock = Lock()

    def _check_rate_limit(self) -> None:
        """
        Check and enforce rate limiting.
        Blocks if rate limit would be exceeded, waiting until a request slot is available.
        """
        with self._rate_limit_lock:
            now = time.time()

            # Remove timestamps outside the current window
            while self._request_timestamps and self._request_timestamps[0] < now - self._rate_limit_window:
                self._request_timestamps.popleft()

            # If at limit, wait until oldest request falls outside window
            if len(self._request_timestamps) >= self._rate_limit_calls:
                oldest_request = self._request_timestamps[0]
                wait_time = self._rate_limit_window - (now - oldest_request)
                if wait_time > 0:
                    logger.warning(f"Rate limit reached. Waiting {wait_time:.1f}s before next request")
                    time.sleep(wait_time)
                    # Recursive call after waiting
                    return self._check_rate_limit()

            # Record this request
            self._request_timestamps.append(now)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT)
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object or None if all retries failed

        Raises:
            ValueError: If DELETE method is attempted
        """
        # Prevent DELETE requests
        if method.upper() == 'DELETE':
            raise ValueError("DELETE requests are not allowed by this application")

        # Check rate limit before making request
        self._check_rate_limit()

        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP error on attempt {attempt + 1}/{self.max_retries}: {e}")
                if response.status_code == 404:
                    # Don't retry on 404
                    return None
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to {method} {url} after {self.max_retries} attempts")
                    return None
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error on attempt {attempt + 1}/{self.max_retries}: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to {method} {url} after {self.max_retries} attempts")
                    return None
                # Exponential backoff using constant
                time.sleep(API_RETRY_BASE_DELAY ** attempt)

        return None

    def health_check(self) -> bool:
        """
        Check if the API is accessible.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            response = self._make_request('GET', '/')
            if response and response.status_code == 200:
                logger.info("API health check successful")
                return True
        except Exception as e:
            logger.error(f"API health check failed: {e}")
        return False

    def get_all_items(self, item_type: Optional[str] = None, use_cache: bool = True) -> Optional[Dict[str, Dict]]:
        """
        Get all items from the API.

        Args:
            item_type: Optional filter by item type
            use_cache: Whether to use cached data if available

        Returns:
            Dictionary of items {item_id: item_data} or None if request failed
        """
        # Check cache
        if use_cache and self._is_cache_valid():
            with self._cache_lock:
                if item_type:
                    # Filter by type from cache
                    return {
                        item_id: item_data
                        for item_id, item_data in self._cache.items()
                        if item_data.get('type') == item_type
                    }
                return self._cache.copy()

        params = {}
        if item_type:
            params['item_type'] = item_type

        response = self._make_request('GET', '/items', params=params)
        if response:
            try:
                data = response.json()
                # Update cache only if we fetched all items
                if not item_type:
                    with self._cache_lock:
                        self._cache = data
                        self._cache_timestamp = time.time()
                logger.debug(f"Retrieved {len(data)} items from API")
                return data
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
        return None

    def get_item(self, item_id: str) -> Optional[Dict]:
        """
        Get a specific item by ID.

        Args:
            item_id: The item ID to retrieve

        Returns:
            Item data dictionary or None if not found
        """
        # Check cache first
        if self._is_cache_valid():
            with self._cache_lock:
                if item_id in self._cache:
                    return self._cache[item_id].copy()

        response = self._make_request('GET', f'/items/{item_id}')
        if response:
            try:
                data = response.json()
                # Update item in cache
                with self._cache_lock:
                    if self._cache_timestamp:  # Only update if cache exists
                        self._cache[item_id] = data
                return data
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
        return None

    def create_item(self, item_id: str, item_data: Dict) -> Optional[Dict]:
        """
        Create a new item.

        Args:
            item_id: The item ID to create
            item_data: Item data (name, type, price, etc.)

        Returns:
            Created item data or None if creation failed
        """
        response = self._make_request('POST', f'/items/{item_id}', json=item_data)
        if response:
            try:
                data = response.json()
                # Update cache
                with self._cache_lock:
                    self._cache[item_id] = data
                logger.debug(f"Created item {item_id} via API")
                return data
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
        return None

    def update_item(self, item_id: str, updates: Dict) -> Optional[Dict]:
        """
        Update an existing item.

        Args:
            item_id: The item ID to update
            updates: Dictionary of fields to update

        Returns:
            Updated item data or None if update failed
        """
        response = self._make_request('PUT', f'/items/{item_id}', json=updates)
        if response:
            try:
                data = response.json()
                # Update cache
                with self._cache_lock:
                    self._cache[item_id] = data
                logger.debug(f"Updated item {item_id} via API")
                return data
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
        return None

    def delete_item(self, item_id: str) -> bool:
        """
        Delete an item.

        Args:
            item_id: The item ID to delete

        Returns:
            True if deletion succeeded, False otherwise

        Raises:
            NotImplementedError: DELETE operations are disabled for this application
        """
        raise NotImplementedError("DELETE requests are not allowed. This application does not support deleting items via the API.")

    def get_item_types(self) -> Optional[list]:
        """
        Get all available item types.

        Returns:
            List of item types or None if request failed
        """
        response = self._make_request('GET', '/types')
        if response:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
        return None

    def get_stats(self) -> Optional[Dict]:
        """
        Get API statistics.

        Returns:
            Statistics dictionary or None if request failed
        """
        response = self._make_request('GET', '/stats')
        if response:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"Failed to parse JSON response: {e}")
        return None

    def invalidate_cache(self):
        """Invalidate the cache, forcing a fresh fetch on next request."""
        with self._cache_lock:
            self._cache.clear()
            self._cache_timestamp = None
        logger.debug("Cache invalidated")

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid based on TTL."""
        if not self._cache_timestamp:
            return False
        return (time.time() - self._cache_timestamp) < self._cache_ttl

    def sync_local_to_api(self, local_data: Dict[str, Dict]) -> int:
        """
        Sync local data to the API (bulk upload).

        Args:
            local_data: Dictionary of local items to sync

        Returns:
            Number of items successfully synced
        """
        logger.info(f"Starting sync of {len(local_data)} items to API")
        success_count = 0

        for item_id, item_data in local_data.items():
            # Try to get existing item
            existing = self.get_item(item_id)

            if existing:
                # Update existing item
                if self.update_item(item_id, item_data):
                    success_count += 1
            else:
                # Create new item
                if self.create_item(item_id, item_data):
                    success_count += 1

        logger.info(f"Sync complete: {success_count}/{len(local_data)} items synced")
        return success_count
