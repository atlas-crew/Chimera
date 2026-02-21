"""
Routes for banking endpoints with intentional vulnerabilities for WAF testing.
"""

from flask import request, jsonify, session
from datetime import datetime, timedelta
import uuid
import random
import time
from decimal import Decimal, ROUND_DOWN
import threading

from . import banking_bp
from app.models import *

# In-memory transfer lock (vulnerable to race conditions in distributed systems)
transfer_locks = {}
transfer_lock_mutex = threading.Lock()


@banking_bp.route('/banking/login')
def banking_portal():
    """Banking portal entry point"""
    return jsonify({
        'service': ' Banking Portal',
        'version': '2.1.0',
        'login_methods': ['username_password', 'mfa', 'biometric'],
        'status': 'active'
    })


# ============================================================================
# ACCOUNT MANAGEMENT ENDPOINTS
# ============================================================================

@banking_bp.route('/api/v1/banking/accounts', methods=['GET'])
def list_accounts():
    """
    List user accounts
    VULNERABILITY: IDOR - No proper authorization check on account ownership
    """
    user_id = request.args.get('user_id')

    # Weak authentication check
    if not user_id:
        user_id = session.get('user_id', 'user-demo')

    # IDOR Vulnerability: Returns accounts for ANY user_id provided
    user_accounts = [acc for acc in accounts_db.values() if acc.get('user_id') == user_id]

    if not user_accounts:
        # Initialize demo accounts if none exist
        demo_accounts = [
            {
                'account_id': f'ACC-{user_id}-001',
                'user_id': user_id,
                'account_type': 'checking',
                'balance': 15420.50,
                'currency': 'USD',
                'status': 'active',
                'created_at': (datetime.now() - timedelta(days=365)).isoformat()
            },
            {
                'account_id': f'ACC-{user_id}-002',
                'user_id': user_id,
                'account_type': 'savings',
                'balance': 52800.25,
                'currency': 'USD',
                'status': 'active',
                'created_at': (datetime.now() - timedelta(days=730)).isoformat()
            }
        ]

        for acc in demo_accounts:
            accounts_db[acc['account_id']] = acc

        user_accounts = demo_accounts

    return jsonify({
        'accounts': user_accounts,
        'total_balance': sum(acc['balance'] for acc in user_accounts),
        'count': len(user_accounts)
    })


@banking_bp.route('/api/v1/banking/accounts/<account_id>', methods=['GET'])
def get_account_details(account_id):
    """
    Get account details
    VULNERABILITY: IDOR - No ownership verification
    """
    # No authorization check - anyone can access any account
    account = accounts_db.get(account_id)

    if not account:
        return jsonify({'error': 'Account not found'}), 404

    # Expose sensitive details without verification
    return jsonify({
        'account_id': account['account_id'],
        'user_id': account['user_id'],  # Exposes user ID
        'account_type': account['account_type'],
        'balance': account['balance'],
        'currency': account['currency'],
        'status': account['status'],
        'account_number': f"****{random.randint(1000, 9999)}",  # Partial exposure
        'routing_number': '021000021',  # Exposes routing number
        'created_at': account['created_at'],
        'last_transaction': datetime.now().isoformat(),
        'overdraft_limit': 500.00,
        'interest_rate': 0.05
    })


@banking_bp.route('/api/v1/banking/accounts/create', methods=['POST'])
def create_account():
    """
    Create new account
    VULNERABILITY: Missing rate limiting - account enumeration possible
    """
    data = request.get_json() or {}
    user_id = data.get('user_id', session.get('user_id', 'user-demo'))
    account_type = data.get('account_type', 'checking')
    initial_deposit = float(data.get('initial_deposit', 0))

    # Weak validation
    if initial_deposit < 0:
        return jsonify({'error': 'Invalid deposit amount'}), 400

    account_id = f"ACC-{user_id}-{random.randint(100, 999)}"

    new_account = {
        'account_id': account_id,
        'user_id': user_id,
        'account_type': account_type,
        'balance': initial_deposit,
        'currency': 'USD',
        'status': 'active',
        'created_at': datetime.now().isoformat()
    }

    accounts_db[account_id] = new_account

    return jsonify({
        'message': 'Account created successfully',
        'account': new_account
    }), 201


