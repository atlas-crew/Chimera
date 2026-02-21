"""
Routes for admin endpoints.
Demonstrates privilege escalation, command injection, and admin panel vulnerabilities.
"""

from flask import request, jsonify, render_template_string, session
from datetime import datetime, timedelta
import uuid
import random
import json
import time
import subprocess
import os
import pickle
import base64

from . import admin_bp
from app.models import *


# ============================================================================
# USER MANAGEMENT - Privilege Escalation Vulnerabilities
# ============================================================================

@admin_bp.route('/api/v1/admin/users')
def list_users():
    """List all users - Missing authorization"""
    # Vulnerability: No admin authorization check
    # Vulnerability: Exposes sensitive user data including password hashes

    with users_db_lock:
        users = [
            {
                'user_id': user_id,
                'username': user.get('username'),
                'email': user.get('email'),
                'role': user.get('role', 'user'),
                'status': user.get('status', 'active'),
                'password_hash': user.get('password_hash', 'md5:' + str(random.randint(100000, 999999))),
                'created_at': user.get('created_at', '2025-01-01'),
                'last_login': user.get('last_login', '2025-10-01'),
                'failed_login_attempts': user.get('failed_login_attempts', 0),
                'mfa_enabled': user.get('mfa_enabled', False),
                'api_key': user.get('api_key', f'sk-{uuid.uuid4().hex}')
            }
            for user_id, user in users_db.items()
        ]

    # Add mock users if database is empty
    if not users:
        users = [
            {
                'user_id': f'USR-{i:04d}',
                'username': username,
                'email': f'{username.lower()}@example.com',
                'role': role,
                'status': 'active',
                'password_hash': f'md5:{random.randint(100000000, 999999999)}',
                'created_at': '2025-01-15',
                'last_login': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                'failed_login_attempts': random.randint(0, 3),
                'mfa_enabled': random.choice([True, False]),
                'api_key': f'sk-{uuid.uuid4().hex}'
            }
            for i, (username, role) in enumerate([
                ('admin', 'admin'),
                ('john.smith', 'user'),
                ('jane.doe', 'user'),
                ('manager', 'manager'),
                ('support', 'support')
            ])
        ]

    return jsonify({
        'users': users,
        'total_count': len(users),
        'warning': 'Sensitive user data exposed without authorization'
    })


@admin_bp.route('/api/v1/admin/users/<user_id>')
def get_user_details(user_id):
    """Get user details - IDOR vulnerability"""
    # Vulnerability: Can access any user's details without authorization
    # Vulnerability: Exposes password hash and security questions

    user = get_user_by_id(user_id)
    if not user:
        # Return mock data for any user_id
        user = {
            'user_id': user_id,
            'username': f'user_{user_id[-4:]}',
            'email': f'user{user_id[-4:]}@example.com',
            'role': random.choice(['user', 'manager', 'admin']),
            'status': 'active'
        }

    return jsonify({
        'user_id': user_id,
        'username': user.get('username'),
        'email': user.get('email'),
        'full_name': user.get('full_name', 'John Doe'),
        'role': user.get('role', 'user'),
        'status': user.get('status', 'active'),
        'password_hash': user.get('password_hash', f'md5:{random.randint(100000000, 999999999)}'),
        'security_questions': [
            {'question': "What is your mother's maiden name?", 'answer_hash': 'md5:abc123'},
            {'question': 'What city were you born in?', 'answer_hash': 'md5:def456'}
        ],
        'permissions': user.get('permissions', ['read', 'write']),
        'created_at': user.get('created_at', '2025-01-01'),
        'last_login': user.get('last_login'),
        'login_history': [
            {
                'timestamp': (datetime.now() - timedelta(days=i)).isoformat(),
                'ip_address': f'192.168.1.{random.randint(1, 254)}',
                'user_agent': 'Mozilla/5.0',
                'success': True
            }
            for i in range(5)
        ]
    })


@admin_bp.route('/api/v1/admin/users/<user_id>/elevate', methods=['POST'])
def elevate_privileges(user_id):
    """Elevate user privileges - Missing authorization"""
    # Vulnerability: No admin authorization check
    # Vulnerability: Can elevate any user to admin

    data = request.get_json() or {}
    new_role = data.get('role', 'admin')

    return jsonify({
        'status': 'elevated',
        'user_id': user_id,
        'previous_role': 'user',
        'new_role': new_role,
        'elevated_by': 'unauthenticated_user',
        'timestamp': datetime.now().isoformat(),
        'warning': 'Privilege escalation performed without authorization'
    })


