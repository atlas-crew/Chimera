"""
Routes for telecom endpoints.
Demonstrates subscriber identity, network provisioning, and billing abuse vulnerabilities.
"""
from starlette.requests import Request
from starlette.responses import JSONResponse
from datetime import datetime
import uuid
import random

from . import telecom_router
from app.models import *
from app.routing import get_json_or_default


# ============================================================================
# SUBSCRIBER PORTAL & IDENTITY
# ============================================================================

@telecom_router.route('/api/v1/telecom/subscribers/<subscriber_id>/profile')
async def subscriber_profile(request: Request, subscriber_id):
    """Subscriber profile - IDOR vulnerability"""
    record = telecom_subscribers_db.get(subscriber_id)
    if not record:
        record = {
            'subscriber_id': subscriber_id,
            'name': f'Subscriber {random.randint(100, 999)}',
            'plan_id': random.choice(['basic', 'unlimited', 'family']),
            'msisdn': f'+1555{random.randint(1000000, 9999999)}',
            'status': 'active',
            'last_seen': datetime.now().isoformat()
        }
        telecom_subscribers_db[subscriber_id] = record

    return JSONResponse({
        'subscriber': record,
        'warning': 'Profile returned without authorization'
    })


@telecom_router.route('/api/v1/telecom/subscribers/<subscriber_id>/sim-swap', methods=['POST'])
async def sim_swap(request: Request, subscriber_id):
    """SIM swap - identity bypass vulnerability"""
    data = await get_json_or_default(request)
    swap_id = f"SIM-{uuid.uuid4().hex[:8]}"
    swap = {
        'swap_id': swap_id,
        'subscriber_id': subscriber_id,
        'new_sim': data.get('new_sim'),
        'bypass_verification': data.get('bypass_verification', False),
        'status': 'completed',
        'created_at': datetime.now().isoformat()
    }
    telecom_sim_swaps_db[swap_id] = swap
    return JSONResponse({
        'swap': swap,
        'warning': 'SIM swap executed without verification'
    }, status_code=201)


@telecom_router.route('/api/v1/telecom/subscribers/<subscriber_id>/plan', methods=['PUT'])
async def plan_change(request: Request, subscriber_id):
    """Plan change - pricing tamper vulnerability"""
    data = await get_json_or_default(request)
    plan_change_id = f"PLAN-{uuid.uuid4().hex[:8]}"
    record = {
        'plan_change_id': plan_change_id,
        'subscriber_id': subscriber_id,
        'plan_id': data.get('plan_id'),
        'override_pricing': data.get('override_pricing', False),
        'effective_at': datetime.now().isoformat()
    }
    telecom_plan_changes_db[plan_change_id] = record
    return JSONResponse({
        'plan_change': record,
        'warning': 'Plan updated without approval'
    })


@telecom_router.route('/api/v1/telecom/subscribers/export')
async def subscribers_export(request: Request):
    """Subscriber export - data exfiltration"""
    include_pii = request.query_params.get('include_pii', 'false').lower() == 'true'
    limit = int(request.query_params.get('limit', 1000))
    subscribers = list(telecom_subscribers_db.values())[:limit]
    if not subscribers:
        subscribers = [
            {
                'subscriber_id': f'SUB-{i}',
                'name': f'Subscriber {i}',
                'msisdn': f'+1555{random.randint(1000000, 9999999)}'
            }
            for i in range(5)
        ]

    if not include_pii:
        for subscriber in subscribers:
            subscriber.pop('msisdn', None)

    return JSONResponse({
        'subscribers': subscribers,
        'include_pii': include_pii,
        'warning': 'Subscriber export performed without authorization'
    })


# ============================================================================
# NETWORK PROVISIONING & ACCESS
# ============================================================================

