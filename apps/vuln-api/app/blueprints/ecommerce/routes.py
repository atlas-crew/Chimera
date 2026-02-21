"""
Routes for ecommerce endpoints.
"""

from flask import request, jsonify, render_template_string, session
from datetime import datetime, timedelta
import uuid
import random
import json
import time

from . import ecommerce_bp
from app.models import *

@ecommerce_bp.route('/api/products/search')
def products_search():
    """Product catalog discovery"""
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')


@ecommerce_bp.route('/api/cart/add', methods=['POST'])
def cart_add():
    """Add items to cart"""
    data = request.get_json()
    product_id = data.get('product_id', '')
    quantity = data.get('quantity', 1)


@ecommerce_bp.route('/api/cart/update', methods=['PUT'])
def cart_update():
    """Update cart quantities - potential for negative quantity attacks"""
    data = request.get_json()
    product_id = data.get('product_id', '')
    quantity = data.get('quantity', 0)


@ecommerce_bp.route('/api/vendors/marketplace')
def vendors_marketplace():
    """List vendors in marketplace"""
    return jsonify({
        'vendors': list(vendor_registry_db.values()),
        'total_vendors': len(vendor_registry_db),
        'exposed_fields': ['inventory_integrity', 'privileges']
    })


@ecommerce_bp.route('/api/vendors/register', methods=['POST'])
def vendors_register():
    """Vendor registration endpoint"""
    data = request.get_json() or {}
    vendor_name = data.get('name')


@ecommerce_bp.route('/api/vendors/documents/upload', methods=['POST'])
def vendors_documents_upload():
    """Upload vendor documents"""
    data = request.get_json() or {}
    vendor_id = data.get('vendor_id')
    documents = data.get('documents', [])


@ecommerce_bp.route('/api/vendors/auth/takeover', methods=['POST'])
def vendors_auth_takeover():
    """Vendor account takeover simulation"""
    data = request.get_json() or {}
    vendor_id = data.get('vendor_id')
    takeover_vector = data.get('method', 'session_hijack')


@ecommerce_bp.route('/api/products/listings', methods=['POST'])
def products_listings():
    """Create new product listings"""
    data = request.get_json() or {}
    listings = data.get('listings', [])


@ecommerce_bp.route('/api/reviews/submit', methods=['POST'])
def reviews_submit():
    """Submit product reviews"""
    data = request.get_json() or {}
    review_id = f"REV-{uuid.uuid4().hex[:8]}"
    reviews_db.append({
        'review_id': review_id,
        'product_id': data.get('product_id'),
        'rating': data.get('rating', 0),
        'review': data.get('review', ''),
        'submitted_at': datetime.now().isoformat()
    })


@ecommerce_bp.route('/api/ratings/bulk', methods=['POST'])
def ratings_bulk():
    """Bulk ratings submission"""
    data = request.get_json() or {}
    ratings = data.get('ratings', [])
    ratings_db.extend(ratings)


@ecommerce_bp.route('/api/vendors/inventory/sabotage', methods=['POST'])
def vendors_inventory_sabotage():
    """Sabotage vendor inventory"""
    data = request.get_json() or {}
    vendor_id = data.get('vendor_id')
    action = data.get('action', 'zero_out_stock')


@ecommerce_bp.route('/api/vendors/privileges/escalate', methods=['PUT'])
def vendors_privileges_escalate():
    """Elevate vendor privileges"""
    data = request.get_json() or {}
    vendor_id = data.get('vendor_id')
    new_privilege = data.get('privilege', 'admin')


@ecommerce_bp.route('/api/vendors/backdoor', methods=['POST'])
def vendors_backdoor():
    """Install backdoor for vendor management"""
    data = request.get_json() or {}
    vendor_id = data.get('vendor_id')


@ecommerce_bp.route('/api/vendors/financial/export')
def vendors_financial_export():
    """Export vendor financial data"""
    return jsonify({
        'vendors': [
            {
                'vendor_id': vendor['vendor_id'],
                'name': vendor['name'],
                'revenue': round(random.uniform(10000, 250000), 2),
                'chargebacks': random.randint(0, 25)
            }
            for vendor in vendor_registry_db.values()
        ],
        'export_id': f"VEND-FIN-{uuid.uuid4().hex[:8]}",
        'data_classification': 'confidential'
    })


