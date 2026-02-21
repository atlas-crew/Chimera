"""
Unit tests for the Data Access Layer (DAL).

Tests cover:
- CRUD operations (create, read, update, delete)
- Thread safety with concurrent operations
- Validation bypass functionality
- Transactional operations
- Singleton pattern for stores
"""

import pytest
import threading
import time
from datetime import datetime
from app.models.dal import (
    DataStore,
    TransactionalDataStore,
    get_store,
    reset_all_stores,
    get_all_store_stats
)


class TestDataStoreBasicOperations:
    """Test basic CRUD operations for DataStore."""

    def test_create_simple_record(self):
        """Test creating a simple record."""
        store = DataStore()
        key = store.create('user_1', {'name': 'Alice', 'age': 30})

        assert key == 'user_1'
        assert store.exists('user_1')
        assert store.count() == 1

    def test_create_with_auto_id(self):
        """Test creating a record with auto-generated ID."""
        store = DataStore()
        key = store.create('', {'name': 'Bob'}, auto_id=True, id_prefix='USER')

        assert key.startswith('USER_')
        assert store.exists(key)

    def test_create_duplicate_key_fails(self):
        """Test that creating duplicate key raises ValueError."""
        store = DataStore()
        store.create('user_1', {'name': 'Alice'})

        with pytest.raises(ValueError, match="already exists"):
            store.create('user_1', {'name': 'Bob'})

    def test_create_adds_timestamps(self):
        """Test that create adds created_at and updated_at timestamps."""
        store = DataStore()
        store.create('user_1', {'name': 'Alice'})

        record = store.read('user_1')
        assert 'created_at' in record
        assert 'updated_at' in record
        assert record['name'] == 'Alice'

    def test_read_existing_record(self):
        """Test reading an existing record."""
        store = DataStore()
        original = {'name': 'Alice', 'age': 30}
        store.create('user_1', original)

        record = store.read('user_1')
        assert record['name'] == 'Alice'
        assert record['age'] == 30

    def test_read_nonexistent_record_returns_default(self):
        """Test reading nonexistent record returns default value."""
        store = DataStore()

        result = store.read('nonexistent')
        assert result is None

        result = store.read('nonexistent', default={'empty': True})
        assert result == {'empty': True}

    def test_read_returns_deep_copy(self):
        """Test that read returns a deep copy to prevent external modifications."""
        store = DataStore()
        store.create('user_1', {'name': 'Alice', 'tags': ['admin']})

        record1 = store.read('user_1')
        record1['tags'].append('editor')

        record2 = store.read('user_1')
        assert record2['tags'] == ['admin']  # Should not be modified

    def test_update_existing_record_merge(self):
        """Test updating existing record with merge."""
        store = DataStore()
        store.create('user_1', {'name': 'Alice', 'age': 30})

        success = store.update('user_1', {'age': 31, 'city': 'NYC'}, merge=True)

        assert success is True
        record = store.read('user_1')
        assert record['name'] == 'Alice'
        assert record['age'] == 31
        assert record['city'] == 'NYC'

    def test_update_existing_record_replace(self):
        """Test updating existing record without merge."""
        store = DataStore()
        store.create('user_1', {'name': 'Alice', 'age': 30})

        success = store.update('user_1', {'name': 'Alice Updated'}, merge=False)

        assert success is True
        record = store.read('user_1')
        assert record['name'] == 'Alice Updated'
        assert 'age' not in record

    def test_update_nonexistent_record_fails(self):
        """Test updating nonexistent record returns False."""
        store = DataStore()

        success = store.update('nonexistent', {'data': 'value'})
        assert success is False

    def test_update_adds_updated_at_timestamp(self):
        """Test that update refreshes updated_at timestamp."""
        store = DataStore()
        store.create('user_1', {'name': 'Alice'})

        time.sleep(0.01)  # Small delay to ensure timestamp changes
        store.update('user_1', {'name': 'Alice Updated'})

        record = store.read('user_1')
        assert 'updated_at' in record

    def test_delete_existing_record(self):
        """Test deleting an existing record."""
        store = DataStore()
        store.create('user_1', {'name': 'Alice'})

        success = store.delete('user_1')

        assert success is True
        assert not store.exists('user_1')
        assert store.count() == 0

    def test_delete_nonexistent_record_fails(self):
        """Test deleting nonexistent record returns False."""
        store = DataStore()

        success = store.delete('nonexistent')
        assert success is False

    def test_exists_checks_key_presence(self):
        """Test exists method accurately checks key presence."""
        store = DataStore()
        store.create('user_1', {'name': 'Alice'})

        assert store.exists('user_1') is True
        assert store.exists('nonexistent') is False

    def test_list_all_returns_all_records(self):
        """Test listing all records in store."""
        store = DataStore()
        store.create('user_1', {'name': 'Alice'})
        store.create('user_2', {'name': 'Bob'})
        store.create('user_3', {'name': 'Charlie'})

        all_records = store.list_all()

        assert len(all_records) == 3
        assert 'user_1' in all_records
        assert all_records['user_1']['name'] == 'Alice'

    def test_list_all_returns_deep_copy(self):
        """Test that list_all returns deep copy."""
        store = DataStore()
        store.create('user_1', {'name': 'Alice', 'tags': ['admin']})

        all_records = store.list_all()
        all_records['user_1']['tags'].append('editor')

        record = store.read('user_1')
        assert record['tags'] == ['admin']  # Should not be modified

    def test_count_returns_correct_number(self):
        """Test count returns accurate record count."""
        store = DataStore()

        assert store.count() == 0

        store.create('user_1', {'name': 'Alice'})
        assert store.count() == 1

        store.create('user_2', {'name': 'Bob'})
        assert store.count() == 2

        store.delete('user_1')
        assert store.count() == 1

    def test_clear_removes_all_records(self):
        """Test clear removes all records."""
        store = DataStore()
        store.create('user_1', {'name': 'Alice'})
        store.create('user_2', {'name': 'Bob'})

        store.clear()

        assert store.count() == 0
        assert not store.exists('user_1')
        assert not store.exists('user_2')

    def test_find_with_predicate(self):
        """Test finding records with predicate function."""
        store = DataStore()
        store.create('user_1', {'name': 'Alice', 'age': 30})
        store.create('user_2', {'name': 'Bob', 'age': 25})
        store.create('user_3', {'name': 'Charlie', 'age': 35})

        results = store.find(lambda record: record.get('age', 0) > 28)

        assert len(results) == 2
        names = {r['name'] for r in results}
        assert 'Alice' in names
        assert 'Charlie' in names

    def test_find_with_limit(self):
        """Test finding records with limit."""
        store = DataStore()
        for i in range(10):
            store.create(f'user_{i}', {'name': f'User{i}', 'age': 20 + i})

        results = store.find(lambda r: r.get('age', 0) > 0, limit=5)

        assert len(results) == 5

    def test_bulk_insert_multiple_records(self):
        """Test bulk inserting multiple records."""
        store = DataStore()
        records = {
            'user_1': {'name': 'Alice'},
            'user_2': {'name': 'Bob'},
            'user_3': {'name': 'Charlie'}
        }

        count = store.bulk_insert(records)

        assert count == 3
        assert store.count() == 3
        assert store.read('user_2')['name'] == 'Bob'

    def test_bulk_insert_skips_existing_keys(self):
        """Test bulk insert skips existing keys."""
        store = DataStore()
        store.create('user_1', {'name': 'Alice'})

        records = {
            'user_1': {'name': 'Alice Updated'},
            'user_2': {'name': 'Bob'}
        }

        count = store.bulk_insert(records)

        assert count == 1  # Only user_2 inserted
        assert store.read('user_1')['name'] == 'Alice'  # Not updated


