"""
Unit tests for Admin Routes (WS6).

Tests cover:
- User management operations and privilege escalation
- System configuration exposure
- Command injection vulnerabilities
- Remote code execution (RCE)
- Log access and tampering
- Attack simulation endpoints
- Data exfiltration
- Secret exposure
"""

import json
import base64
import pytest
from datetime import datetime


class TestUserManagement:
    """Test user management endpoints and authorization vulnerabilities."""

    def test_list_users_no_auth(self, client, mock_users):
        """Test that user list is exposed without authorization."""
        response = client.get('/api/v1/admin/users')

        assert response.status_code == 200
        data = response.get_json()
        assert 'users' in data
        assert len(data['users']) > 0
        assert 'warning' in data
        assert 'authorization' in data['warning'].lower()

    def test_list_users_password_hash_exposure(self, client, mock_users):
        """Test that password hashes are exposed."""
        response = client.get('/api/v1/admin/users')

        data = response.get_json()
        for user in data['users']:
            assert 'password_hash' in user
            assert 'api_key' in user
            assert user['password_hash'].startswith('md5:')

    def test_list_users_sensitive_fields(self, client, mock_users):
        """Test that all sensitive user fields are exposed."""
        response = client.get('/api/v1/admin/users')

        data = response.get_json()
        user = data['users'][0]
        required_fields = [
            'user_id', 'username', 'email', 'role', 'password_hash',
            'api_key', 'mfa_enabled', 'failed_login_attempts'
        ]
        for field in required_fields:
            assert field in user

    def test_get_user_details_idor(self, client):
        """Test IDOR vulnerability in user details endpoint."""
        # Can access any user's details without authorization
        response = client.get('/api/v1/admin/users/USR-9999')

        assert response.status_code == 200
        data = response.get_json()
        assert data['user_id'] == 'USR-9999'

    def test_get_user_security_questions_exposed(self, client, mock_users):
        """Test that security questions are exposed."""
        response = client.get('/api/v1/admin/users/USR-0001')

        data = response.get_json()
        assert 'security_questions' in data
        assert len(data['security_questions']) > 0
        assert 'answer_hash' in data['security_questions'][0]

    def test_get_user_login_history(self, client, mock_users):
        """Test that login history is exposed."""
        response = client.get('/api/v1/admin/users/USR-0001')

        data = response.get_json()
        assert 'login_history' in data
        assert len(data['login_history']) > 0
        for entry in data['login_history']:
            assert 'ip_address' in entry
            assert 'user_agent' in entry

    def test_elevate_privileges_no_auth(self, client, mock_users):
        """Test privilege escalation without authorization."""
        response = client.post(
            '/api/v1/admin/users/USR-0002/elevate',
            json={'role': 'admin'}
        )

        data = response.get_json()
        assert response.status_code == 200
        assert data['status'] == 'elevated'
        assert data['new_role'] == 'admin'
        assert 'warning' in data

    def test_elevate_self_to_admin(self, client, mock_users):
        """Test elevating own account to admin."""
        response = client.post(
            '/api/v1/admin/users/USR-0002/elevate',
            json={'role': 'admin'}
        )

        data = response.get_json()
        assert data['previous_role'] == 'user'
        assert data['new_role'] == 'admin'

    def test_elevate_to_superadmin(self, client):
        """Test elevating to superadmin role."""
        response = client.post(
            '/api/v1/admin/users/USR-0002/elevate',
            json={'role': 'superadmin'}
        )

        data = response.get_json()
        assert data['new_role'] == 'superadmin'


class TestUserExport:
    """Test user data export and exfiltration vulnerabilities."""

    def test_export_user_data_no_auth(self, client):
        """Test user data export without authorization."""
        response = client.get('/api/v1/admin/users/export')

        assert response.status_code == 200
        data = response.get_json()
        assert 'users' in data
        assert len(data['users']) > 0
        assert 'warning' in data

    def test_export_includes_passwords(self, client):
        """Test that export can include plaintext passwords."""
        response = client.get('/api/v1/admin/users/export?include_passwords=true')

        data = response.get_json()
        assert data['includes_passwords'] is True
        for user in data['users']:
            assert 'password_hash' in user
            assert 'password_plaintext' in user

    def test_export_includes_pii(self, client):
        """Test that export includes PII data."""
        response = client.get('/api/v1/admin/users/export')

        data = response.get_json()
        user = data['users'][0]
        pii_fields = ['ssn', 'phone', 'address', 'email']
        for field in pii_fields:
            assert field in user

    def test_export_format_options(self, client):
        """Test export with different format options."""
        for fmt in ['json', 'csv', 'xml']:
            response = client.get(f'/api/v1/admin/users/export?format={fmt}')
            data = response.get_json()
            assert data['format'] == fmt

    def test_export_large_dataset(self, client):
        """Test exporting large user dataset."""
        response = client.get('/api/v1/admin/users/export')

        data = response.get_json()
        assert data['total_count'] == 100  # Large export without limits