@banking_bp.route('/api/v1/banking/balance', methods=['GET'])
def check_balance():
    """
    Check account balance
    VULNERABILITY: Parameter pollution on account_id
    """
    # Vulnerable to parameter pollution
    account_ids = request.args.getlist('account_id')

    if not account_ids:
        return jsonify({'error': 'account_id required'}), 400

    # Takes the first account_id, but parameter pollution could bypass logging
    account_id = account_ids[0]

    account = accounts_db.get(account_id)

    if not account:
        return jsonify({'error': 'Account not found'}), 404

    return jsonify({
        'account_id': account_id,
        'balance': account['balance'],
        'available_balance': account['balance'] - 100,  # Reserve
        'currency': account['currency'],
        'timestamp': datetime.now().isoformat()
    })


# ============================================================================
# TRANSACTION ENDPOINTS
# ============================================================================

@banking_bp.route('/api/v1/banking/transfer', methods=['POST'])
def transfer_funds():
    """
    Transfer funds between accounts
    VULNERABILITY: Race condition - no proper locking mechanism
    VULNERABILITY: Decimal precision errors with float arithmetic
    """
    data = request.get_json() or {}
    from_account = data.get('from_account')
    to_account = data.get('to_account')

    # VULNERABILITY: Using float instead of Decimal for money
    amount = float(data.get('amount', 0))

    if not from_account or not to_account:
        return jsonify({'error': 'Missing account information'}), 400

    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    # VULNERABILITY: Race condition window
    # Simulate checking balance
    source = accounts_db.get(from_account)
    dest = accounts_db.get(to_account)

    if not source or not dest:
        return jsonify({'error': 'Invalid accounts'}), 404

    # Race condition: Check and update are not atomic
    time.sleep(0.001)  # Simulate processing delay - widens race window

    if source['balance'] < amount:
        return jsonify({'error': 'Insufficient funds'}), 400

    # VULNERABILITY: Float precision errors
    # Multiple concurrent transfers could exploit this
    source['balance'] -= amount  # Not atomic
    time.sleep(0.001)  # Race condition window
    dest['balance'] += amount  # Not atomic

    # Record transaction
    transaction_id = str(uuid.uuid4())
    transaction = {
        'transaction_id': transaction_id,
        'type': 'transfer',
        'from_account': from_account,
        'to_account': to_account,
        'amount': amount,
        'status': 'completed',
        'timestamp': datetime.now().isoformat()
    }

    transactions_db[transaction_id] = transaction

    return jsonify({
        'message': 'Transfer successful',
        'transaction': transaction,
        'new_balance': source['balance']
    })


@banking_bp.route('/api/v1/banking/transactions', methods=['GET'])
def transaction_history():
    """
    Get transaction history
    VULNERABILITY: IDOR - can view any account's transactions
    """
    account_id = request.args.get('account_id')
    limit = int(request.args.get('limit', 50))

    if not account_id:
        return jsonify({'error': 'account_id required'}), 400

    # No authorization - can access any account's transactions
    account_transactions = [
        txn for txn in transactions_db.values()
        if txn.get('from_account') == account_id or txn.get('to_account') == account_id
    ]

    # Generate demo transactions if none exist
    if not account_transactions:
        for i in range(10):
            txn_id = str(uuid.uuid4())
            transaction = {
                'transaction_id': txn_id,
                'type': random.choice(['transfer', 'deposit', 'withdrawal', 'payment']),
                'account_id': account_id,
                'amount': round(random.uniform(10, 1000), 2),
                'description': random.choice(['Salary', 'Rent', 'Groceries', 'Utilities']),
                'status': 'completed',
                'timestamp': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
            }
            transactions_db[txn_id] = transaction
            account_transactions.append(transaction)

    return jsonify({
        'account_id': account_id,
        'transactions': sorted(account_transactions, key=lambda x: x['timestamp'], reverse=True)[:limit],
        'total': len(account_transactions)
    })


@banking_bp.route('/api/v1/banking/transactions/<transaction_id>', methods=['GET'])
def transaction_details(transaction_id):
    """
    Get transaction details
    VULNERABILITY: Direct object reference without ownership check
    """
    transaction = transactions_db.get(transaction_id)

    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404

    # Exposes full transaction details without authorization
    return jsonify({
        'transaction': transaction,
        'metadata': {
            'ip_address': request.remote_addr,  # Exposes client info
            'user_agent': request.headers.get('User-Agent')
        }
    })


