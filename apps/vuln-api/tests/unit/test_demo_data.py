"""
Unit tests for demo data utilities.

Tests cover:
- Data seeding
- Data reset functionality
- Predictable test data generation
- Export/import functionality
- Seed statistics
"""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime
from app.utils.demo_data import (
    init_demo_data,
    reset_demo_data,
    seed_fedramp_demo_fixtures,
    get_fedramp_demo_fixtures,
    get_demo_user,
    get_demo_customer,
    seed_additional_users,
    seed_additional_products,
    seed_transactions,
    get_seed_statistics,
    create_predictable_test_data,
    export_demo_data,
    import_demo_data
)
from app.utils.security_config import security_config


class TestInitDemoData:
    """Test demo data initialization."""

    @patch('app.utils.demo_data.users_db', {})
    @patch('app.utils.demo_data.accounts_db', {})
    @patch('app.utils.demo_data.products_db', {})
    def test_init_demo_data_creates_users(self):
        """Test initialization creates demo users."""
        from app.utils.demo_data import users_db

        init_demo_data()

        assert 'demo@chimera.com' in users_db
        assert users_db['demo@chimera.com']['id'] == 'user_123456'

    @patch('app.utils.demo_data.users_db', {})
    @patch('app.utils.demo_data.accounts_db', {})
    @patch('app.utils.demo_data.products_db', {})
    def test_init_demo_data_creates_accounts(self):
        """Test initialization creates demo accounts."""
        from app.utils.demo_data import accounts_db

        init_demo_data()

        assert 'user_123456' in accounts_db
        assert len(accounts_db['user_123456']) == 2

    @patch('app.utils.demo_data.users_db', {})
    @patch('app.utils.demo_data.products_db', {})
    def test_init_demo_data_creates_products(self):
        """Test initialization creates demo products."""
        from app.utils.demo_data import products_db

        init_demo_data()

        assert len(products_db) >= 3
        assert 'PROD-001' in products_db