@admin_bp.route('/api/v1/admin/users/export')
def export_user_data():
    """Export user data - Data exfiltration"""
    # Vulnerability: No authorization check
    # Vulnerability: Exports sensitive user data including credentials

    export_format = request.args.get('format', 'json')
    include_passwords = request.args.get('include_passwords', 'true').lower() == 'true'

    users = []
    for i in range(100):
        user_data = {
            'user_id': f'USR-{i:04d}',
            'username': f'user{i}',
            'email': f'user{i}@example.com',
            'role': random.choice(['user', 'manager', 'admin']),
            'ssn': f'{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}',
            'phone': f'+1-555-{random.randint(1000, 9999)}',
            'address': f'{random.randint(100, 9999)} Main St, City, ST 12345'
        }

        if include_passwords:
            user_data['password_hash'] = f'md5:{random.randint(100000000, 999999999)}'
            user_data['password_plaintext'] = f'Password{random.randint(1, 999)}!'

        users.append(user_data)

    export_id = f'EXPORT-{uuid.uuid4().hex[:8]}'

    return jsonify({
        'export_id': export_id,
        'format': export_format,
        'users': users,
        'total_count': len(users),
        'includes_passwords': include_passwords,
        'warning': 'Sensitive user data exported without authorization'
    })


# ============================================================================
# SYSTEM OPERATIONS - Command Injection Vulnerabilities
# ============================================================================

@admin_bp.route('/api/v1/admin/config', methods=['GET', 'POST'])
def system_config():
    """System configuration - Exposes sensitive configuration"""
    # Vulnerability: Exposes sensitive configuration without authorization
    # Vulnerability: Can modify configuration without validation

    if request.method == 'POST':
        data = request.get_json() or {}
        return jsonify({
            'status': 'updated',
            'config': data,
            'warning': 'Configuration updated without validation'
        })

    # GET request - expose configuration
    return jsonify({
        'database': {
            'host': 'db.internal.example.com',
            'port': 5432,
            'username': 'admin',
            'password': 'SuperSecret123!',
            'database': 'production_db'
        },
        'api_keys': {
            'stripe': 'sk_live_51HxyzABCDEFG123456789',
            'sendgrid': 'SG.1234567890.ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij',
            'aws': {
                'access_key_id': 'AKIAIOSFODNN7EXAMPLE',
                'secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
            }
        },
        'security': {
            'secret_key': 'django-insecure-secret-key-12345',
            'jwt_secret': 'jwt-secret-key-67890',
            'encryption_key': 'aes-256-key-ABCDEFGH'
        },
        'features': {
            'debug_mode': True,
            'detailed_errors': True,
            'admin_bypass': True
        },
        'warning': 'Sensitive configuration exposed without authorization'
    })


@admin_bp.route('/api/v1/admin/logs')
def view_logs():
    """View system logs - Information disclosure"""
    # Vulnerability: Exposes detailed system logs without authorization
    # Vulnerability: May contain sensitive information

    log_type = request.args.get('type', 'application')
    lines = int(request.args.get('lines', 100))

    logs = [
        {
            'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat(),
            'level': random.choice(['INFO', 'WARN', 'ERROR', 'DEBUG']),
            'message': random.choice([
                'User login attempt from 192.168.1.100',
                'Database query executed: SELECT * FROM users WHERE password=...',
                'API key validation failed for key sk_live_...',
                'Admin panel accessed by user admin',
                'System configuration changed',
                'Backup completed successfully',
                'Failed authentication attempt: username=admin, password=admin123'
            ]),
            'source': random.choice(['auth.py', 'database.py', 'api.py', 'admin.py'])
        }
        for i in range(lines)
    ]

    return jsonify({
        'log_type': log_type,
        'logs': logs,
        'total_lines': len(logs),
        'warning': 'Detailed logs exposed without authorization'
    })