@banking_bp.route('/api/v1/banking/statements', methods=['GET'])
def download_statements():
    """
    Download account statements
    VULNERABILITY: Direct object reference - can download any account's statements
    """
    account_id = request.args.get('account_id')
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    format_type = request.args.get('format', 'json')

    if not account_id:
        return jsonify({'error': 'account_id required'}), 400

    # No authorization check - direct object reference vulnerability
    account = accounts_db.get(account_id)

    if not account:
        return jsonify({'error': 'Account not found'}), 404

    # Generate statement data
    statement = {
        'account_id': account_id,
        'statement_period': month,
        'opening_balance': account['balance'] - random.uniform(100, 1000),
        'closing_balance': account['balance'],
        'total_deposits': random.uniform(1000, 5000),
        'total_withdrawals': random.uniform(500, 2000),
        'transactions': [
            txn for txn in transactions_db.values()
            if txn.get('from_account') == account_id or txn.get('to_account') == account_id
        ][:20],
        'generated_at': datetime.now().isoformat(),
        'account_holder': {
            'user_id': account['user_id'],
            'account_number': f"****{random.randint(1000, 9999)}"
        }
    }

    if format_type == 'pdf':
        # Simulate PDF generation
        return jsonify({
            'format': 'pdf',
            'download_url': f'/api/v1/banking/statements/download/{account_id}/{month}.pdf',
            'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
        })

    return jsonify(statement)


# ============================================================================
# BENEFICIARIES & WIRE TRANSFERS
# ============================================================================

@banking_bp.route('/api/v1/banking/beneficiaries/<beneficiary_id>', methods=['GET'])
def beneficiary_details(beneficiary_id):
    """Beneficiary lookup - IDOR vulnerability"""
    beneficiary = banking_beneficiaries_db.get(beneficiary_id)
    if not beneficiary:
        beneficiary = {
            'beneficiary_id': beneficiary_id,
            'name': f'Recipient {random.randint(100, 999)}',
            'account_number': f'****{random.randint(1000, 9999)}',
            'bank': random.choice(['Example Bank', 'Metro Credit', 'Union Trust']),
            'created_at': datetime.now().isoformat()
        }
        banking_beneficiaries_db[beneficiary_id] = beneficiary

    return jsonify({
        'beneficiary': beneficiary,
        'warning': 'Beneficiary data exposed without authorization'
    })


@banking_bp.route('/api/v1/banking/wire-transfer', methods=['POST'])
def wire_transfer():
    """Wire transfer - AML and approval bypass"""
    data = request.get_json() or {}
    wire_id = f"WIRE-{uuid.uuid4().hex[:8]}"

    record = {
        'wire_id': wire_id,
        'amount': data.get('amount', 0),
        'beneficiary': data.get('beneficiary', 'unknown'),
        'swift_code': data.get('swift_code'),
        'bypass_aml': data.get('bypass_aml', False),
        'skip_screening': data.get('skip_screening', False),
        'status': 'submitted',
        'created_at': datetime.now().isoformat()
    }
    banking_wire_transfers_db[wire_id] = record

    return jsonify({
        'wire': record,
        'warning': 'Wire transfer submitted without AML screening'
    }), 201


@banking_bp.route('/api/v1/banking/kyc/documents/export', methods=['GET'])
def kyc_documents_export():
    """KYC document export - PII exposure"""
    include_pii = request.args.get('include_pii', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 1000))
    documents = list(banking_kyc_documents_db.values())[:limit]

    if include_pii:
        for doc in documents:
            doc.setdefault('ssn', f'{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}')

    return jsonify({
        'documents': documents,
        'include_pii': include_pii,
        'count': len(documents),
        'warning': 'KYC documents exported without authorization'
    })


# ============================================================================
# CARD MANAGEMENT ENDPOINTS
# ============================================================================

@banking_bp.route('/api/v1/banking/cards', methods=['GET'])
def list_cards():
    """
    List user cards
    VULNERABILITY: Exposes partial card numbers without proper masking
    """
    user_id = request.args.get('user_id', session.get('user_id', 'user-demo'))

    # Generate demo cards
    cards = [
        {
            'card_id': f'CARD-{user_id}-001',
            'card_number': f'4532-****-****-{random.randint(1000, 9999)}',  # Partial exposure
            'card_type': 'debit',
            'network': 'VISA',
            'status': 'active',
            'expiry': '12/26',
            'cvv_hash': 'redacted',  # Should never be returned
            'daily_limit': 5000.00,
            'linked_account': f'ACC-{user_id}-001'
        },
        {
            'card_id': f'CARD-{user_id}-002',
            'card_number': f'5500-****-****-{random.randint(1000, 9999)}',
            'card_type': 'credit',
            'network': 'MASTERCARD',
            'status': 'active',
            'expiry': '06/27',
            'cvv_hash': 'redacted',
            'credit_limit': 10000.00,
            'available_credit': 8750.00
        }
    ]

    return jsonify({
        'cards': cards,
        'total': len(cards)
    })