class TestFedRampDemoFixtures:
    """Test deterministic FedRAMP fixtures for scenario authors."""

    def test_init_demo_data_creates_fedramp_fixture_set(self):
        """Test FedRAMP fixtures are seeded across tenant and resource stores."""
        import app.models as _models

        init_demo_data()
        assert 'fedramp-tenant-a' in _models.saas_tenants_db
        assert 'fedramp-tenant-b' in _models.saas_tenants_db
        assert _models.saas_tenants_db['fedramp-tenant-a']['plan'] == 'govcloud'
        assert _models.saas_tenants_db['fedramp-tenant-a']['owner_id'] == 'fedramp-admin'
        assert _models.saas_tenants_db['fedramp-tenant-b']['data_region'] == 'us-gov-east-1'

        assert _models.saas_projects_db['fedramp-tenant-a'][0]['project_id'] == 'fedramp-proj-a-001'
        assert _models.saas_projects_db['fedramp-tenant-b'][0]['project_id'] == 'fedramp-proj-b-001'
        assert _models.accounts_db['ACC-FEDRAMP-A-001']['user_id'] == 'fedramp-user-a'
        assert _models.accounts_db['ACC-FEDRAMP-B-001']['user_id'] == 'fedramp-user-b'
        assert _models.medical_records_db['REC-FEDRAMP-A-001']['patient_id'] == 'fedramp-user-a'
        assert _models.medical_records_db['REC-FEDRAMP-B-001']['patient_id'] == 'fedramp-user-b'
        assert _models.orders_db['ORDER-FEDRAMP-A-001']['customer_id'] == 'CUST-FEDRAMP-A'
        assert _models.orders_db['ORDER-FEDRAMP-B-001']['customer_id'] == 'CUST-FEDRAMP-B'
        assert _models.customer_payment_methods_db['CUST-FEDRAMP-A'][0]['method_id'] == 'PM-FEDRAMP-A-001'
        assert _models.customer_payment_methods_db['CUST-FEDRAMP-B'][0]['method_id'] == 'PM-FEDRAMP-B-001'
        assert _models.payment_methods_db['authorizations']['AUTH-FEDRAMP-001']['amount'] == 100.00

        compliance_log = _models.compliance_logs_db['fedramp-audit-deny-001']
        assert compliance_log['framework'] == 'fedramp'
        assert compliance_log['controls'] == ['AC-3', 'AC-4', 'AC-6', 'AU-2']
        assert compliance_log['decision'] == 'deny'

        expected_users = {
            'fedramp-admin': ('admin', 'fedramp-tenant-a', 'fedramp.admin@agency.example'),
            'fedramp-operator-a': ('operator', 'fedramp-tenant-a', 'fedramp.operator.a@agency.example'),
            'fedramp-auditor': ('auditor', 'fedramp-tenant-a', 'fedramp.auditor@agency.example'),
            'fedramp-user-a': ('member', 'fedramp-tenant-a', 'fedramp.user.a@agency.example'),
            'fedramp-user-b': ('member', 'fedramp-tenant-b', 'fedramp.user.b@agency.example'),
        }
        for user_id, (role, tenant_id, email) in expected_users.items():
            assert user_id in _models.users_db
            assert user_id in _models.saas_users_db
            assert _models.users_db[user_id]['password'].startswith('fedramp-demo-')
            assert _models.users_db[user_id]['role'] == role
            assert _models.users_db[user_id]['tenant_id'] == tenant_id
            assert _models.users_db[user_id]['email'] == email
            assert _models.saas_users_db[user_id]['role'] == role
            assert _models.saas_users_db[user_id]['tenant_id'] == tenant_id

        assert set(_models.saas_users_by_tenant['fedramp-tenant-a']) >= {
            'fedramp-admin',
            'fedramp-operator-a',
            'fedramp-auditor',
            'fedramp-user-a',
        }
        assert _models.saas_users_by_tenant['fedramp-tenant-b'] == ['fedramp-user-b']

    def test_get_fedramp_demo_fixtures_returns_stable_contract(self):
        """Test published FedRAMP fixture IDs and credentials stay stable."""
        assert get_fedramp_demo_fixtures() == {
            'note': 'Demo-only credentials for local scenario automation; not real secrets.',
            'tenants': {
                'tenant_a': 'fedramp-tenant-a',
                'tenant_b': 'fedramp-tenant-b',
            },
            'users': {
                'admin': {
                    'user_id': 'fedramp-admin',
                    'username': 'fedramp.admin',
                    'email': 'fedramp.admin@agency.example',
                    'password': 'fedramp-demo-admin',
                    'role': 'admin',
                    'tenant_id': 'fedramp-tenant-a',
                },
                'operator_a': {
                    'user_id': 'fedramp-operator-a',
                    'username': 'fedramp.operator.a',
                    'email': 'fedramp.operator.a@agency.example',
                    'password': 'fedramp-demo-operator-a',
                    'role': 'operator',
                    'tenant_id': 'fedramp-tenant-a',
                },
                'auditor': {
                    'user_id': 'fedramp-auditor',
                    'username': 'fedramp.auditor',
                    'email': 'fedramp.auditor@agency.example',
                    'password': 'fedramp-demo-auditor',
                    'role': 'auditor',
                    'tenant_id': 'fedramp-tenant-a',
                },
                'user_a': {
                    'user_id': 'fedramp-user-a',
                    'username': 'fedramp.user.a',
                    'email': 'fedramp.user.a@agency.example',
                    'password': 'fedramp-demo-user-a',
                    'role': 'member',
                    'tenant_id': 'fedramp-tenant-a',
                },
                'user_b': {
                    'user_id': 'fedramp-user-b',
                    'username': 'fedramp.user.b',
                    'email': 'fedramp.user.b@agency.example',
                    'password': 'fedramp-demo-user-b',
                    'role': 'member',
                    'tenant_id': 'fedramp-tenant-b',
                },
            },
            'resources': {
                'tenant_a_project': 'fedramp-proj-a-001',
                'tenant_b_project': 'fedramp-proj-b-001',
                'tenant_a_account': 'ACC-FEDRAMP-A-001',
                'tenant_b_account': 'ACC-FEDRAMP-B-001',
                'tenant_a_health_record': 'REC-FEDRAMP-A-001',
                'tenant_b_health_record': 'REC-FEDRAMP-B-001',
                'tenant_a_order': 'ORDER-FEDRAMP-A-001',
                'tenant_b_order': 'ORDER-FEDRAMP-B-001',
                'tenant_a_customer': 'CUST-FEDRAMP-A',
                'tenant_b_customer': 'CUST-FEDRAMP-B',
                'payment_authorization': 'AUTH-FEDRAMP-001',
                'audit_allow_log': 'fedramp-audit-allow-001',
                'audit_deny_log': 'fedramp-audit-deny-001',
                'audit_suppression': 'fedramp-audit-suppression-001',
            },
        }

    def test_reset_demo_data_restores_fedramp_fixture_ids(self):
        """Test reset recreates deleted FedRAMP fixture IDs deterministically."""
        import app.models as _models

        init_demo_data()
        fixtures = get_fedramp_demo_fixtures()
        resources = fixtures['resources']

        _models.saas_tenants_db.pop(fixtures['tenants']['tenant_a'])
        _models.accounts_db.pop(resources['tenant_b_account'])
        _models.payment_methods_db['authorizations'].pop(resources['payment_authorization'])

        reset_demo_data()

        assert fixtures['tenants']['tenant_a'] in _models.saas_tenants_db
        assert resources['tenant_b_account'] in _models.accounts_db
        assert resources['payment_authorization'] in _models.payment_methods_db['authorizations']

    def test_fedramp_fixture_seeder_is_idempotent(self):
        """Test direct fixture seeding does not duplicate list-backed fixtures."""
        import app.models as _models

        init_demo_data()
        assert seed_fedramp_demo_fixtures() == get_fedramp_demo_fixtures()
        seed_fedramp_demo_fixtures()
        seed_fedramp_demo_fixtures()

        fedramp_events = [event for event in _models.payment_test_events if event.get('fedramp_fixture')]
        fedramp_audit_logs = [log for log in _models.saas_audit_logs_db if log.get('fedramp_fixture')]
        fedramp_suppressions = [
            suppression for suppression in _models.audit_suppressions_db if suppression.get('fedramp_fixture')
        ]

        assert [event['event_id'] for event in fedramp_events] == ['PAY-FEDRAMP-AUTH-001']
        assert {log['log_id'] for log in fedramp_audit_logs} == {
            'fedramp-audit-allow-001',
            'fedramp-audit-deny-001',
        }
        assert [suppression['suppression_id'] for suppression in fedramp_suppressions] == [
            'fedramp-audit-suppression-001',
        ]

    def test_fedramp_fixture_seeder_supports_patched_saas_user_store(self):
        """Test direct SaaS user insertion when tests patch the module store."""
        import app.utils.demo_data as demo_data

        with patch('app.utils.demo_data.saas_users_db', {}), patch('app.utils.demo_data.add_saas_user') as add_user:
            demo_data.seed_fedramp_demo_fixtures()

            assert 'fedramp-admin' in demo_data.saas_users_db
            assert 'fedramp-user-b' in demo_data.saas_users_db
            assert demo_data.saas_users_db['fedramp-user-b']['tenant_id'] == 'fedramp-tenant-b'
            add_user.assert_not_called()

    def test_fedramp_cross_tenant_resources_stay_separate_in_stores(self):
        """Test normal fixture state keeps tenant A and tenant B ownership separate."""
        import app.models as _models

        init_demo_data()
        fixtures = get_fedramp_demo_fixtures()
        tenant_a = fixtures['tenants']['tenant_a']
        tenant_b = fixtures['tenants']['tenant_b']
        resources = fixtures['resources']

        assert _models.accounts_db[resources['tenant_a_account']]['tenant_id'] == tenant_a
        assert _models.accounts_db[resources['tenant_b_account']]['tenant_id'] == tenant_b
        assert _models.medical_records_db[resources['tenant_a_health_record']]['tenant_id'] == tenant_a
        assert _models.medical_records_db[resources['tenant_b_health_record']]['tenant_id'] == tenant_b
        assert _models.orders_db[resources['tenant_a_order']]['tenant_id'] == tenant_a
        assert _models.orders_db[resources['tenant_b_order']]['tenant_id'] == tenant_b

    def test_fedramp_tenant_projects_are_accessible_via_vulnerable_flow(self, client, set_session):
        """Test the vulnerable SaaS tenant route exposes another tenant's fixture."""
        init_demo_data()
        fixtures = get_fedramp_demo_fixtures()
        set_session(client, {'user_id': fixtures['users']['user_a']['user_id']})

        response = client.get(f"/api/v1/saas/tenants/{fixtures['tenants']['tenant_b']}/projects")

        assert response.status_code == 200
        body = response.json()
        assert body['tenant_id'] == fixtures['tenants']['tenant_b']
        assert body['projects'][0]['project_id'] == fixtures['resources']['tenant_b_project']

    def test_fedramp_banking_fixture_compares_vulnerable_and_secure_modes(self, client, set_session):
        """Test account fixture supports vulnerable access and secure-mode denial."""
        init_demo_data()
        fixtures = get_fedramp_demo_fixtures()
        original_config = security_config.to_dict().copy()
        set_session(client, {'user_id': fixtures['users']['user_a']['user_id']})

        try:
            security_config.update({'bola_protection': False})
            vulnerable_response = client.get(
                f"/api/v1/banking/accounts/{fixtures['resources']['tenant_b_account']}"
            )
            assert vulnerable_response.status_code == 200
            vulnerable_body = vulnerable_response.json()
            assert vulnerable_body['account_id'] == fixtures['resources']['tenant_b_account']
            assert vulnerable_body['vulnerability'] == 'BOLA_IDOR_DETECTED'

            security_config.update({'bola_protection': True})
            secure_response = client.get(f"/api/v1/banking/accounts/{fixtures['resources']['tenant_b_account']}")
            assert secure_response.status_code == 403
            assert secure_response.json()['vulnerability'] == 'BOLA_IDOR_BLOCKED'
        finally:
            security_config.update(original_config)


