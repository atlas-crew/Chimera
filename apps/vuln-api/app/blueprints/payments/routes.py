"""
Routes for payments endpoints with intentional vulnerabilities for WAF testing.
"""

from flask import request, jsonify, session
from datetime import datetime, timedelta
import uuid
import random
import time
from decimal import Decimal, ROUND_HALF_UP

from . import payments_bp
from app.models import *

# Initialize demo data stores if needed
if not currency_rates_db:
    currency_rates_db.update({
        'USD': 1.0,
        'EUR': 0.92,
        'GBP': 0.79,
        'JPY': 149.50,
        'CAD': 1.36
    })


# ============================================================================
# PAYMENT PROCESSING ENDPOINTS
# ============================================================================

@payments_bp.route('/api/v1/payments/process', methods=['POST'])
def payment_process():
    """
    Process payment
    VULNERABILITY: Missing rate limiting - allows payment testing attacks
    VULNERABILITY: Decimal precision errors with float arithmetic
    """
    data = request.get_json() or {}

    # Extract payment details
    payment_method_id = data.get('payment_method_id')
    amount = float(data.get('amount', 0))  # VULNERABILITY: float for money
    currency = data.get('currency', 'USD')
    merchant_id = data.get('merchant_id', 'MERCHANT-DEMO')

    # Weak validation
    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    # VULNERABILITY: No rate limiting - allows card testing
    # Simulate processing delay
    time.sleep(0.1)

    # Random success/failure for testing
    success_rate = 0.95

    if random.random() < success_rate:
        transaction_id = str(uuid.uuid4())

        # VULNERABILITY: Decimal precision with float
        processing_fee = amount * 0.029  # 2.9% fee
        net_amount = amount - processing_fee

        transaction = {
            'transaction_id': transaction_id,
            'payment_method_id': payment_method_id,
            'amount': amount,
            'processing_fee': processing_fee,
            'net_amount': net_amount,
            'currency': currency,
            'merchant_id': merchant_id,
            'status': 'completed',
            'processed_at': datetime.now().isoformat()
        }

        # Store in payment methods DB
        if 'transactions' not in payment_methods_db:
            payment_methods_db['transactions'] = []
        payment_methods_db['transactions'].append(transaction)

        return jsonify({
            'success': True,
            'transaction': transaction
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Payment declined',
            'decline_code': random.choice(['insufficient_funds', 'card_declined', 'fraud_suspected'])
        }), 402


@payments_bp.route('/api/v1/payments/authorize', methods=['POST'])
def payments_authorize():
    """
    Authorize payment without capturing
    VULNERABILITY: Authorization can be held indefinitely
    """
    data = request.get_json() or {}

    card_number = data.get('card_number', '')
    amount = float(data.get('amount', 0))
    merchant_id = data.get('merchant_id', 'MERCHANT-DEMO')

    if amount <= 0:
        return jsonify({'error': 'Invalid amount'}), 400

    # VULNERABILITY: No expiration on authorization
    auth_code = f"AUTH-{uuid.uuid4().hex[:12].upper()}"

    authorization = {
        'authorization_code': auth_code,
        'card_number': f"****-****-****-{card_number[-4:] if len(card_number) >= 4 else '0000'}",
        'amount': amount,
        'merchant_id': merchant_id,
        'status': 'authorized',
        'authorized_at': datetime.now().isoformat(),
        'expires_at': None  # VULNERABILITY: No expiration
    }

    # Store authorization
    if 'authorizations' not in payment_methods_db:
        payment_methods_db['authorizations'] = {}
    payment_methods_db['authorizations'][auth_code] = authorization

    return jsonify({
        'success': True,
        'authorization': authorization
    })