@banking_bp.route('/api/v1/banking/cards/activate', methods=['POST'])
def activate_card():
    """
    Activate a card
    VULNERABILITY: Missing rate limiting - card enumeration
    """
    data = request.get_json() or {}
    card_id = data.get('card_id')
    activation_code = data.get('activation_code')

    if not card_id or not activation_code:
        return jsonify({'error': 'Missing required fields'}), 400

    # Weak validation - accepts any 6-digit code
    if len(activation_code) != 6 or not activation_code.isdigit():
        return jsonify({'error': 'Invalid activation code format'}), 400

    # No rate limiting - allows brute force
    # Simulate activation
    return jsonify({
        'message': 'Card activated successfully',
        'card_id': card_id,
        'status': 'active',
        'activated_at': datetime.now().isoformat()
    })


@banking_bp.route('/api/v1/banking/cards/block', methods=['POST'])
def block_card():
    """
    Block a card
    VULNERABILITY: IDOR - can block any card
    """
    data = request.get_json() or {}
    card_id = data.get('card_id')
    reason = data.get('reason', 'user_request')

    if not card_id:
        return jsonify({'error': 'card_id required'}), 400

    # No ownership verification - can block anyone's card
    return jsonify({
        'message': 'Card blocked successfully',
        'card_id': card_id,
        'status': 'blocked',
        'reason': reason,
        'blocked_at': datetime.now().isoformat(),
        'can_unblock': True  # Information disclosure
    })


# ============================================================================
# VULNERABLE HELPER ENDPOINTS (FOR WAF TESTING)
# ============================================================================

@banking_bp.route('/api/v1/banking/internal/reset-balance', methods=['POST'])
def reset_balance():
    """
    Internal endpoint for resetting account balance
    VULNERABILITY: Should be internal-only but exposed publicly
    """
    data = request.get_json() or {}
    account_id = data.get('account_id')
    new_balance = float(data.get('new_balance', 0))

    if account_id in accounts_db:
        accounts_db[account_id]['balance'] = new_balance
        return jsonify({
            'message': 'Balance reset successfully',
            'account_id': account_id,
            'new_balance': new_balance
        })

    return jsonify({'error': 'Account not found'}), 404


@banking_bp.route('/api/v1/banking/accounts/enumerate')
def enumerate_accounts():
    """
    Account enumeration endpoint
    VULNERABILITY: Allows discovering valid account IDs
    """
    prefix = request.args.get('prefix', 'ACC')

    # Returns all accounts matching prefix
    matching_accounts = [
        {
            'account_id': acc_id,
            'exists': True,
            'account_type': acc.get('account_type')
        }
        for acc_id, acc in accounts_db.items()
        if acc_id.startswith(prefix)
    ]

    return jsonify({
        'prefix': prefix,
        'matches': matching_accounts,
        'count': len(matching_accounts)
    })


@banking_bp.route('/api/v1/banking/transfer/bulk', methods=['POST'])
def bulk_transfer():
    """
    Bulk transfer endpoint
    VULNERABILITY: No per-transfer validation, amplifies race conditions
    """
    data = request.get_json() or {}
    transfers = data.get('transfers', [])

    results = []

    for transfer in transfers:
        from_account = transfer.get('from_account')
        to_account = transfer.get('to_account')
        amount = float(transfer.get('amount', 0))

        # No validation or atomicity between transfers
        if from_account in accounts_db and to_account in accounts_db:
            accounts_db[from_account]['balance'] -= amount
            accounts_db[to_account]['balance'] += amount

            results.append({
                'from': from_account,
                'to': to_account,
                'amount': amount,
                'status': 'success'
            })
        else:
            results.append({
                'from': from_account,
                'to': to_account,
                'amount': amount,
                'status': 'failed'
            })

    return jsonify({
        'total_transfers': len(transfers),
        'successful': len([r for r in results if r['status'] == 'success']),
        'failed': len([r for r in results if r['status'] == 'failed']),
        'results': results
    })