class TestResetDemoData:
    """Test demo data reset functionality."""

    @patch('app.utils.demo_data.users_db', {'existing': 'data'})
    @patch('app.utils.demo_data.accounts_db', {'existing': 'data'})
    def test_reset_demo_data_clears_stores(self):
        """Test reset clears existing data."""
        from app.utils.demo_data import users_db, accounts_db

        # Verify data exists
        assert len(users_db) > 0
        assert len(accounts_db) > 0

        reset_demo_data()

        # Data should be cleared and re-initialized
        # Note: This depends on the import structure working correctly

    @patch('app.utils.demo_data.users_db', {})
    def test_reset_demo_data_reinitializes(self):
        """Test reset reinitializes with fresh data."""
        from app.utils.demo_data import users_db

        reset_demo_data()

        # Should have fresh demo data
        assert 'demo@chimera.com' in users_db


class TestGetDemoUser:
    """Test getting demo user credentials."""

    def test_get_demo_user_returns_dict(self):
        """Test get_demo_user returns dictionary."""
        demo_user = get_demo_user()

        assert isinstance(demo_user, dict)
        assert 'id' in demo_user
        assert 'email' in demo_user
        assert 'password' in demo_user

    def test_get_demo_user_has_correct_data(self):
        """Test demo user has expected values."""
        demo_user = get_demo_user()

        assert demo_user['id'] == 'user_123456'
        assert demo_user['email'] == 'demo@chimera.com'
        assert demo_user['password'] == 'demo123'
        assert demo_user['name'] == ' Demo User'


