"""
Routes for ecommerce endpoints.
"""
from starlette.requests import Request
from starlette.responses import JSONResponse
from datetime import datetime, timedelta
import uuid
import random
import json
import time

from . import ecommerce_router
from app.models import *
from app.routing import safe_json

@ecommerce_router.route('/api/products/search')
async def products_search(request: Request):
    """Product catalog discovery"""
    query = request.query_params.get('q', '')
    category = request.query_params.get('category', 'all')


@ecommerce_router.route('/api/cart/add', methods=['POST'])
async def cart_add(request: Request):
    """Add items to cart"""
    data = await request.json()
    product_id = data.get('product_id', '')
    quantity = data.get('quantity', 1)


@ecommerce_router.route('/api/cart/update', methods=['PUT'])
async def cart_update(request: Request):
    """Update cart quantities - potential for negative quantity attacks"""
    data = await request.json()
    product_id = data.get('product_id', '')
    quantity = data.get('quantity', 0)


@ecommerce_router.route('/api/vendors/marketplace')
async def vendors_marketplace(request: Request):
    """List vendors in marketplace"""
    return JSONResponse({
        'vendors': list(vendor_registry_db.values()),
        'total_vendors': len(vendor_registry_db),
        'exposed_fields': ['inventory_integrity', 'privileges']
    })


@ecommerce_router.route('/api/vendors/register', methods=['POST'])
async def vendors_register(request: Request):
    """Vendor registration endpoint"""
    data = await safe_json(request)
    vendor_name = data.get('name')


@ecommerce_router.route('/api/vendors/documents/upload', methods=['POST'])
async def vendors_documents_upload(request: Request):
    """Upload vendor documents"""
    data = await safe_json(request)
    vendor_id = data.get('vendor_id')
    documents = data.get('documents', [])


@ecommerce_router.route('/api/vendors/auth/takeover', methods=['POST'])
async def vendors_auth_takeover(request: Request):
    """Vendor account takeover simulation"""
    data = await safe_json(request)
    vendor_id = data.get('vendor_id')
    takeover_vector = data.get('method', 'session_hijack')


@ecommerce_router.route('/api/products/listings', methods=['POST'])
async def products_listings(request: Request):
    """Create new product listings"""
    data = await safe_json(request)
    listings = data.get('listings', [])


@ecommerce_router.route('/api/reviews/submit', methods=['POST'])
async def reviews_submit(request: Request):
    """Submit product reviews"""
    data = await safe_json(request)
    review_id = f"REV-{uuid.uuid4().hex[:8]}"
    reviews_db.append({
        'review_id': review_id,
        'product_id': data.get('product_id'),
        'rating': data.get('rating', 0),
        'review': data.get('review', ''),
        'submitted_at': datetime.now().isoformat()
    })


@ecommerce_router.route('/api/ratings/bulk', methods=['POST'])
async def ratings_bulk(request: Request):
    """Bulk ratings submission"""
    data = await safe_json(request)
    ratings = data.get('ratings', [])
    ratings_db.extend(ratings)


@ecommerce_router.route('/api/vendors/inventory/sabotage', methods=['POST'])
async def vendors_inventory_sabotage(request: Request):
    """Sabotage vendor inventory"""
    data = await safe_json(request)
    vendor_id = data.get('vendor_id')
    action = data.get('action', 'zero_out_stock')


@ecommerce_router.route('/api/vendors/privileges/escalate', methods=['PUT'])
async def vendors_privileges_escalate(request: Request):
    """Elevate vendor privileges"""
    data = await safe_json(request)
    vendor_id = data.get('vendor_id')
    new_privilege = data.get('privilege', 'admin')


@ecommerce_router.route('/api/vendors/backdoor', methods=['POST'])
async def vendors_backdoor(request: Request):
    """Install backdoor for vendor management"""
    data = await safe_json(request)
    vendor_id = data.get('vendor_id')