class TestSystemConfiguration:
    """Test system configuration exposure vulnerabilities."""

    def test_get_config_no_auth(self, client):
        """Test system configuration exposed without authorization."""
        response = client.get('/api/v1/admin/config')

        assert response.status_code == 200
        data = response.get_json()
        assert 'database' in data
        assert 'api_keys' in data
        assert 'security' in data
        assert 'warning' in data

    def test_config_database_credentials(self, client):
        """Test that database credentials are exposed."""
        response = client.get('/api/v1/admin/config')

        data = response.get_json()
        db_config = data['database']
        assert 'host' in db_config
        assert 'username' in db_config
        assert 'password' in db_config
        assert db_config['password'] != '***'  # Not redacted

    def test_config_api_keys_exposure(self, client):
        """Test that API keys are fully exposed."""
        response = client.get('/api/v1/admin/config')

        data = response.get_json()
        api_keys = data['api_keys']
        assert 'stripe' in api_keys
        assert 'sendgrid' in api_keys
        assert 'aws' in api_keys
        assert api_keys['stripe'].startswith('sk_live_')

    def test_config_aws_credentials(self, client):
        """Test that AWS credentials are exposed."""
        response = client.get('/api/v1/admin/config')

        data = response.get_json()
        aws = data['api_keys']['aws']
        assert 'access_key_id' in aws
        assert 'secret_access_key' in aws
        assert aws['access_key_id'].startswith('AKIA')

    def test_config_security_secrets(self, client):
        """Test that security secrets are exposed."""
        response = client.get('/api/v1/admin/config')

        data = response.get_json()
        security = data['security']
        assert 'secret_key' in security
        assert 'jwt_secret' in security
        assert 'encryption_key' in security

    def test_config_dangerous_features_enabled(self, client):
        """Test that dangerous features are shown as enabled."""
        response = client.get('/api/v1/admin/config')

        data = response.get_json()
        features = data['features']
        assert features['debug_mode'] is True
        assert features['detailed_errors'] is True
        assert features['admin_bypass'] is True

    def test_update_config_no_validation(self, client):
        """Test config update without validation."""
        response = client.post(
            '/api/v1/admin/config',
            json={
                'database': {'password': 'hacked123'},
                'features': {'admin_bypass': True}
            }
        )

        data = response.get_json()
        assert response.status_code == 200
        assert data['status'] == 'updated'


class TestSystemLogs:
    """Test log viewing and information disclosure."""

    def test_view_logs_no_auth(self, client):
        """Test logs are viewable without authorization."""
        response = client.get('/api/v1/admin/logs')

        assert response.status_code == 200
        data = response.get_json()
        assert 'logs' in data
        assert len(data['logs']) > 0
        assert 'warning' in data

    def test_logs_contain_sensitive_info(self, client):
        """Test that logs contain sensitive information."""
        response = client.get('/api/v1/admin/logs?lines=100')

        data = response.get_json()
        log_messages = [log['message'] for log in data['logs']]

        # Check for sensitive info in logs
        sensitive_patterns = ['password', 'api key', 'admin']
        has_sensitive = any(
            any(pattern in msg.lower() for pattern in sensitive_patterns)
            for msg in log_messages
        )
        assert has_sensitive

    def test_logs_different_types(self, client):
        """Test accessing different log types."""
        log_types = ['application', 'security', 'access', 'error']
        for log_type in log_types:
            response = client.get(f'/api/v1/admin/logs?type={log_type}')
            data = response.get_json()
            assert data['log_type'] == log_type

    def test_logs_line_limit(self, client):
        """Test log line limit parameter."""
        response = client.get('/api/v1/admin/logs?lines=500')

        data = response.get_json()
        assert data['total_lines'] == 500