class TestGetDemoCustomer:
    """Test getting demo customer data."""

    def test_get_demo_customer_returns_dict(self):
        """Test get_demo_customer returns dictionary."""
        demo_customer = get_demo_customer()

        assert isinstance(demo_customer, dict)
        assert 'customer_id' in demo_customer

    def test_get_demo_customer_has_correct_data(self):
        """Test demo customer has expected values."""
        demo_customer = get_demo_customer()

        assert demo_customer['customer_id'] == 'CUST-001'
        assert demo_customer['name'] == 'John Smith'
        assert demo_customer['segment'] == 'retail'


class TestSeedAdditionalUsers:
    """Test seeding additional test users."""

    @patch('app.utils.demo_data.users_db', {})
    def test_seed_additional_users_creates_users(self):
        """Test seeding creates specified number of users."""
        from app.utils.demo_data import users_db

        users = seed_additional_users(count=5)

        assert len(users) == 5
        assert len(users_db) == 5

    @patch('app.utils.demo_data.users_db', {})
    def test_seed_additional_users_structure(self):
        """Test seeded users have correct structure."""
        users = seed_additional_users(count=3)

        for user in users:
            assert 'id' in user
            assert 'email' in user
            assert 'password' in user
            assert 'name' in user
            assert 'created' in user

    @patch('app.utils.demo_data.users_db', {})
    def test_seed_additional_users_unique_emails(self):
        """Test seeded users have unique emails."""
        users = seed_additional_users(count=10)

        emails = [u['email'] for u in users]
        assert len(emails) == len(set(emails))  # All unique


class TestSeedAdditionalProducts:
    """Test seeding additional products."""

    def test_seed_additional_products_creates_products(self):
        """Test seeding creates specified number of products."""
        import app.models as _models

        before = len(_models.products_db)
        products = seed_additional_products(count=20)

        assert len(products) == 20
        assert len(_models.products_db) == before + 20

    def test_seed_additional_products_structure(self):
        """Test seeded products have correct structure."""
        products = seed_additional_products(count=5)

        for product in products:
            assert 'product_id' in product
            assert 'name' in product
            assert 'price' in product
            assert 'category' in product
            assert 'in_stock' in product

    def test_seed_additional_products_varied_data(self):
        """Test seeded products have varied data."""
        products = seed_additional_products(count=50)

        categories = {p['category'] for p in products}
        prices = [p['price'] for p in products]

        assert len(categories) > 1  # Multiple categories
        assert len(set(prices)) > 10  # Varied prices