@ecommerce_bp.route('/api/inventory/reserve', methods=['POST'])
def inventory_reserve():
    """Reserve inventory items"""
    data = request.get_json() or {}
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    duration = data.get('duration_minutes', 15)


@ecommerce_bp.route('/api/inventory/check', methods=['POST'])
def inventory_check():
    """Check inventory availability"""
    data = request.get_json() or {}
    product_ids = data.get('product_ids', [])


# ============================================================================
# E-COMMERCE V1 ENDPOINTS (GAUNTLET TARGETS)
# ============================================================================

@ecommerce_bp.route('/api/v1/ecommerce/cart/add', methods=['POST'])
def v1_cart_add():
    """Add item to cart - price/quantity tampering"""
    data = request.get_json() or {}
    cart_id = f"CART-{uuid.uuid4().hex[:6]}"
    return jsonify({
        'cart_id': cart_id,
        'product_id': data.get('product_id'),
        'quantity': data.get('quantity', 1),
        'price': data.get('price'),
        'override_price': data.get('override_price', False),
        'warning': 'Cart updated without price validation'
    })


@ecommerce_bp.route('/api/v1/ecommerce/cart/checkout', methods=['POST'])
def v1_cart_checkout():
    """Checkout - race condition / discount abuse"""
    data = request.get_json() or {}
    return jsonify({
        'cart_id': data.get('cart_id', f"CART-{uuid.uuid4().hex[:6]}"),
        'discount_code': data.get('discount_code'),
        'apply_discount': data.get('apply_discount', False),
        'status': 'submitted',
        'warning': 'Checkout accepted without inventory lock'
    })


@ecommerce_bp.route('/api/v1/ecommerce/cart/<cart_id>')
def v1_cart_details(cart_id):
    """Cart details - IDOR vulnerability"""
    return jsonify({
        'cart_id': cart_id,
        'items': [{'product_id': 'prod-123', 'qty': 1, 'price': 19.99}],
        'warning': 'Cart data exposed without authorization'
    })


@ecommerce_bp.route('/api/v1/ecommerce/cart/apply-discount', methods=['POST'])
def v1_cart_apply_discount():
    """Discount stacking abuse"""
    data = request.get_json() or {}
    return jsonify({
        'codes': data.get('codes', []),
        'total_discount': 0.75,
        'warning': 'Multiple discounts applied without validation'
    })


@ecommerce_bp.route('/api/v1/ecommerce/inventory/<item_id>', methods=['PUT'])
def v1_inventory_update(item_id):
    """Inventory manipulation"""
    data = request.get_json() or {}
    return jsonify({
        'item_id': item_id,
        'quantity': data.get('quantity'),
        'bypass_audit': data.get('bypass_audit', False),
        'warning': 'Inventory updated without audit trail'
    })


@ecommerce_bp.route('/api/v1/ecommerce/products')
def v1_products_list():
    """Product scraping"""
    limit = int(request.args.get('limit', 100))
    return jsonify({
        'products': [{'product_id': f'prod-{i}', 'price': random.randint(10, 500)} for i in range(min(limit, 20))],
        'warning': 'Catalog exposed without rate limits'
    })


@ecommerce_bp.route('/api/v1/ecommerce/products/search')
def v1_products_search():
    """Search products - SQLi vector"""
    query = request.args.get('query', '')
    if any(token in query.lower() for token in ['union', 'select', '--', ';']):
        return jsonify({
            'vulnerability': 'SQL_INJECTION_DETECTED',
            'query': query,
            'exposed_tables': ['users', 'payments']
        })
    return jsonify({
        'query': query,
        'results': [{'product_id': 'prod-123', 'name': 'Demo Item'}]
    })