class TestCommandInjection:
    """Test command injection vulnerabilities."""

    def test_backup_command_injection(self, client, command_injection_payloads):
        """Test command injection in backup endpoint."""
        for payload in command_injection_payloads[:3]:
            response = client.post(
                '/api/v1/admin/backup',
                json={
                    'backup_path': f'/tmp{payload}',
                    'backup_name': 'test_backup'
                }
            )

            data = response.get_json()
            if 'vulnerability' in data:
                assert data['vulnerability'] == 'COMMAND_INJECTION_DETECTED'
                assert 'executed_command' in data

    def test_backup_semicolon_injection(self, client):
        """Test semicolon-based command injection."""
        response = client.post(
            '/api/v1/admin/backup',
            json={'backup_path': '/tmp; cat /etc/passwd'}
        )

        data = response.get_json()
        assert data['vulnerability'] == 'COMMAND_INJECTION_DETECTED'
        assert 'root:x:0:0' in data['injected_output']

    def test_backup_pipe_injection(self, client):
        """Test pipe-based command injection."""
        response = client.post(
            '/api/v1/admin/backup',
            json={'backup_path': '/tmp | ls -la /'}
        )

        data = response.get_json()
        assert data['vulnerability'] == 'COMMAND_INJECTION_DETECTED'

    def test_backup_backtick_injection(self, client):
        """Test backtick command substitution."""
        response = client.post(
            '/api/v1/admin/backup',
            json={'backup_path': '/tmp`whoami`'}
        )

        data = response.get_json()
        assert data['vulnerability'] == 'COMMAND_INJECTION_DETECTED'

    def test_backup_normal_path(self, client):
        """Test normal backup without injection."""
        response = client.post(
            '/api/v1/admin/backup',
            json={
                'backup_path': '/var/backups',
                'backup_name': 'daily_backup'
            }
        )

        data = response.get_json()
        assert data['status'] == 'started'
        assert 'backup_id' in data