# ============================================================================
# ACCOUNT RECOVERY & DEVICE TRUST
# ============================================================================

@banking_bp.route('/api/v1/banking/account-recovery', methods=['POST'])
def account_recovery():
    """Account recovery - IDOR and bypass risks"""
    data = request.get_json() or {}
    account_id = data.get('account_id')
    request_id = f"REC-{uuid.uuid4().hex[:8]}"

    recovery = {
        'request_id': request_id,
        'account_id': account_id,
        'send_link': data.get('send_link', True),
        'bypass_mfa': data.get('bypass_mfa', False),
        'created_at': datetime.now().isoformat()
    }
    banking_recovery_requests_db[request_id] = recovery

    return jsonify({
        'recovery': recovery,
        'warning': 'Account recovery initiated without ownership verification'
    }), 201


@banking_bp.route('/api/v1/banking/device/verify', methods=['POST'])
def device_verify():
    """Device trust verification - bypass vulnerability"""
    data = request.get_json() or {}
    device_id = data.get('device_id')
    record = {
        'device_id': device_id,
        'trusted': True,
        'override_trust': data.get('override_trust', False),
        'verified_at': datetime.now().isoformat()
    }
    banking_device_trust_db[device_id] = record

    return jsonify({
        'device': record,
        'warning': 'Device marked trusted without validation'
    })


@banking_bp.route('/api/v1/banking/session/terminate', methods=['POST'])
def session_terminate():
    """Terminate session - forced logout abuse"""
    data = request.get_json() or {}
    session_id = data.get('session_id', f"SESS-{uuid.uuid4().hex[:6]}")

    banking_sessions_db[session_id] = {
        'session_id': session_id,
        'terminated': True,
        'force_logout': data.get('force_logout', False),
        'terminated_at': datetime.now().isoformat()
    }

    return jsonify({
        'session_id': session_id,
        'terminated': True,
        'warning': 'Session terminated without authorization'
    })


# ============================================================================
# LOANS & CREDIT
# ============================================================================

@banking_bp.route('/api/v1/banking/loans/apply', methods=['POST'])
def loan_apply():
    """Loan application - injection and bypass risks"""
    data = request.get_json() or {}
    loan_id = f"LOAN-{uuid.uuid4().hex[:8]}"

    application = {
        'loan_id': loan_id,
        'applicant_id': data.get('applicant_id'),
        'amount': data.get('amount', 0),
        'income': data.get('income'),
        'submitted_at': datetime.now().isoformat(),
        'status': 'submitted'
    }
    banking_loan_applications_db[loan_id] = application

    return jsonify({
        'application': application,
        'warning': 'Loan application accepted without validation'
    }), 201


@banking_bp.route('/api/v1/banking/credit/limit', methods=['PUT'])
def credit_limit_update():
    """Credit limit override - authorization bypass"""
    data = request.get_json() or {}
    account_id = data.get('account_id')
    limit = data.get('credit_limit', 0)

    banking_credit_limits_db[account_id] = {
        'account_id': account_id,
        'credit_limit': limit,
        'bypass_controls': data.get('bypass_controls', False),
        'updated_at': datetime.now().isoformat()
    }

    return jsonify({
        'account_id': account_id,
        'credit_limit': limit,
        'warning': 'Credit limit updated without approval'
    })


@banking_bp.route('/api/v1/banking/loans/underwrite', methods=['POST'])
def loan_underwrite():
    """Underwriting override - risk bypass"""
    data = request.get_json() or {}
    loan_id = data.get('loan_id')
    record = banking_loan_applications_db.get(loan_id, {'loan_id': loan_id})
    record['override_risk'] = data.get('override_risk', False)
    record['status'] = 'approved'
    record['approved_at'] = datetime.now().isoformat()
    banking_loan_applications_db[loan_id] = record

    return jsonify({
        'loan': record,
        'warning': 'Loan approved without underwriting validation'
    })


# ============================================================================
# OPEN BANKING & CONSENT
# ============================================================================

@banking_bp.route('/api/v1/banking/consents', methods=['POST'])
def create_consent():
    """Create open banking consent - scope escalation"""
    data = request.get_json() or {}
    consent_id = f"CONS-{uuid.uuid4().hex[:8]}"
    consent = {
        'consent_id': consent_id,
        'customer_id': data.get('customer_id'),
        'scopes': data.get('scopes', []),
        'force_approval': data.get('force_approval', False),
        'status': 'approved',
        'approved_at': datetime.now().isoformat()
    }
    banking_consents_db[consent_id] = consent

    return jsonify({
        'consent': consent,
        'warning': 'Consent approved without customer confirmation'
    }), 201


