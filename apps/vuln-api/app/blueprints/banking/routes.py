"""
Routes for banking endpoints with intentional vulnerabilities for WAF testing.
"""
from starlette.requests import Request
from starlette.responses import JSONResponse
from datetime import datetime, timedelta
import uuid
import random
import time
from decimal import Decimal, ROUND_DOWN
import threading
import hashlib

from . import banking_router
from app.models import *
from app.routing import safe_json
from app.utils.hotpatch import hotpatch


# In-memory transfer lock (vulnerable to race conditions in distributed systems)
transfer_locks = {}
transfer_lock_mutex = threading.Lock()


@banking_router.route('/banking/login')
async def banking_portal(request: Request):
    """Banking portal entry point"""
    return JSONResponse({
        'service': ' Banking Portal',
        'version': '2.1.0',
        'login_methods': ['username_password', 'mfa', 'biometric'],
        'status': 'active'
    })


# ============================================================================
# ACCOUNT MANAGEMENT ENDPOINTS
# ============================================================================

@banking_router.route('/api/v1/banking/accounts', methods=['GET'])
@hotpatch('bola')
async def list_accounts(request: Request, is_secure=False):
    """
    List user accounts
    VULNERABILITY (when insecure): BOLA/IDOR — no ownership check. 
    Toggled by @hotpatch('bola') based on security_config.
    """
    user_id = request.query_params.get('user_id')

    # Weak authentication check
    if not user_id:
        user_id = request.session.get('user_id', 'user-demo')

    if is_secure:
        # SECURE: Only return accounts belonging to the authenticated session user
        authenticated_user = request.session.get('user_id', 'user-demo')
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

    if not is_secure and user_id and user_id != request.session.get('user_id', 'user-demo'):
        response['vulnerability'] = 'BOLA_IDOR_DETECTED'
        response['vulnerability_type'] = 'BOLA'

    return JSONResponse(response)


@banking_router.route('/api/v1/banking/accounts/<account_id>', methods=['GET'])
@hotpatch('bola')
async def get_account_details(request: Request, account_id, is_secure=False):
    """
    Get account details
    VULNERABILITY (when insecure): BOLA/IDOR — no ownership check.
    Toggled by @hotpatch('bola') based on security_config.
    """
    account = accounts_db.get(account_id)

    if not account:
        return JSONResponse({'error': 'Account not found'}, status_code = 404)

    is_owner = account['user_id'] == request.session.get('user_id', 'user-demo')
    
    if is_secure:
        # SECURE: Check if account belongs to the logged-in user
        if not is_owner:
            return JSONResponse({
                'error': 'Unauthorized', 
                'vulnerability': 'BOLA_IDOR_BLOCKED',
                'vulnerability_type': 'BOLA'
            }, status_code = 403)

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

    return JSONResponse(response)


# ============================================================================
# WIRE TRANSFER ENDPOINT
# ============================================================================

@banking_router.route('/api/v1/banking/wire-transfer', methods=['POST'])
async def create_wire_transfer(request: Request):
    """
    Process wire transfer without AML checks.
    VULNERABILITY: Accepts bypass_aml flag without authorization.
    """
    data = await safe_json(request)
    wire = {
        'wire_id': f'WIRE-{uuid.uuid4().hex[:8].upper()}',
        'amount': data.get('amount', 0),
        'beneficiary': data.get('beneficiary', 'Unknown'),
        'bypass_aml': data.get('bypass_aml', False),
        'status': 'completed',
        'timestamp': datetime.now().isoformat(),
    }
    return JSONResponse({'wire': wire}, status_code = 201)


# ============================================================================
# BENEFICIARY ENDPOINT
# ============================================================================

@banking_router.route('/api/v1/banking/beneficiaries/<beneficiary_id>', methods=['GET'])
async def get_beneficiary(request: Request, beneficiary_id):
    """
    Get beneficiary details without ownership verification.
    VULNERABILITY: IDOR — any user can access any beneficiary record.
    """
    beneficiary = {
        'beneficiary_id': beneficiary_id,
        'name': 'Jane Doe',
        'account_number': '****7890',
        'bank': 'Example Bank',
        'user_id': 'user-victim',
    }
    return JSONResponse({'beneficiary': beneficiary})


# ============================================================================
# KYC DOCUMENTS EXPORT ENDPOINT
# ============================================================================

@banking_router.route('/api/v1/banking/kyc/documents/export', methods=['GET'])
async def export_kyc_documents(request: Request):
    """
    Export KYC documents without admin verification.
    VULNERABILITY: Broken access control — no role check, PII exposed.
    """
    include_pii = request.query_params.get('include_pii', 'false').lower() == 'true'
    documents = [
        {'doc_id': 'KYC-001', 'user_id': 'user-001', 'type': 'passport', 'status': 'verified'},
        {'doc_id': 'KYC-002', 'user_id': 'user-002', 'type': 'drivers_license', 'status': 'pending'},
    ]
    return JSONResponse({'documents': documents, 'include_pii': include_pii})