@admin_bp.route('/api/v1/admin/backup', methods=['POST'])
def trigger_backup():
    """Trigger backup - Command injection vulnerability"""
    # Vulnerability: Command injection through backup path parameter
    # Vulnerability: No authorization check

    data = request.get_json() or {}
    backup_path = data.get('backup_path', '/var/backups')
    backup_name = data.get('backup_name', f'backup_{datetime.now().strftime("%Y%m%d")}')

    # Vulnerability: Command injection through unsanitized input
    # Example: backup_path="/tmp; cat /etc/passwd"
    if any(char in backup_path for char in [';', '|', '&', '$', '`']):
        # Simulate command injection
        return jsonify({
            'vulnerability': 'COMMAND_INJECTION_DETECTED',
            'backup_path': backup_path,
            'message': 'Command injection successful',
            'executed_command': f'mkdir -p {backup_path} && tar -czf {backup_path}/{backup_name}.tar.gz /var/www',
            'injected_output': 'root:x:0:0:root:/root:/bin/bash\nbin:x:1:1:bin:/bin:/sbin/nologin'
        })

    backup_id = f'BACKUP-{uuid.uuid4().hex[:8]}'

    return jsonify({
        'status': 'started',
        'backup_id': backup_id,
        'backup_path': backup_path,
        'backup_name': backup_name,
        'estimated_size_mb': random.randint(100, 5000),
        'warning': 'Backup command vulnerable to injection'
    })


@admin_bp.route('/api/v1/admin/execute', methods=['POST'])
def execute_command():
    """Execute commands - Direct command injection"""
    # Vulnerability: Direct command execution without validation
    # Vulnerability: No authorization check

    data = request.get_json() or {}
    command = data.get('command', '')
    args = data.get('args', [])

    # Vulnerability: Direct command execution
    full_command = f"{command} {' '.join(args)}"

    # Simulate command execution
    if command:
        # Detect dangerous commands
        dangerous_commands = ['rm', 'dd', 'mkfs', 'shutdown', 'reboot', 'kill']
        is_dangerous = any(cmd in command.lower() for cmd in dangerous_commands)

        # Simulate command injection payloads
        if any(char in command for char in [';', '|', '&', '$', '`', '\n']):
            return jsonify({
                'vulnerability': 'COMMAND_INJECTION',
                'command': full_command,
                'message': 'Multiple commands executed',
                'output': '''
                total 128
                drwxr-xr-x  2 root root 4096 Oct 11 12:34 config
                drwxr-xr-x  3 root root 4096 Oct 11 12:34 secrets
                -rw-------  1 root root  451 Oct 11 12:34 database.yml
                -rw-------  1 root root  892 Oct 11 12:34 api_keys.json

                root:x:0:0:root:/root:/bin/bash
                www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
                ''',
                'warning': 'Command injection vulnerability exploited'
            })

        return jsonify({
            'status': 'executed',
            'command': full_command,
            'exit_code': 0,
            'output': f'Executed: {full_command}\nSuccess',
            'is_dangerous': is_dangerous,
            'warning': 'Direct command execution without validation'
        })

    return jsonify({
        'error': 'No command provided'
    }), 400


# ============================================================================
# ATTACK SIMULATION - Security Testing Endpoints
# ============================================================================

@admin_bp.route('/api/v1/admin/attack/sqli', methods=['POST'])
def test_sql_injection():
    """SQL injection test endpoint"""
    # Intentionally vulnerable endpoint for WAF testing

    data = request.get_json() or {}
    query = data.get('query', '')
    table = data.get('table', 'users')

    # Simulate SQL injection
    sql_query = f"SELECT * FROM {table} WHERE {query}"

    # Detect SQL injection patterns
    sql_keywords = ['union', 'select', 'drop', 'delete', 'insert', 'update', '--', ';', 'or 1=1', 'or 1=1--']
    is_injection = any(keyword in query.lower() for keyword in sql_keywords)

    if is_injection:
        return jsonify({
            'test': 'SQL_INJECTION',
            'status': 'vulnerable',
            'query': sql_query,
            'result': {
                'rows_affected': 9999,
                'exposed_tables': ['users', 'admin', 'credentials', 'sessions'],
                'exposed_data': [
                    {'username': 'admin', 'password_hash': 'md5:5f4dcc3b5aa765d61d8327deb882cf99'},
                    {'username': 'root', 'password_hash': 'md5:63a9f0ea7bb98050796b649e85481845'}
                ]
            },
            'warning': 'SQL injection vulnerability confirmed'
        })

    return jsonify({
        'test': 'SQL_INJECTION',
        'status': 'tested',
        'query': sql_query,
        'result': 'No injection detected'
    })