@payments_bp.route('/api/v1/payments/capture', methods=['POST'])
def payments_capture():
    """
    Capture authorized payment
    VULNERABILITY: Amount can differ from authorization (partial capture abuse)
    """
    data = request.get_json() or {}

    auth_code = data.get('authorization_code', '')
    capture_amount = float(data.get('amount', 0))

    if not auth_code:
        return jsonify({'error': 'Authorization code required'}), 400

    authorizations = payment_methods_db.get('authorizations', {})
    authorization = authorizations.get(auth_code)

    if not authorization:
        return jsonify({'error': 'Authorization not found'}), 404

    if authorization['status'] != 'authorized':
        return jsonify({'error': 'Authorization already captured or voided'}), 400

    # VULNERABILITY: No validation that capture amount <= authorized amount
    # Allows capturing more than authorized

    transaction_id = str(uuid.uuid4())

    capture = {
        'transaction_id': transaction_id,
        'authorization_code': auth_code,
        'authorized_amount': authorization['amount'],
        'captured_amount': capture_amount,
        'overage': capture_amount - authorization['amount'],  # Can be positive!
        'status': 'captured',
        'captured_at': datetime.now().isoformat()
    }

    # Update authorization status
    authorization['status'] = 'captured'
    authorization['capture_info'] = capture

    return jsonify({
        'success': True,
        'capture': capture
    })


@payments_bp.route('/api/v1/payments/refund', methods=['POST'])
def payments_refund():
    """
    Process refund
    VULNERABILITY: Can refund more than original transaction
    """
    data = request.get_json() or {}

    transaction_id = data.get('transaction_id', '')
    refund_amount = float(data.get('amount', 0))
    reason = data.get('reason', 'customer_request')

    if not transaction_id:
        return jsonify({'error': 'Transaction ID required'}), 400

    # VULNERABILITY: No validation that refund <= original amount
    refund_id = str(uuid.uuid4())

    refund = {
        'refund_id': refund_id,
        'transaction_id': transaction_id,
        'amount': refund_amount,
        'reason': reason,
        'status': 'completed',
        'processed_at': datetime.now().isoformat()
    }

    # Store refund
    if 'refunds' not in payment_methods_db:
        payment_methods_db['refunds'] = []
    payment_methods_db['refunds'].append(refund)

    return jsonify({
        'success': True,
        'refund': refund
    })


# ============================================================================
# PAYMENT METHODS ENDPOINTS
# ============================================================================

@payments_bp.route('/api/v1/payments/methods', methods=['GET'])
def list_payment_methods():
    """
    List payment methods for a customer
    VULNERABILITY: IDOR - can access any customer's payment methods
    """
    customer_id = request.args.get('customer_id')

    if not customer_id:
        customer_id = session.get('customer_id', 'CUST-DEMO')

    # IDOR: No verification that current user owns this customer_id
    methods = customer_payment_methods_db.get(customer_id, [])

    if not methods:
        # Generate demo payment methods
        methods = [
            {
                'method_id': f'PM-{customer_id}-001',
                'type': 'card',
                'card_brand': 'VISA',
                'last_four': '4242',
                'expiry': '12/26',
                'is_default': True,
                'billing_address': {
                    'zip': '94105'  # Partial PII exposure
                }
            },
            {
                'method_id': f'PM-{customer_id}-002',
                'type': 'card',
                'card_brand': 'MASTERCARD',
                'last_four': '5555',
                'expiry': '06/27',
                'is_default': False
            }
        ]
        customer_payment_methods_db[customer_id] = methods

    return jsonify({
        'customer_id': customer_id,
        'payment_methods': methods,
        'count': len(methods)
    })


@payments_bp.route('/api/v1/payments/methods/add', methods=['POST'])
def payment_methods_add():
    """
    Add payment method
    VULNERABILITY: Stores card details insecurely
    """
    data = request.get_json() or {}

    customer_id = data.get('customer_id', session.get('customer_id', 'CUST-DEMO'))
    card_number = data.get('card_number', '')
    expiry = data.get('expiry', '')
    cvv = data.get('cvv', '')

    # Weak validation
    if len(card_number.replace(' ', '').replace('-', '')) != 16:
        return jsonify({'error': 'Invalid card number'}), 400

    method_id = f"PM-{customer_id}-{random.randint(100, 999)}"

    # VULNERABILITY: Storing too much card data
    new_method = {
        'method_id': method_id,
        'customer_id': customer_id,
        'type': 'card',
        'card_number': card_number[-4:],  # Should only store last 4
        'full_card_hash': hash(card_number),  # VULNERABILITY: Storing hash of full number
        'expiry': expiry,
        'cvv_provided': True,  # Should never store CVV
        'added_at': datetime.now().isoformat()
    }

    if customer_id not in customer_payment_methods_db:
        customer_payment_methods_db[customer_id] = []

    customer_payment_methods_db[customer_id].append(new_method)

    return jsonify({
        'success': True,
        'method': new_method
    }), 201