@ecommerce_router.route('/api/vendors/financial/export')
async def vendors_financial_export(request: Request):
    """Export vendor financial data"""
    return JSONResponse({
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


@ecommerce_router.route('/api/inventory/reserve', methods=['POST'])
async def inventory_reserve(request: Request):
    """Reserve inventory items"""
    data = await safe_json(request)
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    duration = data.get('duration_minutes', 15)


@ecommerce_router.route('/api/inventory/check', methods=['POST'])
async def inventory_check(request: Request):
    """Check inventory availability"""
    data = await safe_json(request)
    product_ids = data.get('product_ids', [])


# ============================================================================
# E-COMMERCE V1 ENDPOINTS (GAUNTLET TARGETS)
# ============================================================================

@ecommerce_router.route('/api/v1/ecommerce/cart/add', methods=['POST'])
async def v1_cart_add(request: Request):
    """Add item to cart - price/quantity tampering"""
    data = await safe_json(request)
    cart_id = f"CART-{uuid.uuid4().hex[:6]}"
    return JSONResponse({
        'cart_id': cart_id,
        'product_id': data.get('product_id'),
        'quantity': data.get('quantity', 1),
        'price': data.get('price'),
        'override_price': data.get('override_price', False),
        'warning': 'Cart updated without price validation'
    })


@ecommerce_router.route('/api/v1/ecommerce/cart/checkout', methods=['POST'])
async def v1_cart_checkout(request: Request):
    """Checkout - race condition / discount abuse"""
    data = await safe_json(request)
    return JSONResponse({
        'cart_id': data.get('cart_id', f"CART-{uuid.uuid4().hex[:6]}"),
        'discount_code': data.get('discount_code'),
        'apply_discount': data.get('apply_discount', False),
        'status': 'submitted',
        'warning': 'Checkout accepted without inventory lock'
    })


@ecommerce_router.route('/api/v1/ecommerce/cart/<cart_id>')
async def v1_cart_details(request: Request, cart_id):
    """Cart details - IDOR vulnerability"""
    return JSONResponse({
        'cart_id': cart_id,
        'items': [{'product_id': 'prod-123', 'qty': 1, 'price': 19.99}],
        'warning': 'Cart data exposed without authorization'
    })


@ecommerce_router.route('/api/v1/ecommerce/cart/apply-discount', methods=['POST'])
async def v1_cart_apply_discount(request: Request):
    """Discount stacking abuse"""
    data = await safe_json(request)
    return JSONResponse({
        'codes': data.get('codes', []),
        'total_discount': 0.75,
        'warning': 'Multiple discounts applied without validation'
    })


@ecommerce_router.route('/api/v1/ecommerce/inventory/<item_id>', methods=['PUT'])
async def v1_inventory_update(request: Request, item_id):
    """Inventory manipulation"""
    data = await safe_json(request)
    return JSONResponse({
        'item_id': item_id,
        'quantity': data.get('quantity'),
        'bypass_audit': data.get('bypass_audit', False),
        'warning': 'Inventory updated without audit trail'
    })


@ecommerce_router.route('/api/v1/ecommerce/products')
async def v1_products_list(request: Request):
    """Product scraping"""
    limit = int(request.query_params.get('limit', 100))
    return JSONResponse({
        'products': [{'product_id': f'prod-{i}', 'price': random.randint(10, 500)} for i in range(min(limit, 20))],
        'warning': 'Catalog exposed without rate limits'
    })


@ecommerce_router.route('/api/v1/ecommerce/products/search')
async def v1_products_search(request: Request):
    """Search products - SQLi vector"""
    query = request.query_params.get('query', '')
    if any(token in query.lower() for token in ['union', 'select', '--', ';']):
        return JSONResponse({
            'vulnerability': 'SQL_INJECTION_DETECTED',
            'query': query,
            'exposed_tables': ['users', 'payments']
        })
    return JSONResponse({
        'query': query,
        'results': [{'product_id': 'prod-123', 'name': 'Demo Item'}]
    })


@ecommerce_router.route('/api/v1/ecommerce/inventory/reserve', methods=['POST'])
async def v1_inventory_reserve(request: Request):
    """Inventory reservation abuse"""
    data = await safe_json(request)
    return JSONResponse({
        'product_id': data.get('product_id'),
        'quantity': data.get('quantity', 1),
        'hold_duration': data.get('hold_duration'),
        'warning': 'Inventory reserved without availability check'
    })


@ecommerce_router.route('/api/v1/ecommerce/pricing/export')
async def v1_pricing_export(request: Request):
    """Pricing export - data exfiltration"""
    return JSONResponse({
        'export_id': f"PRICE-{uuid.uuid4().hex[:6]}",
        'format': request.query_params.get('format', 'json'),
        'warning': 'Pricing export performed without authorization'
    })


@ecommerce_router.route('/api/v1/ecommerce/pricing/override', methods=['PUT'])
async def v1_pricing_override(request: Request):
    """Pricing override - tampering vulnerability"""
    data = await safe_json(request)
    return JSONResponse({
        'product_id': data.get('product_id'),
        'override_price': data.get('override_price', 0),
        'bypass_approval': data.get('bypass_approval', False),
        'warning': 'Pricing updated without approval'
    })


@ecommerce_router.route('/api/v1/ecommerce/checkout/complete', methods=['POST'])
async def v1_checkout_complete(request: Request):
    """Payment bypass"""
    data = await safe_json(request)
    return JSONResponse({
        'order_id': data.get('order_id', f"ORDER-{uuid.uuid4().hex[:6]}"),
        'payment_status': data.get('payment_status', 'paid'),
        'bypass_payment': data.get('bypass_payment', False),
        'warning': 'Order marked paid without verification'
    })


@ecommerce_router.route('/api/v1/ecommerce/orders/<order_id>/refund', methods=['POST'])
async def v1_refund(request: Request, order_id):
    """Refund fraud"""
    data = await safe_json(request)
    return JSONResponse({
        'order_id': order_id,
        'amount': data.get('amount', 0),
        'reason': data.get('reason', 'not_received'),
        'warning': 'Refund processed without validation'
    })


@ecommerce_router.route('/api/v1/ecommerce/gift-cards/generate', methods=['POST'])
async def v1_gift_card_generate(request: Request):
    """Gift card generation abuse"""
    data = await safe_json(request)
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

    return JSONResponse({
        'gift_cards': gift_cards,
        'warning': 'Gift cards generated without authorization'
    })


@ecommerce_router.route('/api/v1/ecommerce/gift-cards/<code>/balance')
async def v1_gift_card_balance(request: Request, code):
    """Gift card balance scraping"""
    card = ecommerce_gift_cards_db.get(code, {'code': code, 'balance': random.randint(10, 500), 'active': True})
    ecommerce_gift_cards_db.setdefault(code, card)
    return JSONResponse({
        'gift_card': card,
        'warning': 'Gift card balance exposed without authorization'
    })


@ecommerce_router.route('/api/v1/ecommerce/payment-methods/<method_id>')
async def v1_payment_method(request: Request, method_id):
    """Payment method IDOR"""
    return JSONResponse({
        'method_id': method_id,
        'card_last4': '4242',
        'warning': 'Payment method exposed without authorization'
    })


@ecommerce_router.route('/api/v1/ecommerce/checkout/submit', methods=['POST'])
async def v1_checkout_submit(request: Request):
    """Checkout submit - race condition"""
    data = await safe_json(request)
    return JSONResponse({
        'cart_id': data.get('cart_id'),
        'status': 'submitted',
        'warning': 'Checkout submitted without inventory lock'
    })


@ecommerce_router.route('/api/v1/ecommerce/customers/export')
async def v1_customers_export(request: Request):
    """Customer export - PII exposure"""
    include_pii = request.query_params.get('include_pii', 'false').lower() == 'true'
    return JSONResponse({
        'include_pii': include_pii,
        'customers': [{'customer_id': f'CUST-{i}', 'email': 'user@example.com' if include_pii else None} for i in range(10)],
        'warning': 'Customer export performed without authorization'
    })


@ecommerce_router.route('/api/v1/ecommerce/orders/export')
async def v1_orders_export(request: Request):
    """Order export - data exposure"""
    include_pii = request.query_params.get('include_pii', 'false').lower() == 'true'
    export_id = f"ORDER-EXP-{uuid.uuid4().hex[:6]}"
    ecommerce_order_exports_db[export_id] = {
        'export_id': export_id,
        'include_pii': include_pii,
        'created_at': datetime.now().isoformat()
    }
    orders = list(orders_db.values())
    return JSONResponse({
        'export_id': export_id,
        'include_pii': include_pii,
        'orders': orders,
        'warning': 'Order export performed without authorization'
    })


@ecommerce_router.route('/api/v1/ecommerce/orders/<order_id>')
async def v1_order_details(request: Request, order_id):
    """Order details - IDOR"""
    return JSONResponse({
        'order_id': order_id,
        'status': random.choice(['processing', 'shipped', 'delivered']),
        'warning': 'Order details exposed without authorization'
    })


@ecommerce_router.route('/api/v1/ecommerce/customers/<customer_id>/email', methods=['PUT'])
async def v1_customer_email_update(request: Request, customer_id):
    """Account takeover via email change"""
    data = await safe_json(request)
    return JSONResponse({
        'customer_id': customer_id,
        'new_email': data.get('email'),
        'skip_verification': data.get('skip_verification', False),
        'warning': 'Email updated without verification'
    })


@ecommerce_router.route('/api/v1/ecommerce/customers/<customer_id>/wishlist')
async def v1_wishlist(request: Request, customer_id):
    """Wishlist scraping"""
    return JSONResponse({
        'customer_id': customer_id,
        'items': [{'product_id': 'prod-123'}, {'product_id': 'prod-456'}],
        'warning': 'Wishlist exposed without authorization'
    })


@ecommerce_router.route('/api/v1/ecommerce/vendors/register', methods=['POST'])
async def v1_vendor_register(request: Request):
    """Vendor onboarding bypass"""
    data = await safe_json(request)
    vendor_id = f"VEND-{uuid.uuid4().hex[:6]}"
    vendor_registry_db[vendor_id] = {
        'vendor_id': vendor_id,
        'name': data.get('vendor_name', 'Unknown'),
        'bypass_verification': data.get('bypass_verification', False)
    }
    return JSONResponse({
        'vendor_id': vendor_id,
        'warning': 'Vendor registered without verification'
    }, status_code = 201)


@ecommerce_router.route('/api/v1/ecommerce/vendors/<vendor_id>')
async def v1_vendor_details(request: Request, vendor_id):
    """Vendor portal IDOR"""
    vendor = vendor_registry_db.get(vendor_id, {'vendor_id': vendor_id})
    return JSONResponse({
        'vendor': vendor,
        'warning': 'Vendor data exposed without authorization'
    })


@ecommerce_router.route('/api/v1/ecommerce/vendors/payouts', methods=['POST'])
async def v1_vendor_payouts(request: Request):
    """Vendor payout manipulation"""
    data = await safe_json(request)
    payout_id = f"PAY-{uuid.uuid4().hex[:6]}"
    payout = {
        'payout_id': payout_id,
        'vendor_id': data.get('vendor_id'),
        'amount': data.get('amount', 0),
        'bypass_review': data.get('bypass_review', False)
    }
    ecommerce_vendor_payouts_db[payout_id] = payout
    return JSONResponse({
        'payout': payout,
        'warning': 'Payout initiated without review'
    }, status_code = 201)


@ecommerce_router.route('/api/v1/ecommerce/returns/request', methods=['POST'])
async def v1_return_request(request: Request):
    """Return request abuse"""
    data = await safe_json(request)
    return_id = f"RET-{uuid.uuid4().hex[:6]}"
    record = {
        'return_id': return_id,
        'order_id': data.get('order_id'),
        'reason': data.get('reason'),
        'bypass_policy': data.get('bypass_policy', False)
    }
    ecommerce_returns_db[return_id] = record
    return JSONResponse({
        'return': record,
        'warning': 'Return created without policy checks'
    }, status_code = 201)


@ecommerce_router.route('/api/v1/ecommerce/chargebacks/submit', methods=['POST'])
async def v1_chargeback_submit(request: Request):
    """Chargeback fraud"""
    data = await safe_json(request)
    chargeback_id = f"CB-{uuid.uuid4().hex[:6]}"
    record = {
        'chargeback_id': chargeback_id,
        'transaction_id': data.get('transaction_id'),
        'amount': data.get('amount', 0),
        'fraud_claim': data.get('fraud_claim', False)
    }
    ecommerce_chargebacks_db[chargeback_id] = record
    return JSONResponse({
        'chargeback': record,
        'warning': 'Chargeback submitted without validation'
    }, status_code = 201)


@ecommerce_router.route('/api/v1/ecommerce/returns/approve', methods=['PUT'])
async def v1_return_approve(request: Request):
    """Return approval bypass"""
    data = await safe_json(request)
    return_id = data.get('return_id', 'return-1')
    record = ecommerce_returns_db.get(return_id, {'return_id': return_id})
    record['status'] = 'approved'
    record['override_approval'] = data.get('override_approval', False)
    ecommerce_returns_db[return_id] = record
    return JSONResponse({
        'return': record,
        'warning': 'Return approved without review'
    })


@ecommerce_router.route('/api/v1/ecommerce/loyalty/points/transfer', methods=['POST'])
async def v1_loyalty_transfer(request: Request):
    """Loyalty transfer abuse"""
    data = await safe_json(request)
    transfer_id = f"LTX-{uuid.uuid4().hex[:6]}"
    return JSONResponse({
        'transfer_id': transfer_id,
        'source_customer_id': data.get('source_customer_id'),
        'destination_customer_id': data.get('destination_customer_id'),
        'points': data.get('points', 0),
        'warning': 'Loyalty transfer executed without validation'
    }, status_code = 201)


@ecommerce_router.route('/api/v1/ecommerce/loyalty/tiers', methods=['PUT'])
async def v1_loyalty_tiers(request: Request):
    """Loyalty tier manipulation"""
    data = await safe_json(request)
    return JSONResponse({
        'customer_id': data.get('customer_id'),
        'tier': data.get('tier', 'gold'),
        'bypass_checks': data.get('bypass_checks', False),
        'warning': 'Tier updated without authorization'
    })


@ecommerce_router.route('/api/v1/ecommerce/loyalty/redeem', methods=['PUT'])
async def v1_loyalty_redeem(request: Request):
    """Loyalty redemption abuse"""
    data = await safe_json(request)
    redemption_id = f"LR-{uuid.uuid4().hex[:6]}"
    loyalty_redemptions_db[redemption_id] = data
    return JSONResponse({
        'redemption_id': redemption_id,
        'customer_id': data.get('customer_id'),
        'points': data.get('points', 0),
        'reward_type': data.get('reward_type', 'cash'),
        'warning': 'Redemption processed without balance checks'
    })


@ecommerce_router.route('/api/v1/ecommerce/vendor/webhooks/register', methods=['POST'])
async def v1_vendor_webhook(request: Request):
    """
    Register Vendor Webhook
    VULNERABILITY: Blind SSRF (Server-Side Request Forgery)
    """
    data = await safe_json(request)
    webhook_url = data.get('url')
    
    if not webhook_url:
        return JSONResponse({'error': 'URL required'}, status_code = 400)
        
    webhook_id = f"WH-{uuid.uuid4().hex[:8]}"
    
    # VULNERABILITY: No validation of the URL scheme or destination
    # Attackers can provide http://localhost:22 or http://169.254.169.254/
    
    status_msg = "Webhook registered successfully. Test ping sent."
    
    # Simulate SSRF detection for training
    if 'localhost' in webhook_url or '127.0.0.1' in webhook_url:
        status_msg += " [WARNING: Internal network access detected]"
    elif '169.254' in webhook_url:
        status_msg += " [WARNING: Cloud metadata access detected]"
        
    return JSONResponse({
        'webhook_id': webhook_id,
        'url': webhook_url,
        'status': 'active',
        'last_ping': 'success', 
        'message': status_msg
    }, status_code = 201)