@admin_bp.route('/api/v1/admin/attack/xxe', methods=['POST'])
def test_xxe_injection():
    """XXE injection test endpoint"""
    # Intentionally vulnerable to XXE

    data = request.get_json() or {}
    xml_data = data.get('xml', '')

    # Detect XXE patterns
    xxe_patterns = ['<!ENTITY', '<!DOCTYPE', 'SYSTEM', 'file://', 'http://']
    is_xxe = any(pattern in xml_data for pattern in xxe_patterns)

    if is_xxe:
        return jsonify({
            'test': 'XXE_INJECTION',
            'status': 'vulnerable',
            'xml_input': xml_data,
            'result': {
                'external_entity_processed': True,
                'file_content': '''root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin''',
                'exposed_files': ['/etc/passwd', '/etc/shadow', '/app/config/database.yml']
            },
            'warning': 'XXE injection vulnerability confirmed'
        })

    return jsonify({
        'test': 'XXE_INJECTION',
        'status': 'tested',
        'result': 'No XXE detected'
    })


@admin_bp.route('/api/v1/admin/attack/ssrf', methods=['POST'])
def test_ssrf():
    """SSRF test endpoint"""
    # Intentionally vulnerable to SSRF

    data = request.get_json() or {}
    url = data.get('url', '')
    method = data.get('method', 'GET')

    # Detect SSRF patterns
    ssrf_patterns = ['localhost', '127.0.0.1', '169.254.169.254', '10.', '192.168', '172.16', 'metadata']
    is_ssrf = any(pattern in url.lower() for pattern in ssrf_patterns)

    if is_ssrf:
        return jsonify({
            'test': 'SSRF',
            'status': 'vulnerable',
            'url': url,
            'result': {
                'request_sent': True,
                'response_code': 200,
                'response_body': {
                    'metadata': {
                        'instance-id': 'i-1234567890abcdef0',
                        'iam-role': 'production-admin-role',
                        'credentials': {
                            'AccessKeyId': 'ASIAIOSFODNN7EXAMPLE',
                            'SecretAccessKey': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
                            'Token': 'token123456'
                        }
                    }
                },
                'internal_services': [
                    'http://localhost:8080/admin',
                    'http://10.0.0.5:3306/mysql',
                    'http://169.254.169.254/latest/meta-data/'
                ]
            },
            'warning': 'SSRF vulnerability confirmed'
        })

    return jsonify({
        'test': 'SSRF',
        'status': 'tested',
        'url': url,
        'result': 'No SSRF detected'
    })


@admin_bp.route('/api/v1/admin/attack/deserialize', methods=['POST'])
def test_deserialization():
    """Insecure deserialization test endpoint"""
    # Intentionally vulnerable to deserialization attacks

    data = request.get_json() or {}
    serialized_data = data.get('data', '')
    format_type = data.get('format', 'pickle')

    try:
        # Detect deserialization payloads
        if serialized_data:
            decoded = base64.b64decode(serialized_data)

            # Detect pickle payloads
            if b'pickle' in decoded or b'__reduce__' in decoded or b'__setstate__' in decoded:
                return jsonify({
                    'test': 'DESERIALIZATION',
                    'status': 'vulnerable',
                    'format': format_type,
                    'result': {
                        'deserialized': True,
                        'code_executed': True,
                        'payload_type': 'remote_code_execution',
                        'impact': 'Full system compromise possible',
                        'executed_commands': [
                            'import os',
                            'os.system("whoami")',
                            'os.system("cat /etc/passwd")'
                        ]
                    },
                    'warning': 'Insecure deserialization vulnerability confirmed'
                })
    except:
        pass

    return jsonify({
        'test': 'DESERIALIZATION',
        'status': 'tested',
        'result': 'No deserialization vulnerability detected'
    })


# ============================================================================
# LEGACY ADMIN ENDPOINTS
# ============================================================================

@admin_bp.route('/api/transactions/split', methods=['POST'])
def transactions_split():
    """Transaction splitting to avoid reporting thresholds"""
    data = request.get_json() or {}
    original_amount = data.get('amount', 0)
    split_count = data.get('split_count', 1)

    split_amount = original_amount / split_count if split_count > 0 else 0

    return jsonify({
        'original_amount': original_amount,
        'split_count': split_count,
        'split_amount': split_amount,
        'warning': 'Transaction structuring to avoid reporting'
    })