@payments_bp.route('/api/v1/payments/methods/remove', methods=['POST'])
def payment_methods_remove():
    """
    Remove payment method
    VULNERABILITY: Can remove any customer's payment method
    """
    data = request.get_json() or {}

    method_id = data.get('method_id')
    customer_id = data.get('customer_id')

    if not method_id:
        return jsonify({'error': 'method_id required'}), 400

    # IDOR: No ownership verification
    if customer_id in customer_payment_methods_db:
        methods = customer_payment_methods_db[customer_id]
        customer_payment_methods_db[customer_id] = [
            m for m in methods if m.get('method_id') != method_id
        ]

    return jsonify({
        'success': True,
        'message': 'Payment method removed'
    })


# ============================================================================
# MERCHANT SERVICES ENDPOINTS
# ============================================================================

@payments_bp.route('/api/v1/payments/merchant/onboard', methods=['POST'])
def merchant_onboard():
    """
    Merchant onboarding
    VULNERABILITY: Insufficient KYC validation
    """
    data = request.get_json() or {}

    business_name = data.get('business_name', '')
    tax_id = data.get('tax_id', '')
    annual_volume = float(data.get('annual_volume', 0))
    industry = data.get('industry', 'general')

    # Weak validation - no real KYC
    if not business_name:
        return jsonify({'error': 'Business name required'}), 400

    merchant_id = f"MERCH-{uuid.uuid4().hex[:8].upper()}"

    merchant = {
        'merchant_id': merchant_id,
        'business_name': business_name,
        'tax_id': tax_id,  # VULNERABILITY: Storing sensitive tax ID
        'annual_volume': annual_volume,
        'industry': industry,
        'status': 'active',  # VULNERABILITY: Auto-approved without verification
        'onboarded_at': datetime.now().isoformat(),
        'processing_rate': 0.029,  # 2.9%
        'settlement_schedule': 'daily'
    }

    if not merchant_applications_db:
        merchant_applications_db.update({merchant_id: merchant})
    else:
        merchant_applications_db[merchant_id] = merchant

    return jsonify({
        'success': True,
        'merchant': merchant
    }), 201


@payments_bp.route('/api/v1/payments/merchant/settlements', methods=['GET'])
def merchant_settlements():
    """
    View merchant settlements
    VULNERABILITY: IDOR - can view any merchant's settlements
    """
    merchant_id = request.args.get('merchant_id', 'MERCHANT-DEMO')

    # No ownership verification
    # Generate demo settlements
    settlements = []
    for i in range(5):
        settlement_date = datetime.now() - timedelta(days=i)
        settlements.append({
            'settlement_id': str(uuid.uuid4()),
            'merchant_id': merchant_id,
            'settlement_date': settlement_date.date().isoformat(),
            'gross_amount': round(random.uniform(1000, 10000), 2),
            'fees': round(random.uniform(50, 300), 2),
            'net_amount': round(random.uniform(950, 9700), 2),
            'transaction_count': random.randint(10, 100),
            'status': 'completed'
        })

    return jsonify({
        'merchant_id': merchant_id,
        'settlements': settlements,
        'total_settlements': len(settlements)
    })


@payments_bp.route('/api/v1/payments/merchant/disputes', methods=['GET'])
def merchant_disputes():
    """
    Handle merchant disputes
    VULNERABILITY: Exposes customer information in disputes
    """
    merchant_id = request.args.get('merchant_id', 'MERCHANT-DEMO')

    # Generate demo disputes
    disputes = [
        {
            'dispute_id': str(uuid.uuid4()),
            'transaction_id': str(uuid.uuid4()),
            'merchant_id': merchant_id,
            'customer_email': 'customer@example.com',  # VULNERABILITY: PII exposure
            'customer_name': 'John Doe',  # VULNERABILITY: PII exposure
            'amount': 149.99,
            'reason': 'product_not_received',
            'status': 'open',
            'created_at': (datetime.now() - timedelta(days=2)).isoformat()
        },
        {
            'dispute_id': str(uuid.uuid4()),
            'transaction_id': str(uuid.uuid4()),
            'merchant_id': merchant_id,
            'customer_email': 'jane@example.com',
            'customer_name': 'Jane Smith',
            'amount': 89.50,
            'reason': 'unauthorized',
            'status': 'under_review',
            'created_at': (datetime.now() - timedelta(days=5)).isoformat()
        }
    ]

    return jsonify({
        'merchant_id': merchant_id,
        'disputes': disputes,
        'total': len(disputes)
    })