@ecommerce_bp.route('/api/v1/ecommerce/inventory/reserve', methods=['POST'])
def v1_inventory_reserve():
    """Inventory reservation abuse"""
    data = request.get_json() or {}
    return jsonify({
        'product_id': data.get('product_id'),
        'quantity': data.get('quantity', 1),
        'hold_duration': data.get('hold_duration'),
        'warning': 'Inventory reserved without availability check'
    })


@ecommerce_bp.route('/api/v1/ecommerce/pricing/export')
def v1_pricing_export():
    """Pricing export - data exfiltration"""
    return jsonify({
        'export_id': f"PRICE-{uuid.uuid4().hex[:6]}",
        'format': request.args.get('format', 'json'),
        'warning': 'Pricing export performed without authorization'
    })


@ecommerce_bp.route('/api/v1/ecommerce/pricing/override', methods=['PUT'])
def v1_pricing_override():
    """Pricing override - tampering vulnerability"""
    data = request.get_json() or {}
    return jsonify({
        'product_id': data.get('product_id'),
        'override_price': data.get('override_price', 0),
        'bypass_approval': data.get('bypass_approval', False),
        'warning': 'Pricing updated without approval'
    })


@ecommerce_bp.route('/api/v1/ecommerce/checkout/complete', methods=['POST'])
def v1_checkout_complete():
    """Payment bypass"""
    data = request.get_json() or {}
    return jsonify({
        'order_id': data.get('order_id', f"ORDER-{uuid.uuid4().hex[:6]}"),
        'payment_status': data.get('payment_status', 'paid'),
        'bypass_payment': data.get('bypass_payment', False),
        'warning': 'Order marked paid without verification'
    })


@ecommerce_bp.route('/api/v1/ecommerce/orders/<order_id>/refund', methods=['POST'])
def v1_refund(order_id):
    """Refund fraud"""
    data = request.get_json() or {}
    return jsonify({
        'order_id': order_id,
        'amount': data.get('amount', 0),
        'reason': data.get('reason', 'not_received'),
        'warning': 'Refund processed without validation'
    })


@ecommerce_bp.route('/api/v1/ecommerce/gift-cards/generate', methods=['POST'])
def v1_gift_card_generate():
    """Gift card generation abuse"""
    data = request.get_json() or {}
    gift_cards = []
    for _ in range(min(data.get('quantity', 1), 5)):
        code = f'GC-{uuid.uuid4().hex[:6]}'
        amount = data.get('amount', 0)
        ecommerce_gift_cards_db[code] = {
            'code': code,
            'balance': amount,
            'active': True
        }
        gift_cards.append({'code': code, 'amount': amount})

    return jsonify({
        'gift_cards': gift_cards,
        'warning': 'Gift cards generated without authorization'
    })


@ecommerce_bp.route('/api/v1/ecommerce/gift-cards/<code>/balance')
def v1_gift_card_balance(code):
    """Gift card balance scraping"""
    card = ecommerce_gift_cards_db.get(code, {'code': code, 'balance': random.randint(10, 500), 'active': True})
    ecommerce_gift_cards_db.setdefault(code, card)
    return jsonify({
        'gift_card': card,
        'warning': 'Gift card balance exposed without authorization'
    })


@ecommerce_bp.route('/api/v1/ecommerce/payment-methods/<method_id>')
def v1_payment_method(method_id):
    """Payment method IDOR"""
    return jsonify({
        'method_id': method_id,
        'card_last4': '4242',
        'warning': 'Payment method exposed without authorization'
    })


@ecommerce_bp.route('/api/v1/ecommerce/checkout/submit', methods=['POST'])
def v1_checkout_submit():
    """Checkout submit - race condition"""
    data = request.get_json() or {}
    return jsonify({
        'cart_id': data.get('cart_id'),
        'status': 'submitted',
        'warning': 'Checkout submitted without inventory lock'
    })


@ecommerce_bp.route('/api/v1/ecommerce/customers/export')
def v1_customers_export():
    """Customer export - PII exposure"""
    include_pii = request.args.get('include_pii', 'false').lower() == 'true'
    return jsonify({
        'include_pii': include_pii,
        'customers': [{'customer_id': f'CUST-{i}', 'email': 'user@example.com' if include_pii else None} for i in range(10)],
        'warning': 'Customer export performed without authorization'
    })


