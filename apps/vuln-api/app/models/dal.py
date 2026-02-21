"""
Data Access Layer (DAL) for demo purposes.

Provides thread-safe, in-memory data storage with CRUD operations.
Supports optional vulnerability injection for WAF testing scenarios.

In production, this would be replaced with proper database models and ORM.
"""

from datetime import datetime
from gevent.lock import BoundedSemaphore as Lock
from typing import Any, Dict, List, Optional, Callable
import copy
import uuid


class DataStore:
    """
    Thread-safe in-memory data store with CRUD operations.

    This class provides a flexible storage mechanism that can support
    both secure operations and intentionally vulnerable operations for
    WAF testing scenarios.

    Attributes:
        _data: Internal dictionary storage
        _lock: Thread lock for concurrent access
        _validator: Optional validation function
        _bypass_validation: Flag to disable validation for vulnerable endpoints
    """

    def __init__(
        self,
        validator: Optional[Callable[[Dict[str, Any]], bool]] = None,
        bypass_validation: bool = False
    ):
        """
        Initialize a new data store.

        Args:
            validator: Optional function to validate data before storage
            bypass_validation: If True, skip validation (for vulnerable endpoints)
        """
        self._data: Dict[str, Any] = {}
        self._lock = Lock()
        self._validator = validator
        self._bypass_validation = bypass_validation

    def create(
        self,
        key: str,
        value: Any,
        auto_id: bool = False,
        id_prefix: str = "ID"
    ) -> str:
        """
        Create a new record in the data store.

        Args:
            key: Primary key for the record
            value: Data to store
            auto_id: Generate a unique ID if True
            id_prefix: Prefix for auto-generated IDs

        Returns:
            The key used for storage (generated if auto_id=True)

        Raises:
            ValueError: If validation fails or key already exists
        """
        if auto_id:
            key = f"{id_prefix}_{uuid.uuid4().hex[:8]}"

        # Validate data unless bypassed
        if not self._bypass_validation and self._validator:
            if not self._validator(value):
                raise ValueError("Data validation failed")

        with self._lock:
            if key in self._data:
                raise ValueError(f"Key '{key}' already exists")

            # Add metadata
            if isinstance(value, dict):
                value['created_at'] = datetime.now().isoformat()
                value['updated_at'] = datetime.now().isoformat()

            self._data[key] = copy.deepcopy(value)

        return key

    def read(self, key: str, default: Any = None) -> Optional[Any]:
        """
        Read a record from the data store.

        Args:
            key: Key to retrieve
            default: Default value if key not found

        Returns:
            The stored value or default if not found
        """
        with self._lock:
            value = self._data.get(key, default)
            # Return a deep copy to prevent external modifications
            return copy.deepcopy(value) if value is not None else default

    def update(
        self,
        key: str,
        value: Any,
        merge: bool = True
    ) -> bool:
        """
        Update an existing record.

        Args:
            key: Key to update
            value: New data
            merge: If True and value is dict, merge with existing data

        Returns:
            True if updated, False if key not found
        """
        with self._lock:
            if key not in self._data:
                return False

            if merge and isinstance(value, dict) and isinstance(self._data[key], dict):
                self._data[key].update(value)
                self._data[key]['updated_at'] = datetime.now().isoformat()
            else:
                if isinstance(value, dict):
                    value['updated_at'] = datetime.now().isoformat()
                self._data[key] = copy.deepcopy(value)

        return True

    def delete(self, key: str) -> bool:
        """
        Delete a record from the data store.

        Args:
            key: Key to delete

        Returns:
            True if deleted, False if key not found
        """
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the data store.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise
        """
        with self._lock:
            return key in self._data

    def list_all(self) -> Dict[str, Any]:
        """
        List all records in the data store.

        Returns:
            Dictionary of all stored records (deep copy)
        """
        with self._lock:
            return copy.deepcopy(self._data)

    def find(
        self,
        predicate: Callable[[Any], bool],
        limit: Optional[int] = None
    ) -> List[Any]:
        """
        Find records matching a predicate function.

        Args:
            predicate: Function that returns True for matching records
            limit: Maximum number of results to return

        Returns:
            List of matching records
        """
        results = []
        with self._lock:
            for value in self._data.values():
                if predicate(value):
                    results.append(copy.deepcopy(value))
                    if limit and len(results) >= limit:
                        break

        return results

    def count(self) -> int:
        """
        Count the number of records in the data store.

        Returns:
            Number of records
        """
        with self._lock:
            return len(self._data)

    def clear(self) -> None:
        """
        Clear all records from the data store.

        WARNING: This operation cannot be undone.
        """
        with self._lock:
            self._data.clear()

    def bulk_insert(self, records: Dict[str, Any]) -> int:
        """
        Insert multiple records at once.

        Args:
            records: Dictionary of key-value pairs to insert

        Returns:
            Number of records inserted
        """
        count = 0
        with self._lock:
            for key, value in records.items():
                if key not in self._data:
                    if isinstance(value, dict):
                        value['created_at'] = datetime.now().isoformat()
                        value['updated_at'] = datetime.now().isoformat()
                    self._data[key] = copy.deepcopy(value)
                    count += 1

        return count


class TransactionalDataStore(DataStore):
    """
    Extended data store with transaction-like operations.

    Provides support for transactional patterns like append-only logs
    and time-series data.
    """

    def append(self, key: str, item: Any) -> bool:
        """
        Append an item to a list stored at key.

        Args:
            key: Key containing a list
            item: Item to append

        Returns:
            True if appended, False if key doesn't exist or isn't a list
        """
        with self._lock:
            if key not in self._data:
                self._data[key] = []

            if not isinstance(self._data[key], list):
                return False

            # Add timestamp to item if it's a dict
            if isinstance(item, dict):
                item['timestamp'] = datetime.now().isoformat()

            self._data[key].append(copy.deepcopy(item))

        return True

    def get_range(
        self,
        key: str,
        start: int = 0,
        end: Optional[int] = None
    ) -> List[Any]:
        """
        Get a range of items from a list stored at key.

        Args:
            key: Key containing a list
            start: Start index (inclusive)
            end: End index (exclusive), None for end of list

        Returns:
            List of items in the range
        """
        with self._lock:
            if key not in self._data or not isinstance(self._data[key], list):
                return []

            return copy.deepcopy(self._data[key][start:end])

    def increment(self, key: str, field: str, amount: float = 1.0) -> float:
        """
        Atomically increment a numeric field.

        Args:
            key: Key containing a dict
            field: Field name to increment
            amount: Amount to add (default 1.0)

        Returns:
            New value after increment

        Raises:
            ValueError: If key doesn't exist or field isn't numeric
        """
        with self._lock:
            if key not in self._data:
                raise ValueError(f"Key '{key}' not found")

            if not isinstance(self._data[key], dict):
                raise ValueError(f"Key '{key}' does not contain a dictionary")

            current = self._data[key].get(field, 0)
            if not isinstance(current, (int, float)):
                raise ValueError(f"Field '{field}' is not numeric")

            new_value = current + amount
            self._data[key][field] = new_value
            self._data[key]['updated_at'] = datetime.now().isoformat()

            return new_value


# Singleton instances for application-wide use
_stores: Dict[str, DataStore] = {}
_stores_lock = Lock()


def get_store(
    name: str,
    store_class: type = DataStore,
    **kwargs
) -> DataStore:
    """
    Get or create a named data store instance.

    This function provides singleton access to data stores, ensuring
    that the same store instance is returned for the same name.

    Args:
        name: Unique name for the data store
        store_class: Class to instantiate (DataStore or subclass)
        **kwargs: Arguments passed to store constructor

    Returns:
        Data store instance
    """
    with _stores_lock:
        if name not in _stores:
            _stores[name] = store_class(**kwargs)
        return _stores[name]


def reset_all_stores() -> None:
    """
    Clear all data from all stores.

    Useful for resetting demo data between test runs.
    WARNING: This operation cannot be undone.
    """
    with _stores_lock:
        for store in _stores.values():
            store.clear()


def get_all_store_stats() -> Dict[str, Dict[str, int]]:
    """
    Get statistics for all data stores.

    Returns:
        Dictionary mapping store names to their statistics
    """
    stats = {}
    with _stores_lock:
        for name, store in _stores.items():
            stats[name] = {
                'count': store.count(),
                'type': store.__class__.__name__
            }
    return stats