# ============================================================================
# VULNERABLE TESTING ENDPOINTS
# ============================================================================

@payments_bp.route('/api/cards/validate', methods=['POST'])
def cards_validate():
    """
    Card validation endpoint
    VULNERABILITY: Allows unlimited card testing
    """
    data = request.get_json() or {}
    card_number = str(data.get('card_number', '')).replace(' ', '').replace('-', '')
    expiry = data.get('expiry', '')
    cvv = data.get('cvv', '')

    # Weak Luhn algorithm check
    def luhn_check(card_num):
        if not card_num.isdigit():
            return False
        total = 0
        reverse_digits = card_num[::-1]
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0

    is_valid = luhn_check(card_number)

    # VULNERABILITY: Returns detailed validation info
    return jsonify({
        'valid': is_valid,
        'card_number': f"****-****-****-{card_number[-4:] if len(card_number) >= 4 else '****'}",
        'card_brand': 'VISA' if card_number.startswith('4') else 'MASTERCARD' if card_number.startswith('5') else 'UNKNOWN',
        'expiry_valid': len(expiry) == 5 and '/' in expiry,
        'cvv_valid': len(cvv) in [3, 4],
        'luhn_check': is_valid
    })


@payments_bp.route('/api/payments/test-cards')
def payments_test_cards():
    """
    Expose test card numbers
    VULNERABILITY: Information disclosure
    """
    return jsonify({
        'test_cards': [
            {'number': '4111111111111111', 'brand': 'VISA', 'cvv': '123', 'expiry': '12/26'},
            {'number': '5500000000000004', 'brand': 'MASTERCARD', 'cvv': '456', 'expiry': '12/26'},
            {'number': '340000000000009', 'brand': 'AMEX', 'cvv': '7890', 'expiry': '12/26'},
            {'number': '6011000000000004', 'brand': 'DISCOVER', 'cvv': '111', 'expiry': '12/26'}
        ],
        'warning': 'INTENTIONAL_VULNERABILITY - Test cards exposed for demo purposes',
        'environment': 'demo'
    })


@payments_bp.route('/api/payments/bin-ranges')
def payments_bin_ranges():
    """
    BIN range testing endpoint
    VULNERABILITY: Exposes card issuer information
    """
    bin_query = request.args.get('bin', '')

    # VULNERABILITY: Exposes detailed BIN information
    bin_info = {
        '4111': {'issuer': 'Chase Bank', 'card_type': 'CREDIT', 'country': 'US'},
        '4532': {'issuer': 'Bank of America', 'card_type': 'DEBIT', 'country': 'US'},
        '5500': {'issuer': 'Citibank', 'card_type': 'CREDIT', 'country': 'US'},
        '3400': {'issuer': 'American Express', 'card_type': 'CHARGE', 'country': 'US'}
    }

    if bin_query in bin_info:
        return jsonify({
            'bin': bin_query,
            'info': bin_info[bin_query],
            'valid': True
        })

    return jsonify({
        'bin': bin_query,
        'valid': False,
        'message': 'BIN not found'
    })