@banking_bp.route('/api/v1/banking/consents/revoke', methods=['POST'])
def revoke_consent():
    """Revoke consent - audit bypass"""
    data = request.get_json() or {}
    consent_id = data.get('consent_id')
    consent = banking_consents_db.get(consent_id, {'consent_id': consent_id})
    consent['status'] = 'revoked'
    consent['skip_audit'] = data.get('skip_audit', False)
    consent['revoked_at'] = datetime.now().isoformat()
    banking_consents_db[consent_id] = consent

    return jsonify({
        'consent': consent,
        'warning': 'Consent revoked without audit trail'
    })


@banking_bp.route('/api/v1/banking/open-banking/token', methods=['POST'])
def open_banking_token():
    """Token exchange - replay risk"""
    data = request.get_json() or {}
    token_id = f"OB-{uuid.uuid4().hex[:8]}"

    token = {
        'token_id': token_id,
        'client_id': data.get('client_id'),
        'grant_type': data.get('grant_type'),
        'code': data.get('code'),
        'issued_at': datetime.now().isoformat(),
        'replay_detected': False
    }
    open_banking_tokens_db[token_id] = token

    return jsonify({
        'token': token,
        'warning': 'Authorization code reuse not detected'
    }), 201


# ============================================================================
# NEW FEATURES: REMOTE DEPOSIT & WIRES
# ============================================================================

@banking_bp.route('/api/v1/banking/checks/deposit', methods=['POST'])
def deposit_check():
    """
    Remote Check Deposit (RDC)
    VULNERABILITY: XXE (XML External Entity) via check metadata
    VULNERABILITY: RCE via ImageMagick simulation
    """
    # Check for file upload or JSON metadata
    if 'metadata' in request.files:
        # Simulate processing XML metadata for the check image
        content = request.files['metadata'].read().decode('utf-8')
        
        # VULNERABILITY: XXE Simulation
        # If the XML contains DOCTYPE ENTITY system, it's an attack
        if '<!ENTITY' in content and 'SYSTEM' in content:
            # Simulate reading /etc/passwd via XXE
            if '/etc/passwd' in content:
                return jsonify({
                    'status': 'error',
                    'error': 'XXE_PROCESSING_ERROR',
                    'internal_error': "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon...",
                    'message': 'Failed to parse check metadata'
                }), 500
            
            # Simulate internal network scan via XXE
            if 'http://' in content:
                return jsonify({
                    'status': 'error', 
                    'error': 'XXE_SSRF_ERROR',
                    'message': f"Failed to reach external entity: {content[content.find('http'):content.find('\"', content.find('http'))]}"
                }), 500

    data = request.form or request.get_json() or {}
    amount = float(data.get('amount', 0))
    
    return jsonify({
        'status': 'pending',
        'deposit_id': f"RDC-{uuid.uuid4().hex[:8]}",
        'amount': amount,
        'clearing_date': (datetime.now() + timedelta(days=1)).isoformat()
    }), 202


@banking_bp.route('/api/v1/banking/wires/swift', methods=['POST'])
def swift_wire():
    """
    International SWIFT Wire Transfer
    VULNERABILITY: Logic Flaw (Negative currency conversion)
    VULNERABILITY: Integer Overflow
    """
    data = request.get_json() or {}
    amount = data.get('amount', 0)
    currency = data.get('currency', 'USD')
    target_currency = data.get('target_currency', 'EUR')
    
    # VULNERABILITY: Logic flaw - Negative exchange rates
    # If user provides a custom rate, we accept it blindly
    exchange_rate = float(data.get('exchange_rate', 0.85))
    
    # Calculate converted amount
    # If exchange_rate is negative (e.g. -1.0), the sender GAINS money
    converted_amount = float(amount) * exchange_rate
    
    return jsonify({
        'status': 'processing',
        'wire_id': f"SWIFT-{uuid.uuid4().hex[:12].upper()}",
        'source_amount': amount,
        'source_currency': currency,
        'target_amount': converted_amount,
        'target_currency': target_currency,
        'exchange_rate': exchange_rate,
        'warning': 'Custom exchange rate accepted without validation'
    })
