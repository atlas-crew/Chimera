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
import hashlib

from . import banking_bp
from app.models import *
from app.utils.hotpatch import hotpatch


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
@hotpatch('bola')
def list_accounts(is_secure=False):
    """
    List user accounts
    VULNERABILITY (when insecure): BOLA/IDOR — no ownership check. 
    Toggled by @hotpatch('bola') based on security_config.
    """
    user_id = request.args.get('user_id')

    # Weak authentication check
    if not user_id:
        user_id = session.get('user_id', 'user-demo')

    if is_secure:
        # SECURE: Only return accounts belonging to the authenticated session user
        authenticated_user = session.get('user_id', 'user-demo')
        user_accounts = [acc for acc in accounts_db.values() if acc.get('user_id') == authenticated_user]
        demo_user = authenticated_user
    else:
        # VULNERABLE: Returns accounts for ANY user_id provided (IDOR)
        user_accounts = [acc for acc in accounts_db.values() if acc.get('user_id') == user_id]
        demo_user = user_id

    if not user_accounts:
        # Initialize demo accounts if none exist
        demo_accounts = [
            {
                'account_id': f'ACC-{demo_user}-001',
                'user_id': demo_user,
                'account_type': 'checking',
                'balance': 15420.50,
                'currency': 'USD',
                'status': 'active',
                'created_at': (datetime.now() - timedelta(days=365)).isoformat()
            },
            {
                'account_id': f'ACC-{demo_user}-002',
                'user_id': demo_user,
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

    response = {
        'accounts': user_accounts,
        'total_balance': sum(acc['balance'] for acc in user_accounts),
        'count': len(user_accounts)
    }

    if not is_secure and user_id and user_id != session.get('user_id', 'user-demo'):
        response['vulnerability'] = 'BOLA_IDOR_DETECTED'
        response['vulnerability_type'] = 'BOLA'

    return jsonify(response)


@banking_bp.route('/api/v1/banking/accounts/<account_id>', methods=['GET'])
@hotpatch('bola')
def get_account_details(account_id, is_secure=False):
    """
    Get account details
    VULNERABILITY (when insecure): BOLA/IDOR — no ownership check.
    Toggled by @hotpatch('bola') based on security_config.
    """
    account = accounts_db.get(account_id)

    if not account:
        return jsonify({'error': 'Account not found'}), 404

    is_owner = account['user_id'] == session.get('user_id', 'user-demo')
    
    if is_secure:
        # SECURE: Check if account belongs to the logged-in user
        if not is_owner:
            return jsonify({
                'error': 'Unauthorized', 
                'vulnerability': 'BOLA_IDOR_BLOCKED',
                'vulnerability_type': 'BOLA'
            }), 403

    # Generate a stable masked account number for realism
    acc_hash = int(hashlib.md5(account['account_id'].encode()).hexdigest(), 16)
    masked_suffix = str(acc_hash % 9000 + 1000)

    # Expose sensitive details
    response = {
        'account_id': account['account_id'],
        'user_id': account['user_id'],
        'account_type': account['account_type'],
        'balance': account['balance'],
        'currency': account['currency'],
        'status': account['status'],
        'account_number': f"****{masked_suffix}",
        'routing_number': '021000021',
        'created_at': account['created_at'],
        'last_transaction': datetime.now().isoformat(),
        'overdraft_limit': 500.00,
        'interest_rate': 0.05
    }

    # Add vulnerability metadata if insecure and accessing someone else's account
    if not is_secure and not is_owner:
        response['vulnerability'] = 'BOLA_IDOR_DETECTED'
        response['vulnerability_type'] = 'BOLA'

    return jsonify(response)