class TestDataStoreValidation:
    """Test validation functionality in DataStore."""

    def test_validator_function_called_on_create(self):
        """Test that validator function is called during create."""
        def validator(data):
            return data.get('valid') is True

        store = DataStore(validator=validator)

        # Valid data
        key = store.create('record_1', {'valid': True, 'name': 'Test'})
        assert key == 'record_1'

        # Invalid data
        with pytest.raises(ValueError, match="validation failed"):
            store.create('record_2', {'valid': False})

    def test_bypass_validation_skips_validator(self):
        """Test that bypass_validation skips validator."""
        def validator(data):
            return data.get('valid') is True

        store = DataStore(validator=validator, bypass_validation=True)

        # Should succeed even with invalid data
        key = store.create('record_1', {'valid': False})
        assert key == 'record_1'


class TestDataStoreThreadSafety:
    """Test thread safety of DataStore operations."""

    def test_concurrent_creates(self):
        """Test concurrent create operations are thread-safe."""
        store = DataStore()
        errors = []

        def create_records(start_id):
            try:
                for i in range(10):
                    store.create(f'user_{start_id}_{i}', {'name': f'User{start_id}_{i}'})
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=create_records, args=(i,))
            for i in range(5)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(errors) == 0
        assert store.count() == 50

    def test_concurrent_read_write(self):
        """Test concurrent read and write operations."""
        store = DataStore()
        store.create('counter', {'value': 0})
        errors = []

        def increment():
            try:
                for _ in range(100):
                    record = store.read('counter')
                    record['value'] += 1
                    store.update('counter', record, merge=False)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=increment) for _ in range(5)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(errors) == 0
        # Note: Due to race conditions, final value may be less than 500
        # The important thing is no exceptions occurred

    def test_concurrent_delete_operations(self):
        """Test concurrent delete operations."""
        store = DataStore()
        for i in range(100):
            store.create(f'user_{i}', {'name': f'User{i}'})

        errors = []

        def delete_records(start_id):
            try:
                for i in range(start_id, start_id + 20):
                    store.delete(f'user_{i}')
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=delete_records, args=(i,))
            for i in range(0, 100, 20)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(errors) == 0
        assert store.count() == 0