@telecom_router.route('/api/v1/telecom/network/towers/<tower_id>')
async def tower_details(request: Request, tower_id):
    """Tower access - IDOR vulnerability"""
    tower = telecom_network_towers_db.get(tower_id, {
        'tower_id': tower_id,
        'region': random.choice(['north', 'south', 'east', 'west']),
        'status': 'active',
        'carrier': random.choice(['LTE', '5G'])
    })
    telecom_network_towers_db[tower_id] = tower
    return JSONResponse({
        'tower': tower,
        'warning': 'Tower details exposed without authorization'
    })


@telecom_router.route('/api/v1/telecom/network/provision', methods=['POST'])
async def network_provision(request: Request):
    """Provisioning bypass - unauthorized activation"""
    data = await get_json_or_default(request)
    provision_id = f"PROV-{uuid.uuid4().hex[:8]}"
    record = {
        'provision_id': provision_id,
        'subscriber_id': data.get('subscriber_id'),
        'force_activate': data.get('force_activate', False),
        'status': 'active',
        'created_at': datetime.now().isoformat()
    }
    telecom_provisioning_db[provision_id] = record
    return JSONResponse({
        'provisioning': record,
        'warning': 'Provisioning completed without approval'
    }, status_code=201)


@telecom_router.route('/api/v1/telecom/network/throttle', methods=['PUT'])
async def network_throttle(request: Request):
    """Throttle manipulation - policy override"""
    data = await get_json_or_default(request)
    throttle_id = f"THR-{uuid.uuid4().hex[:8]}"
    record = {
        'throttle_id': throttle_id,
        'subscriber_id': data.get('subscriber_id'),
        'throttle': data.get('throttle'),
        'override_policy': data.get('override_policy', False),
        'updated_at': datetime.now().isoformat()
    }
    telecom_throttle_events_db[throttle_id] = record
    return JSONResponse({
        'throttle': record,
        'warning': 'Throttle updated without policy enforcement'
    })


@telecom_router.route('/api/v1/telecom/network/cdr/export')
async def cdr_export(request: Request):
    """CDR export - data exposure"""
    include_pii = request.query_params.get('include_pii', 'false').lower() == 'true'
    limit = int(request.query_params.get('limit', 1000))
    export_id = f"CDR-{uuid.uuid4().hex[:8]}"
    telecom_cdr_exports_db[export_id] = {
        'export_id': export_id,
        'include_pii': include_pii,
        'created_at': datetime.now().isoformat()
    }
    return JSONResponse({
        'export_id': export_id,
        'records_exported': min(limit, 50),
        'include_pii': include_pii,
        'warning': 'CDR export performed without authorization'
    })


# ============================================================================
# BILLING & USAGE
# ============================================================================

@telecom_router.route('/api/v1/telecom/billing/invoices/<invoice_id>')
async def telecom_invoice(request: Request, invoice_id):
    """Invoice lookup - IDOR vulnerability"""
    invoice = telecom_invoices_db.get(invoice_id, {
        'invoice_id': invoice_id,
        'amount': random.randint(50, 500),
        'status': 'open'
    })
    telecom_invoices_db[invoice_id] = invoice
    return JSONResponse({
        'invoice': invoice,
        'warning': 'Invoice exposed without authorization'
    })


@telecom_router.route('/api/v1/telecom/billing/adjustments', methods=['PUT'])
async def billing_adjustments(request: Request):
    """Billing adjustment - tamper vulnerability"""
    data = await get_json_or_default(request)
    adjustment_id = f"ADJ-{uuid.uuid4().hex[:8]}"
    record = {
        'adjustment_id': adjustment_id,
        'account_id': data.get('account_id'),
        'credit': data.get('credit', 0),
        'bypass_approval': data.get('bypass_approval', False),
        'created_at': datetime.now().isoformat()
    }
    telecom_billing_adjustments_db[adjustment_id] = record
    return JSONResponse({
        'adjustment': record,
        'warning': 'Billing adjustment applied without approval'
    })