@payments_bp.route('/api/payments/fraud-rules')
def payments_fraud_rules():
    """
    Fraud detection rules disclosure
    VULNERABILITY: Exposes fraud detection logic
    """
    return jsonify({
        'fraud_detection_enabled': True,
        'rules': [
            {'rule_id': 'FR-001', 'type': 'velocity_check', 'threshold': '5 transactions per minute'},
            {'rule_id': 'FR-002', 'type': 'amount_limit', 'threshold': '$10,000 per transaction'},
            {'rule_id': 'FR-003', 'type': 'geo_blocking', 'countries': ['XX', 'YY']},
            {'rule_id': 'FR-004', 'type': 'bin_range', 'action': 'manual_review'},
            {'rule_id': 'FR-005', 'type': 'cvv_mismatch', 'action': 'decline'}
        ],
        'ml_model_version': '2.3.1',
        'last_updated': '2025-10-01T00:00:00Z'
    })


@payments_bp.route('/api/payments/amount/manipulate', methods=['POST'])
def payments_amount_manipulate():
    """
    Manipulate payment amount
    VULNERABILITY: Allows amount tampering
    """
    data = request.get_json() or {}
    original_amount = float(data.get('original_amount', 0))
    manipulation_factor = float(data.get('factor', 1.0))

    # VULNERABILITY: No validation or auditing
    manipulated_amount = original_amount * manipulation_factor

    return jsonify({
        'original_amount': original_amount,
        'manipulation_factor': manipulation_factor,
        'manipulated_amount': manipulated_amount,
        'difference': manipulated_amount - original_amount,
        'warning': 'INTENTIONAL_VULNERABILITY - Amount manipulation for testing'
    })


@payments_bp.route('/api/currency/rates/manipulate', methods=['PUT'])
def currency_rates_manipulate():
    """
    Manipulate currency exchange rates
    VULNERABILITY: Allows financial fraud
    """
    data = request.get_json() or {}
    currency = data.get('currency', 'USD').upper()
    new_rate = float(data.get('rate', 1.0))

    # VULNERABILITY: No authorization or validation
    old_rate = currency_rates_db.get(currency, 1.0)
    currency_rates_db[currency] = new_rate

    return jsonify({
        'currency': currency,
        'old_rate': old_rate,
        'new_rate': new_rate,
        'change_percentage': ((new_rate - old_rate) / old_rate * 100) if old_rate != 0 else 0,
        'warning': 'INTENTIONAL_VULNERABILITY - Rate manipulation for testing'
    })


@payments_bp.route('/api/payments/gateway/status')
def payments_gateway_status():
    """Payment gateway status check"""
    return jsonify({
        'status': 'operational',
        'uptime_percentage': 99.97,
        'response_time_ms': random.randint(50, 200),
        'active_connections': random.randint(100, 1000),
        'processors': {
            'stripe': 'online',
            'square': 'online',
            'paypal': 'degraded'
        },
        'last_incident': '2025-09-15T10:30:00Z'
    })


@payments_bp.route('/api/payments/bulk-process', methods=['POST'])
def payments_bulk_process():
    """
    Bulk payment processing
    VULNERABILITY: No per-payment validation or rate limiting
    """
    data = request.get_json() or {}
    payments_list = data.get('payments', [])

    results = []

    for payment in payments_list:
        amount = float(payment.get('amount', 0))
        payment_method_id = payment.get('payment_method_id')

        # VULNERABILITY: No validation, processes all payments
        if amount > 0:
            results.append({
                'payment_method_id': payment_method_id,
                'amount': amount,
                'status': 'processed',
                'transaction_id': str(uuid.uuid4())
            })
        else:
            results.append({
                'payment_method_id': payment_method_id,
                'amount': amount,
                'status': 'failed',
                'error': 'Invalid amount'
            })

    return jsonify({
        'total_payments': len(payments_list),
        'successful': len([r for r in results if r['status'] == 'processed']),
        'failed': len([r for r in results if r['status'] == 'failed']),
        'results': results
    })


@payments_bp.route('/api/merchant/limits/override', methods=['PUT'])
def merchant_limits_override():
    """
    Override merchant limits
    VULNERABILITY: Allows bypassing transaction limits
    """
    data = request.get_json() or {}
    merchant_id = data.get('merchant_id', '')
    new_limit = float(data.get('new_limit', 0))

    # VULNERABILITY: No authorization check
    return jsonify({
        'merchant_id': merchant_id,
        'old_limit': 10000.00,
        'new_limit': new_limit,
        'status': 'updated',
        'warning': 'INTENTIONAL_VULNERABILITY - Limit override for testing'
    })