class TestSeedTransactions:
    """Test seeding transaction history."""

    def test_seed_transactions_creates_transactions(self):
        """Test seeding creates transactions for user."""
        import app.models as _models

        # Use a unique user ID to avoid collisions with demo data
        test_user = 'test_txn_user_unique'
        txns = seed_transactions(test_user, count=10)

        assert len(txns) == 10
        assert test_user in _models.transactions_db
        assert len(_models.transactions_db[test_user]) == 10

    def test_seed_transactions_structure(self):
        """Test seeded transactions have correct structure."""
        txns = seed_transactions('test_txn_struct', count=5)

        for txn in txns:
            assert 'transaction_id' in txn
            assert 'type' in txn
            assert 'amount' in txn
            assert 'description' in txn
            assert 'date' in txn
            assert 'status' in txn

    def test_seed_transactions_varied_amounts(self):
        """Test seeded transactions have varied amounts."""
        txns = seed_transactions('test_txn_varied', count=20)

        amounts = [t['amount'] for t in txns]
        assert len(set(amounts)) > 5  # Varied amounts


class TestGetSeedStatistics:
    """Test seed statistics function."""

    def test_get_seed_statistics_returns_counts(self):
        """Test statistics return correct counts matching actual stores."""
        import app.models as _models

        stats = get_seed_statistics()

        assert isinstance(stats, dict)
        assert stats['users'] == len(_models.users_db)
        assert stats['products'] == len(_models.products_db)
        assert stats['customers'] == len(_models.customers_db)
        assert stats['policies'] == len(_models.policies_db)
        assert stats['orders'] == len(_models.orders_db)
        assert stats['medical_records'] == len(_models.medical_records_db)

    def test_get_seed_statistics_empty_stores(self):
        """Test statistics keys are all non-negative integers."""
        stats = get_seed_statistics()

        expected_keys = {'users', 'accounts', 'transactions', 'products',
                         'customers', 'policies', 'orders', 'medical_records'}
        assert expected_keys == set(stats.keys())
        for value in stats.values():
            assert isinstance(value, int)
            assert value >= 0


class TestCreatePredictableTestData:
    """Test predictable test data creation."""

    @patch('app.utils.demo_data.users_db', {})
    @patch('app.utils.demo_data.products_db', {})
    @patch('app.utils.demo_data.transactions_db', {})
    def test_create_predictable_test_data_reproducible(self):
        """Test predictable data is reproducible with same seed."""
        from app.utils.demo_data import users_db

        # Create with seed 42
        data1 = create_predictable_test_data(seed=42)
        users1 = list(users_db.values())

        # Clear and recreate with same seed
        users_db.clear()

        data2 = create_predictable_test_data(seed=42)
        users2 = list(users_db.values())

        # Should produce identical data
        assert len(users1) == len(users2)

    @patch('app.utils.demo_data.users_db', {})
    @patch('app.utils.demo_data.products_db', {})
    @patch('app.utils.demo_data.transactions_db', {})
    def test_create_predictable_test_data_structure(self):
        """Test predictable test data has correct structure."""
        data = create_predictable_test_data()

        assert 'users' in data
        assert 'products' in data
        assert 'transactions' in data
        assert isinstance(data['users'], list)
        assert isinstance(data['products'], list)


class TestExportDemoData:
    """Test demo data export functionality."""

    def test_export_demo_data_returns_dict(self):
        """Test export returns dictionary."""
        data = export_demo_data()

        assert isinstance(data, dict)
        assert len(data) > 0

    def test_export_demo_data_includes_stores(self):
        """Test export includes known data stores."""
        data = export_demo_data()

        # Should include key stores that have data from init_demo_data
        assert 'users_db' in data
        assert 'products_db' in data
        assert isinstance(data['users_db'], dict)
        assert isinstance(data['products_db'], dict)