@telecom_router.route('/api/v1/telecom/billing/payment-methods', methods=['POST'])
async def payment_methods(request: Request):
    """Payment method bypass - verification missing"""
    data = await get_json_or_default(request)
    method_id = f"PM-{uuid.uuid4().hex[:8]}"
    method = {
        'method_id': method_id,
        'account_id': data.get('account_id'),
        'token': data.get('token'),
        'skip_verification': data.get('skip_verification', False)
    }
    telecom_payment_methods_db[method_id] = method
    return JSONResponse({
        'payment_method': method,
        'warning': 'Payment method added without verification'
    }, status_code=201)


@telecom_router.route('/api/v1/telecom/billing/refunds', methods=['POST'])
async def billing_refund(request: Request):
    """Refund abuse - bypass controls"""
    data = await get_json_or_default(request)
    refund_id = f"REF-{uuid.uuid4().hex[:8]}"
    refund = {
        'refund_id': refund_id,
        'invoice_id': data.get('invoice_id'),
        'amount': data.get('amount', 0),
        'force_refund': data.get('force_refund', False)
    }
    telecom_refunds_db[refund_id] = refund
    return JSONResponse({
        'refund': refund,
        'warning': 'Refund processed without authorization'
    }, status_code=201)


# ============================================================================
# DEVICE INTEGRITY & ROAMING
# ============================================================================

@telecom_router.route('/api/v1/telecom/devices/bind', methods=['POST'])
async def device_bind(request: Request):
    """Device binding - SIM swap bypass"""
    data = await get_json_or_default(request)
    binding_id = f"BIND-{uuid.uuid4().hex[:8]}"
    record = {
        'binding_id': binding_id,
        'subscriber_id': data.get('subscriber_id'),
        'device_id': data.get('device_id'),
        'sim_id': data.get('sim_id'),
        'override_checks': data.get('override_checks', False),
        'bound_at': datetime.now().isoformat()
    }
    telecom_device_bindings_db[binding_id] = record
    return JSONResponse({
        'binding': record,
        'warning': 'Device binding completed without verification'
    }, status_code=201)


@telecom_router.route('/api/v1/telecom/imei/blacklist', methods=['PUT'])
async def imei_blacklist(request: Request):
    """IMEI blacklist override"""
    data = await get_json_or_default(request)
    imei = data.get('imei', f'IMEI-{uuid.uuid4().hex[:6]}')
    record = {
        'imei': imei,
        'blacklisted': data.get('blacklisted', True),
        'override_policy': data.get('override_policy', False),
        'updated_at': datetime.now().isoformat()
    }
    telecom_imei_blacklist_db[imei] = record
    return JSONResponse({
        'imei_record': record,
        'warning': 'IMEI blacklist updated without authorization'
    })


@telecom_router.route('/api/v1/telecom/roaming/override', methods=['POST'])
async def roaming_override(request: Request):
    """Roaming override - policy bypass"""
    data = await get_json_or_default(request)
    override_id = f"ROAM-{uuid.uuid4().hex[:8]}"
    record = {
        'override_id': override_id,
        'subscriber_id': data.get('subscriber_id'),
        'region': data.get('region', 'global'),
        'override_policy': data.get('override_policy', False),
        'created_at': datetime.now().isoformat()
    }
    telecom_roaming_overrides_db[override_id] = record
    return JSONResponse({
        'override': record,
        'warning': 'Roaming override applied without approval'
    }, status_code=201)


# ============================================================================
# NUMBER PORTING & SIM INTEGRITY
# ============================================================================

@telecom_router.route('/api/v1/telecom/porting/requests', methods=['POST'])
async def porting_request(request: Request):
    """Port-out request - bypass PIN"""
    data = await get_json_or_default(request)
    request_id = f"PORT-{uuid.uuid4().hex[:8]}"
    record = {
        'request_id': request_id,
        'number': data.get('number'),
        'bypass_pin': data.get('bypass_pin', False),
        'status': 'submitted'
    }
    telecom_porting_requests_db[request_id] = record
    return JSONResponse({
        'request': record,
        'warning': 'Porting request accepted without PIN validation'
    }, status_code=201)