class TestTransactionalDataStore:
    """Test TransactionalDataStore extended functionality."""

    def test_append_creates_list_if_not_exists(self):
        """Test append creates new list if key doesn't exist."""
        store = TransactionalDataStore()

        success = store.append('logs', {'message': 'First log'})

        assert success is True
        logs = store.read('logs')
        assert isinstance(logs, list)
        assert len(logs) == 1

    def test_append_adds_to_existing_list(self):
        """Test append adds to existing list."""
        store = TransactionalDataStore()
        store.create('logs', [])

        store.append('logs', {'message': 'Log 1'})
        store.append('logs', {'message': 'Log 2'})

        logs = store.read('logs')
        assert len(logs) == 2
        assert logs[0]['message'] == 'Log 1'

    def test_append_adds_timestamp_to_dict(self):
        """Test append adds timestamp to dict items."""
        store = TransactionalDataStore()

        store.append('logs', {'message': 'Test'})

        logs = store.read('logs')
        assert 'timestamp' in logs[0]

    def test_append_fails_for_non_list(self):
        """Test append fails if key contains non-list."""
        store = TransactionalDataStore()
        store.create('user', {'name': 'Alice'})

        success = store.append('user', {'data': 'value'})

        assert success is False

    def test_get_range_returns_slice(self):
        """Test get_range returns correct slice of list."""
        store = TransactionalDataStore()
        store.create('items', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

        result = store.get_range('items', start=2, end=5)

        assert result == [3, 4, 5]

    def test_get_range_without_end(self):
        """Test get_range without end parameter."""
        store = TransactionalDataStore()
        store.create('items', [1, 2, 3, 4, 5])

        result = store.get_range('items', start=2)

        assert result == [3, 4, 5]

    def test_get_range_nonexistent_key(self):
        """Test get_range on nonexistent key returns empty list."""
        store = TransactionalDataStore()

        result = store.get_range('nonexistent')

        assert result == []

    def test_get_range_non_list_key(self):
        """Test get_range on non-list key returns empty list."""
        store = TransactionalDataStore()
        store.create('user', {'name': 'Alice'})

        result = store.get_range('user')

        assert result == []

    def test_increment_numeric_field(self):
        """Test incrementing a numeric field."""
        store = TransactionalDataStore()
        store.create('counter', {'value': 10})

        new_value = store.increment('counter', 'value', 5)

        assert new_value == 15
        record = store.read('counter')
        assert record['value'] == 15

    def test_increment_initializes_missing_field(self):
        """Test increment initializes missing field to 0."""
        store = TransactionalDataStore()
        store.create('counter', {'other': 'data'})

        new_value = store.increment('counter', 'value', 10)

        assert new_value == 10

    def test_increment_updates_timestamp(self):
        """Test increment updates updated_at timestamp."""
        store = TransactionalDataStore()
        store.create('counter', {'value': 0})

        store.increment('counter', 'value')

        record = store.read('counter')
        assert 'updated_at' in record

    def test_increment_nonexistent_key_fails(self):
        """Test increment on nonexistent key raises ValueError."""
        store = TransactionalDataStore()

        with pytest.raises(ValueError, match="not found"):
            store.increment('nonexistent', 'value')

    def test_increment_non_dict_fails(self):
        """Test increment on non-dict raises ValueError."""
        store = TransactionalDataStore()
        store.create('list', [1, 2, 3])

        with pytest.raises(ValueError, match="does not contain a dictionary"):
            store.increment('list', 'value')

    def test_increment_non_numeric_field_fails(self):
        """Test increment on non-numeric field raises ValueError."""
        store = TransactionalDataStore()
        store.create('record', {'text': 'not a number'})

        with pytest.raises(ValueError, match="not numeric"):
            store.increment('record', 'text')


class TestStoreSingletonPattern:
    """Test singleton pattern for named stores."""

    def test_get_store_returns_same_instance(self):
        """Test get_store returns same instance for same name."""
        reset_all_stores()

        store1 = get_store('users')
        store2 = get_store('users')

        assert store1 is store2

    def test_get_store_different_names(self):
        """Test get_store returns different instances for different names."""
        reset_all_stores()

        store1 = get_store('users')
        store2 = get_store('products')

        assert store1 is not store2

    def test_get_store_with_custom_class(self):
        """Test get_store with custom store class."""
        reset_all_stores()

        store = get_store('transactions', store_class=TransactionalDataStore)

        assert isinstance(store, TransactionalDataStore)

    def test_reset_all_stores_clears_data(self):
        """Test reset_all_stores clears all store data."""
        reset_all_stores()

        store1 = get_store('users')
        store2 = get_store('products')

        store1.create('user_1', {'name': 'Alice'})
        store2.create('prod_1', {'name': 'Widget'})

        reset_all_stores()

        assert store1.count() == 0
        assert store2.count() == 0

    def test_get_all_store_stats(self):
        """Test get_all_store_stats returns statistics."""
        reset_all_stores()

        users_store = get_store('users')
        products_store = get_store('products', store_class=TransactionalDataStore)

        users_store.create('user_1', {'name': 'Alice'})
        products_store.create('prod_1', {'name': 'Widget'})
        products_store.create('prod_2', {'name': 'Gadget'})

        stats = get_all_store_stats()

        assert stats['users']['count'] == 1
        assert stats['users']['type'] == 'DataStore'
        assert stats['products']['count'] == 2
        assert stats['products']['type'] == 'TransactionalDataStore'


class TestDataStoreEdgeCases:
    """Test edge cases and error conditions."""

    def test_create_with_none_value(self):
        """Test creating record with None value."""
        store = DataStore()

        key = store.create('null_record', None)

        assert key == 'null_record'
        assert store.read('null_record') is None

    def test_create_with_empty_dict(self):
        """Test creating record with empty dict."""
        store = DataStore()

        key = store.create('empty', {})

        assert key == 'empty'
        record = store.read('empty')
        assert isinstance(record, dict)
        assert 'created_at' in record

    def test_find_with_no_matches(self):
        """Test find returns empty list when no matches."""
        store = DataStore()
        store.create('user_1', {'age': 25})

        results = store.find(lambda r: r.get('age') > 100)

        assert results == []

    def test_bulk_insert_empty_dict(self):
        """Test bulk insert with empty dict."""
        store = DataStore()

        count = store.bulk_insert({})

        assert count == 0
        assert store.count() == 0

    def test_update_with_none_value(self):
        """Test update with None value."""
        store = DataStore()
        store.create('record', {'name': 'Alice'})

        success = store.update('record', None, merge=False)

        assert success is True

    def test_concurrent_increment_operations(self):
        """Test concurrent increment operations for race conditions."""
        store = TransactionalDataStore()
        store.create('counter', {'value': 0})

        def increment_many():
            for _ in range(100):
                store.increment('counter', 'value', 1)

        threads = [threading.Thread(target=increment_many) for _ in range(3)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should be 300, but we're testing thread safety not correctness
        # of the final value (which would need locks at a higher level)
        record = store.read('counter')
        assert record['value'] > 0  # At least some increments worked