@admin_bp.route('/api/admin/orders/override', methods=['POST'])
def admin_orders_override():
    """Administrative override of orders"""
    data = request.get_json() or {}
    order_id = data.get('order_id')
    new_status = data.get('status')
    override_reason = data.get('reason', 'manual override')

    return jsonify({
        'status': 'overridden',
        'order_id': order_id,
        'new_status': new_status,
        'reason': override_reason,
        'overridden_by': 'admin',
        'timestamp': datetime.now().isoformat()
    })


@admin_bp.route('/api/customers/payment-methods')
def customers_payment_methods():
    """List customer payment methods"""
    customer_id = request.args.get('customer_id')

    payment_methods = [
        {
            'method_id': f'PM-{uuid.uuid4().hex[:8]}',
            'type': random.choice(['credit_card', 'debit_card', 'bank_account']),
            'last4': f'{random.randint(1000, 9999)}',
            'brand': random.choice(['Visa', 'Mastercard', 'Amex', 'Discover']),
            'exp_month': random.randint(1, 12),
            'exp_year': random.randint(2025, 2030),
            'is_default': random.choice([True, False])
        }
        for _ in range(3)
    ]

    return jsonify({
        'customer_id': customer_id,
        'payment_methods': payment_methods
    })


@admin_bp.route('/api/customers/export')
def customers_export():
    """Export customer roster - sensitive data exfiltration"""
    segment = request.args.get('segment', 'all')

    customers = [
        {
            'customer_id': f'CUST-{i:06d}',
            'name': f'Customer {i}',
            'email': f'customer{i}@example.com',
            'phone': f'+1-555-{random.randint(1000, 9999)}',
            'address': f'{random.randint(100, 9999)} Street, City, ST',
            'total_purchases': random.randint(1, 100),
            'lifetime_value': random.randint(100, 10000),
            'credit_card_last4': f'{random.randint(1000, 9999)}',
            'ssn': f'{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}'
        }
        for i in range(50)
    ]

    return jsonify({
        'segment': segment,
        'customers': customers,
        'total_count': len(customers),
        'warning': 'Sensitive customer data exported'
    })


@admin_bp.route('/api/logs/deletion', methods=['POST'])
def logs_deletion():
    """Delete logs - Evidence tampering"""
    data = request.get_json() or {}
    systems = data.get('systems', ['siem', 'firewall'])

    return jsonify({
        'systems_targeted': systems,
        'logs_deleted': True,
        'recovery_possible': False,
        'warning': 'Audit logs deleted'
    })


@admin_bp.route('/api/system/version')
def system_version():
    """System version endpoint for fingerprinting"""
    return jsonify({
        'application': ' Demo Platform',
        'version': '2.1.0',
        'build': '20241201-1234',
        'environment': 'demo',
        'frameworks': ['Flask', 'Python3.9'],
        'database': 'in-memory',
        'server': 'gunicorn/20.1.0',
        'python_version': '3.9.18',
        'os': 'Linux 5.10.0'
    })


@admin_bp.route('/api/admin/users/create', methods=['POST'])
def admin_create_user():
    """Administrative user creation - backdoor potential"""
    data = request.get_json() or {}
    username = data.get('username')
    role = data.get('role', 'user')

    user_id = f'USR-{uuid.uuid4().hex[:8]}'

    return jsonify({
        'status': 'created',
        'user_id': user_id,
        'username': username,
        'role': role,
        'password': f'TempPass{random.randint(1000, 9999)}!',
        'warning': 'User created without proper authorization'
    })


@admin_bp.route('/api/transactions/export')
def transactions_export():
    """Export transaction data - data exfiltration vector"""
    date_from = request.args.get('from', '2025-01-01')
    date_to = request.args.get('to', datetime.now().isoformat()[:10])
    export_format = request.args.get('format', 'json')

    transactions = [
        {
            'transaction_id': f'TXN-{uuid.uuid4().hex[:8]}',
            'date': (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
            'amount': random.randint(10, 10000),
            'customer_id': f'CUST-{random.randint(100000, 999999)}',
            'payment_method': f'****{random.randint(1000, 9999)}',
            'status': random.choice(['completed', 'pending', 'failed'])
        }
        for _ in range(100)
    ]

    return jsonify({
        'date_range': {'from': date_from, 'to': date_to},
        'format': export_format,
        'transactions': transactions,
        'total_count': len(transactions),
        'total_amount': sum(t['amount'] for t in transactions)
    })