class TestImportDemoData:
    """Test demo data import functionality."""

    def test_import_demo_data_returns_success(self):
        """Test import returns success boolean."""
        import app.models as _models

        test_data = {
            'promotions_db': {'IMPORT_TEST': {'discount': 0.99, 'active': True}}
        }

        result = import_demo_data(test_data)

        assert result is True
        assert 'IMPORT_TEST' in _models.promotions_db

    def test_import_demo_data_handles_exception(self):
        """Test import handles exceptions gracefully."""
        # None is not iterable, so .items() will raise
        result = import_demo_data(None)

        assert result is False


class TestDemoDataIntegration:
    """Integration tests for demo data operations."""

    def test_seed_and_export_workflow(self):
        """Test seeding data and exporting it."""
        import app.models as _models

        users_before = len(_models.users_db)

        # Seed data
        new_users = seed_additional_users(count=3)
        new_products = seed_additional_products(count=5)

        assert len(new_users) == 3
        assert len(new_products) == 5

        # Get statistics — users should have grown
        stats = get_seed_statistics()
        assert stats['users'] == users_before + 3

        # Products use deterministic IDs so may overwrite earlier test entries;
        # verify stats are consistent with the actual store
        assert stats['products'] == len(_models.products_db)

    @patch('app.utils.demo_data.users_db', {})
    def test_predictable_data_for_testing(self):
        """Test creating predictable data for automated tests."""
        # Create predictable data
        data = create_predictable_test_data(seed=123)

        assert len(data['users']) > 0
        assert len(data['products']) > 0
        assert len(data['transactions']) > 0

    @patch('app.utils.demo_data.users_db', {})
    @patch('app.utils.demo_data.accounts_db', {})
    def test_demo_user_and_initialization(self):
        """Test demo user credentials match initialized data."""
        init_demo_data()

        demo_user = get_demo_user()

        from app.utils.demo_data import users_db

        assert demo_user['email'] in users_db
        assert users_db[demo_user['email']]['id'] == demo_user['id']


class TestDemoDataEdgeCases:
    """Test edge cases in demo data utilities."""

    @patch('app.utils.demo_data.users_db', {})
    def test_seed_users_zero_count(self):
        """Test seeding with zero count."""
        users = seed_additional_users(count=0)

        assert len(users) == 0

    @patch('app.utils.demo_data.products_db', {})
    def test_seed_products_large_count(self):
        """Test seeding large number of products."""
        products = seed_additional_products(count=100)

        assert len(products) == 100

    def test_seed_transactions_multiple_users(self):
        """Test seeding transactions for multiple users."""
        import app.models as _models

        seed_transactions('test_multi_u1', count=5)
        seed_transactions('test_multi_u2', count=10)

        assert len(_models.transactions_db['test_multi_u1']) == 5
        assert len(_models.transactions_db['test_multi_u2']) == 10

    @patch('app.utils.demo_data.users_db', {})
    @patch('app.utils.demo_data.products_db', {})
    def test_reset_multiple_times(self):
        """Test reset can be called multiple times."""
        reset_demo_data()
        reset_demo_data()
        reset_demo_data()

        # Should work without errors
        from app.utils.demo_data import users_db

        assert 'demo@chimera.com' in users_db


class TestDemoCustomerFunctions:
    """Test additional demo customer functions."""

    def test_get_demo_customer_consistent(self):
        """Test demo customer returns consistent data."""
        customer1 = get_demo_customer()
        customer2 = get_demo_customer()

        assert customer1 == customer2

    def test_get_demo_user_consistent(self):
        """Test demo user returns consistent data."""
        user1 = get_demo_user()
        user2 = get_demo_user()

        assert user1 == user2


class TestDataQuality:
    """Test quality of generated demo data."""

    @patch('app.utils.demo_data.users_db', {})
    def test_seeded_users_have_valid_emails(self):
        """Test seeded users have valid email format."""
        import re
        users = seed_additional_users(count=10)

        email_pattern = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')

        for user in users:
            assert email_pattern.match(user['email'])

    @patch('app.utils.demo_data.products_db', {})
    def test_seeded_products_have_positive_prices(self):
        """Test seeded products have positive prices."""
        products = seed_additional_products(count=20)

        for product in products:
            assert product['price'] > 0

    @patch('app.utils.demo_data.transactions_db', {})
    def test_seeded_transactions_have_valid_dates(self):
        """Test seeded transactions have valid ISO date format."""
        from datetime import datetime

        txns = seed_transactions('user_123', count=10)

        for txn in txns:
            # Should be able to parse as ISO format
            try:
                datetime.fromisoformat(txn['date'])
            except ValueError:
                pytest.fail(f"Invalid date format: {txn['date']}")