@ecommerce_bp.route('/api/v1/ecommerce/orders/export')
def v1_orders_export():
    """Order export - data exposure"""
    include_pii = request.args.get('include_pii', 'false').lower() == 'true'
    export_id = f"ORDER-EXP-{uuid.uuid4().hex[:6]}"
    ecommerce_order_exports_db[export_id] = {
        'export_id': export_id,
        'include_pii': include_pii,
        'created_at': datetime.now().isoformat()
    }
    orders = list(orders_db.values())
    return jsonify({
        'export_id': export_id,
        'include_pii': include_pii,
        'orders': orders,
        'warning': 'Order export performed without authorization'
    })


@ecommerce_bp.route('/api/v1/ecommerce/orders/<order_id>')
def v1_order_details(order_id):
    """Order details - IDOR"""
    return jsonify({
        'order_id': order_id,
        'status': random.choice(['processing', 'shipped', 'delivered']),
        'warning': 'Order details exposed without authorization'
    })


@ecommerce_bp.route('/api/v1/ecommerce/customers/<customer_id>/email', methods=['PUT'])
def v1_customer_email_update(customer_id):
    """Account takeover via email change"""
    data = request.get_json() or {}
    return jsonify({
        'customer_id': customer_id,
        'new_email': data.get('email'),
        'skip_verification': data.get('skip_verification', False),
        'warning': 'Email updated without verification'
    })


@ecommerce_bp.route('/api/v1/ecommerce/customers/<customer_id>/wishlist')
def v1_wishlist(customer_id):
    """Wishlist scraping"""
    return jsonify({
        'customer_id': customer_id,
        'items': [{'product_id': 'prod-123'}, {'product_id': 'prod-456'}],
        'warning': 'Wishlist exposed without authorization'
    })


@ecommerce_bp.route('/api/v1/ecommerce/vendors/register', methods=['POST'])
def v1_vendor_register():
    """Vendor onboarding bypass"""
    data = request.get_json() or {}
    vendor_id = f"VEND-{uuid.uuid4().hex[:6]}"
    vendor_registry_db[vendor_id] = {
        'vendor_id': vendor_id,
        'name': data.get('vendor_name', 'Unknown'),
        'bypass_verification': data.get('bypass_verification', False)
    }
    return jsonify({
        'vendor_id': vendor_id,
        'warning': 'Vendor registered without verification'
    }), 201


@ecommerce_bp.route('/api/v1/ecommerce/vendors/<vendor_id>')
def v1_vendor_details(vendor_id):
    """Vendor portal IDOR"""
    vendor = vendor_registry_db.get(vendor_id, {'vendor_id': vendor_id})
    return jsonify({
        'vendor': vendor,
        'warning': 'Vendor data exposed without authorization'
    })


@ecommerce_bp.route('/api/v1/ecommerce/vendors/payouts', methods=['POST'])
def v1_vendor_payouts():
    """Vendor payout manipulation"""
    data = request.get_json() or {}
    payout_id = f"PAY-{uuid.uuid4().hex[:6]}"
    payout = {
        'payout_id': payout_id,
        'vendor_id': data.get('vendor_id'),
        'amount': data.get('amount', 0),
        'bypass_review': data.get('bypass_review', False)
    }
    ecommerce_vendor_payouts_db[payout_id] = payout
    return jsonify({
        'payout': payout,
        'warning': 'Payout initiated without review'
    }), 201


@ecommerce_bp.route('/api/v1/ecommerce/returns/request', methods=['POST'])
def v1_return_request():
    """Return request abuse"""
    data = request.get_json() or {}
    return_id = f"RET-{uuid.uuid4().hex[:6]}"
    record = {
        'return_id': return_id,
        'order_id': data.get('order_id'),
        'reason': data.get('reason'),
        'bypass_policy': data.get('bypass_policy', False)
    }
    ecommerce_returns_db[return_id] = record
    return jsonify({
        'return': record,
        'warning': 'Return created without policy checks'
    }), 201