class TestRemoteCodeExecution:
    """Test remote code execution vulnerabilities."""

    def test_execute_command_no_auth(self, client):
        """Test command execution without authorization."""
        response = client.post(
            '/api/v1/admin/execute',
            json={'command': 'ls', 'args': ['-la']}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'executed'

    def test_execute_dangerous_command(self, client):
        """Test execution of dangerous commands."""
        dangerous_cmds = ['rm', 'dd', 'shutdown', 'kill']
        for cmd in dangerous_cmds:
            response = client.post(
                '/api/v1/admin/execute',
                json={'command': cmd, 'args': ['-rf', '/']}
            )

            data = response.get_json()
            assert data['is_dangerous'] is True

    def test_execute_command_injection(self, client):
        """Test command injection in execute endpoint."""
        response = client.post(
            '/api/v1/admin/execute',
            json={'command': 'ls; cat /etc/passwd'}
        )

        data = response.get_json()
        assert data['vulnerability'] == 'COMMAND_INJECTION'
        assert 'root:x:0:0' in data['output']

    def test_execute_pipe_injection(self, client):
        """Test pipe injection in execute endpoint."""
        response = client.post(
            '/api/v1/admin/execute',
            json={'command': 'ls | grep config'}
        )

        data = response.get_json()
        assert data['vulnerability'] == 'COMMAND_INJECTION'

    def test_execute_multiline_injection(self, client):
        """Test multiline command injection."""
        response = client.post(
            '/api/v1/admin/execute',
            json={'command': 'ls\ncat /etc/passwd'}
        )

        data = response.get_json()
        assert data['vulnerability'] == 'COMMAND_INJECTION'

    def test_execute_file_disclosure(self, client):
        """Test file disclosure via command execution."""
        response = client.post(
            '/api/v1/admin/execute',
            json={'command': 'cat; cat /etc/passwd'}
        )

        data = response.get_json()
        assert 'database.yml' in data['output'] or 'api_keys.json' in data['output']


class TestAttackSimulation:
    """Test attack simulation endpoints."""

    def test_sql_injection_simulation(self, client, sql_injection_payloads):
        """Test SQL injection attack simulation."""
        response = client.post(
            '/api/v1/admin/attack/sqli',
            json={
                'query': "id=1' UNION SELECT * FROM users--",
                'table': 'users'
            }
        )

        data = response.get_json()
        assert data['test'] == 'SQL_INJECTION'
        assert data['status'] == 'vulnerable'
        assert 'exposed_data' in data

    def test_sql_injection_or_bypass(self, client):
        """Test OR-based SQL injection."""
        response = client.post(
            '/api/v1/admin/attack/sqli',
            json={'query': "username='admin' OR 1=1--"}
        )

        data = response.get_json()
        assert data['status'] == 'vulnerable'
        assert 'exposed_tables' in data['result']

    def test_sql_injection_drop_table(self, client):
        """Test DROP TABLE SQL injection."""
        response = client.post(
            '/api/v1/admin/attack/sqli',
            json={'query': "'; DROP TABLE users; --"}
        )

        data = response.get_json()
        assert data['status'] == 'vulnerable'

    def test_xxe_injection_simulation(self, client, xxe_injection_payloads):
        """Test XXE injection attack simulation."""
        response = client.post(
            '/api/v1/admin/attack/xxe',
            json={'xml': xxe_injection_payloads[0]}
        )

        data = response.get_json()
        assert data['test'] == 'XXE_INJECTION'
        assert data['status'] == 'vulnerable'
        assert '/etc/passwd' in data['result']['exposed_files']

    def test_xxe_file_inclusion(self, client):
        """Test XXE file inclusion."""
        response = client.post(
            '/api/v1/admin/attack/xxe',
            json={
                'xml': '<!ENTITY xxe SYSTEM "file:///etc/shadow">'
            }
        )

        data = response.get_json()
        assert data['status'] == 'vulnerable'
        assert 'file_content' in data['result']

    def test_ssrf_simulation(self, client, ssrf_payloads):
        """Test SSRF attack simulation."""
        for payload in ssrf_payloads[:3]:
            response = client.post(
                '/api/v1/admin/attack/ssrf',
                json={'url': payload, 'method': 'GET'}
            )

            data = response.get_json()
            if 'vulnerability' in data:
                assert data['test'] == 'SSRF'
                assert data['status'] == 'vulnerable'

    def test_ssrf_metadata_service(self, client):
        """Test SSRF to cloud metadata service."""
        response = client.post(
            '/api/v1/admin/attack/ssrf',
            json={'url': 'http://169.254.169.254/latest/meta-data/'}
        )

        data = response.get_json()
        assert data['status'] == 'vulnerable'
        assert 'metadata' in data['result']['response_body']
        assert 'credentials' in data['result']['response_body']['metadata']

    def test_ssrf_internal_services(self, client):
        """Test SSRF to internal services."""
        response = client.post(
            '/api/v1/admin/attack/ssrf',
            json={'url': 'http://localhost:8080/admin'}
        )

        data = response.get_json()
        assert 'internal_services' in data['result']

    def test_deserialization_simulation(self, client, deserialization_payloads):
        """Test insecure deserialization attack simulation."""
        response = client.post(
            '/api/v1/admin/attack/deserialize',
            json={
                'data': deserialization_payloads[0],
                'format': 'pickle'
            }
        )

        data = response.get_json()
        assert data['test'] == 'DESERIALIZATION'
        assert data['status'] == 'vulnerable'

    def test_deserialization_rce(self, client):
        """Test RCE via deserialization."""
        payload = base64.b64encode(b'pickle___reduce__malicious_code').decode()
        response = client.post(
            '/api/v1/admin/attack/deserialize',
            json={'data': payload}
        )

        data = response.get_json()
        assert data['result']['code_executed'] is True
        assert data['result']['payload_type'] == 'remote_code_execution'


class TestLegacyEndpoints:
    """Test legacy admin endpoints."""

    def test_transaction_splitting(self, client):
        """Test transaction splitting to avoid reporting."""
        response = client.post(
            '/api/transactions/split',
            json={'amount': 10000, 'split_count': 5}
        )

        data = response.get_json()
        assert response.status_code == 200
        assert data['original_amount'] == 10000
        assert data['split_amount'] == 2000
        assert 'warning' in data
        assert 'structuring' in data['warning'].lower()

    def test_orders_override(self, client):
        """Test administrative order override."""
        response = client.post(
            '/api/admin/orders/override',
            json={
                'order_id': 'ORD-12345',
                'status': 'completed',
                'reason': 'manual intervention'
            }
        )

        data = response.get_json()
        assert data['status'] == 'overridden'
        assert data['overridden_by'] == 'admin'

    def test_payment_methods_exposure(self, client):
        """Test customer payment methods exposure."""
        response = client.get('/api/customers/payment-methods?customer_id=CUST-001')

        assert response.status_code == 200
        data = response.get_json()
        assert 'payment_methods' in data
        assert len(data['payment_methods']) > 0

    def test_customer_export_pii(self, client):
        """Test customer export includes PII."""
        response = client.get('/api/customers/export?segment=all')

        data = response.get_json()
        assert 'customers' in data
        customer = data['customers'][0]
        assert 'ssn' in customer
        assert 'credit_card_last4' in customer
        assert 'warning' in data


class TestLogTampering:
    """Test log deletion and tampering vulnerabilities."""

    def test_delete_logs(self, client):
        """Test ability to delete audit logs."""
        response = client.post(
            '/api/logs/deletion',
            json={'systems': ['siem', 'firewall', 'ids']}
        )

        data = response.get_json()
        assert response.status_code == 200
        assert data['logs_deleted'] is True
        assert data['recovery_possible'] is False
        assert 'warning' in data

    def test_delete_all_logs(self, client):
        """Test deleting all system logs."""
        response = client.post(
            '/api/logs/deletion',
            json={'systems': ['all']}
        )

        data = response.get_json()
        assert data['logs_deleted'] is True


class TestSystemFingerprinting:
    """Test system version and fingerprinting endpoints."""

    def test_system_version_disclosure(self, client):
        """Test system version information disclosure."""
        response = client.get('/api/system/version')

        assert response.status_code == 200
        data = response.get_json()
        assert 'application' in data
        assert 'version' in data
        assert 'build' in data
        assert 'frameworks' in data
        assert 'python_version' in data
        assert 'os' in data

    def test_version_detailed_info(self, client):
        """Test detailed version information exposure."""
        response = client.get('/api/system/version')

        data = response.get_json()
        assert 'database' in data
        assert 'server' in data
        # Version info useful for attackers
        assert data['environment'] in ['demo', 'production', 'development']


class TestUserCreation:
    """Test administrative user creation vulnerabilities."""

    def test_create_user_no_auth(self, client):
        """Test user creation without authorization."""
        response = client.post(
            '/api/admin/users/create',
            json={'username': 'backdoor', 'role': 'admin'}
        )

        data = response.get_json()
        assert response.status_code == 200
        assert data['status'] == 'created'
        assert data['role'] == 'admin'

    def test_create_admin_user(self, client):
        """Test creating admin user without authorization."""
        response = client.post(
            '/api/admin/users/create',
            json={'username': 'newadmin', 'role': 'admin'}
        )

        data = response.get_json()
        assert data['role'] == 'admin'
        assert 'password' in data
        assert 'warning' in data

    def test_created_user_password_exposure(self, client):
        """Test that created user password is exposed."""
        response = client.post(
            '/api/admin/users/create',
            json={'username': 'testuser'}
        )

        data = response.get_json()
        assert 'password' in data
        assert data['password'].startswith('TempPass')


class TestTransactionExport:
    """Test transaction export and data exfiltration."""

    def test_export_transactions(self, client):
        """Test transaction data export."""
        response = client.get('/api/transactions/export?from=2025-01-01&to=2025-12-31')

        assert response.status_code == 200
        data = response.get_json()
        assert 'transactions' in data
        assert len(data['transactions']) > 0
        assert 'total_amount' in data

    def test_export_all_transactions(self, client):
        """Test exporting all transaction data."""
        response = client.get('/api/transactions/export')

        data = response.get_json()
        assert data['total_count'] == 100
        assert 'total_amount' in data

    def test_export_transaction_formats(self, client):
        """Test transaction export in different formats."""
        for fmt in ['json', 'csv', 'xml']:
            response = client.get(f'/api/transactions/export?format={fmt}')
            data = response.get_json()
            assert data['format'] == fmt


class TestAuthorizationBypass:
    """Test authorization bypass vulnerabilities across admin endpoints."""

    def test_no_admin_role_check(self, client, user_headers):
        """Test that admin endpoints don't check for admin role."""
        endpoints = [
            '/api/v1/admin/users',
            '/api/v1/admin/config',
            '/api/v1/admin/logs'
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=user_headers)
            # Should return 403 but returns 200 (vulnerability)
            assert response.status_code == 200

    def test_no_token_validation(self, client):
        """Test that no token validation is performed."""
        response = client.get('/api/v1/admin/users')
        assert response.status_code == 200  # Should be 401

    def test_privilege_escalation_chain(self, client):
        """Test complete privilege escalation chain."""
        # 1. List users
        response = client.get('/api/v1/admin/users')
        assert response.status_code == 200

        # 2. Get admin user details
        response = client.get('/api/v1/admin/users/USR-0001')
        assert response.status_code == 200

        # 3. Elevate own privileges
        response = client.post(
            '/api/v1/admin/users/USR-0002/elevate',
            json={'role': 'admin'}
        )
        assert response.status_code == 200
        assert response.get_json()['new_role'] == 'admin'

        # 4. Create backdoor admin user
        response = client.post(
            '/api/admin/users/create',
            json={'username': 'backdoor', 'role': 'admin'}
        )
        assert response.status_code == 200


class TestCriticalVulnerabilities:
    """Test critical security vulnerabilities requiring immediate attention."""

    def test_critical_rce_via_execute(self, client):
        """Critical: Direct remote code execution."""
        response = client.post(
            '/api/v1/admin/execute',
            json={'command': 'cat /etc/passwd'}
        )

        data = response.get_json()
        assert 'executed' in data['status'].lower()

    def test_critical_config_secrets_exposed(self, client):
        """Critical: All system secrets exposed."""
        response = client.get('/api/v1/admin/config')

        data = response.get_json()
        # AWS credentials exposed
        assert 'AKIA' in data['api_keys']['aws']['access_key_id']
        # Database password exposed
        assert len(data['database']['password']) > 5

    def test_critical_privilege_escalation(self, client):
        """Critical: Any user can become admin."""
        response = client.post(
            '/api/v1/admin/users/USR-0002/elevate',
            json={'role': 'admin'}
        )

        assert response.get_json()['new_role'] == 'admin'

    def test_critical_audit_log_deletion(self, client):
        """Critical: Audit logs can be deleted."""
        response = client.post(
            '/api/logs/deletion',
            json={'systems': ['all']}
        )

        data = response.get_json()
        assert data['recovery_possible'] is False

    def test_critical_user_export_with_passwords(self, client):
        """Critical: User passwords exported in plaintext."""
        response = client.get('/api/v1/admin/users/export?include_passwords=true')

        data = response.get_json()
        assert any('password_plaintext' in user for user in data['users'])


class TestSecurityControls:
    """Test missing security controls across admin endpoints."""

    def test_no_rate_limiting(self, client):
        """Test absence of rate limiting on admin endpoints."""
        for _ in range(20):
            response = client.get('/api/v1/admin/users')
            assert response.status_code == 200

    def test_no_input_validation(self, client):
        """Test lack of input validation."""
        response = client.post(
            '/api/v1/admin/execute',
            json={'command': '../../../etc/passwd'}
        )
        assert response.status_code == 200

    def test_no_csrf_protection(self, client):
        """Test absence of CSRF protection."""
        response = client.post(
            '/api/v1/admin/users/USR-0002/elevate',
            json={'role': 'admin'}
        )
        # Should require CSRF token but doesn't
        assert response.status_code == 200

    def test_no_session_validation(self, client):
        """Test no session validation on admin operations."""
        response = client.post(
            '/api/admin/users/create',
            json={'username': 'hacker', 'role': 'admin'}
        )
        assert response.status_code == 200


class TestComplianceViolations:
    """Test compliance and regulatory violations."""

    def test_pii_exposure_violation(self, client):
        """Test PII exposure violates data protection regulations."""
        response = client.get('/api/v1/admin/users/export')

        data = response.get_json()
        # SSN exposure violates regulations
        assert any('ssn' in user for user in data['users'])

    def test_password_storage_violation(self, client):
        """Test password exposure violates security standards."""
        response = client.get('/api/v1/admin/users/export?include_passwords=true')

        data = response.get_json()
        # Plaintext passwords violate security standards
        assert data['includes_passwords'] is True

    def test_audit_tampering_violation(self, client):
        """Test audit log tampering violates compliance requirements."""
        response = client.post(
            '/api/logs/deletion',
            json={'systems': ['audit', 'compliance']}
        )

        data = response.get_json()
        # Audit log deletion violates SOX, PCI-DSS, HIPAA
        assert data['logs_deleted'] is True