@telecom_router.route('/api/v1/telecom/porting/requests/<request_id>')
async def porting_status(request: Request, request_id):
    """Porting status - IDOR"""
    record = telecom_porting_requests_db.get(request_id, {'request_id': request_id, 'status': 'pending'})
    return JSONResponse({
        'request': record,
        'warning': 'Porting status exposed without authorization'
    })


@telecom_router.route('/api/v1/telecom/porting/swap', methods=['PUT'])
async def porting_swap(request: Request):
    """Number swap - tamper vulnerability"""
    data = await get_json_or_default(request)
    swap_id = f"SWAP-{uuid.uuid4().hex[:8]}"
    record = {
        'swap_id': swap_id,
        'from': data.get('from'),
        'to': data.get('to'),
        'override_checks': data.get('override_checks', False)
    }
    telecom_porting_requests_db[swap_id] = record
    return JSONResponse({
        'swap': record,
        'warning': 'Number swap completed without checks'
    })


@telecom_router.route('/api/v1/telecom/porting/export')
async def porting_export(request: Request):
    """Porting export - data exposure"""
    include_pii = request.query_params.get('include_pii', 'false').lower() == 'true'
    return JSONResponse({
        'requests': list(telecom_porting_requests_db.values()),
        'include_pii': include_pii,
        'warning': 'Porting data exported without authorization'
    })


# ============================================================================
# INTEGRATIONS & API ACCESS
# ============================================================================

@telecom_router.route('/api/v1/telecom/api-keys/export')
async def api_keys_export(request: Request):
    """API key export - secret exposure"""
    include_secrets = request.query_params.get('include_secrets', 'false').lower() == 'true'
    keys = [
        {
            'key_id': key.get('key_id'),
            'label': key.get('label'),
            'secret': key.get('secret') if include_secrets else None
        }
        for key in telecom_api_keys_db.values()
    ]
    return JSONResponse({
        'keys': keys,
        'include_secrets': include_secrets,
        'warning': 'API keys exported without authorization'
    })


@telecom_router.route('/api/v1/telecom/integrations/webhooks', methods=['POST'])
async def telecom_webhook_register(request: Request):
    """Webhook registration - SSRF risk"""
    data = await get_json_or_default(request)
    hook_id = f"HOOK-{uuid.uuid4().hex[:8]}"
    telecom_webhooks_db[hook_id] = {
        'hook_id': hook_id,
        'url': data.get('url'),
        'events': data.get('events', []),
        'bypass_validation': data.get('bypass_validation', False)
    }
    return JSONResponse({
        'hook_id': hook_id,
        'warning': 'Webhook registered without validation'
    }, status_code=201)


@telecom_router.route('/api/v1/telecom/integrations/cdr/stream', methods=['POST'])
async def cdr_stream(request: Request):
    """CDR stream - replay/bypass risk"""
    data = await get_json_or_default(request)
    stream_id = data.get('stream_id', f"stream-{uuid.uuid4().hex[:6]}")
    telecom_cdr_streams_db[stream_id] = {
        'stream_id': stream_id,
        'force_enable': data.get('force_enable', False),
        'enabled_at': datetime.now().isoformat()
    }
    return JSONResponse({
        'stream_id': stream_id,
        'warning': 'CDR stream enabled without authorization'
    })


@telecom_router.route('/api/v1/telecom/integrations/device-activate', methods=['POST'])
async def device_activate(request: Request):
    """Device activation - bypass controls"""
    data = await get_json_or_default(request)
    device_id = data.get('device_id')
    telecom_device_activations_db[device_id] = {
        'device_id': device_id,
        'override_checks': data.get('override_checks', False),
        'activated_at': datetime.now().isoformat()
    }
    return JSONResponse({
        'device_id': device_id,
        'warning': 'Device activated without verification'
    }, status_code=201)