@ecommerce_bp.route('/api/v1/ecommerce/chargebacks/submit', methods=['POST'])
def v1_chargeback_submit():
    """Chargeback fraud"""
    data = request.get_json() or {}
    chargeback_id = f"CB-{uuid.uuid4().hex[:6]}"
    record = {
        'chargeback_id': chargeback_id,
        'transaction_id': data.get('transaction_id'),
        'amount': data.get('amount', 0),
        'fraud_claim': data.get('fraud_claim', False)
    }
    ecommerce_chargebacks_db[chargeback_id] = record
    return jsonify({
        'chargeback': record,
        'warning': 'Chargeback submitted without validation'
    }), 201


@ecommerce_bp.route('/api/v1/ecommerce/returns/approve', methods=['PUT'])
def v1_return_approve():
    """Return approval bypass"""
    data = request.get_json() or {}
    return_id = data.get('return_id', 'return-1')
    record = ecommerce_returns_db.get(return_id, {'return_id': return_id})
    record['status'] = 'approved'
    record['override_approval'] = data.get('override_approval', False)
    ecommerce_returns_db[return_id] = record
    return jsonify({
        'return': record,
        'warning': 'Return approved without review'
    })


@ecommerce_bp.route('/api/v1/ecommerce/loyalty/points/transfer', methods=['POST'])
def v1_loyalty_transfer():
    """Loyalty transfer abuse"""
    data = request.get_json() or {}
    transfer_id = f"LTX-{uuid.uuid4().hex[:6]}"
    return jsonify({
        'transfer_id': transfer_id,
        'source_customer_id': data.get('source_customer_id'),
        'destination_customer_id': data.get('destination_customer_id'),
        'points': data.get('points', 0),
        'warning': 'Loyalty transfer executed without validation'
    }), 201


@ecommerce_bp.route('/api/v1/ecommerce/loyalty/tiers', methods=['PUT'])
def v1_loyalty_tiers():
    """Loyalty tier manipulation"""
    data = request.get_json() or {}
    return jsonify({
        'customer_id': data.get('customer_id'),
        'tier': data.get('tier', 'gold'),
        'bypass_checks': data.get('bypass_checks', False),
        'warning': 'Tier updated without authorization'
    })


@ecommerce_bp.route('/api/v1/ecommerce/loyalty/redeem', methods=['PUT'])
def v1_loyalty_redeem():
    """Loyalty redemption abuse"""
    data = request.get_json() or {}
    redemption_id = f"LR-{uuid.uuid4().hex[:6]}"
    loyalty_redemptions_db[redemption_id] = data
    return jsonify({
        'redemption_id': redemption_id,
        'customer_id': data.get('customer_id'),
        'points': data.get('points', 0),
        'reward_type': data.get('reward_type', 'cash'),
        'warning': 'Redemption processed without balance checks'
    })


@ecommerce_bp.route('/api/v1/ecommerce/vendor/webhooks/register', methods=['POST'])
def v1_vendor_webhook():
    """
    Register Vendor Webhook
    VULNERABILITY: Blind SSRF (Server-Side Request Forgery)
    """
    data = request.get_json() or {}
    webhook_url = data.get('url')
    
    if not webhook_url:
        return jsonify({'error': 'URL required'}), 400
        
    webhook_id = f"WH-{uuid.uuid4().hex[:8]}"
    
    # VULNERABILITY: No validation of the URL scheme or destination
    # Attackers can provide http://localhost:22 or http://169.254.169.254/
    
    status_msg = "Webhook registered successfully. Test ping sent."
    
    # Simulate SSRF detection for training
    if 'localhost' in webhook_url or '127.0.0.1' in webhook_url:
        status_msg += " [WARNING: Internal network access detected]"
    elif '169.254' in webhook_url:
        status_msg += " [WARNING: Cloud metadata access detected]"
        
    return jsonify({
        'webhook_id': webhook_id,
        'url': webhook_url,
        'status': 'active',
        'last_ping': 'success', 
        'message': status_msg
    }), 201
