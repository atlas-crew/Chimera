"""
Routes for telecom endpoints.
Demonstrates subscriber identity, network provisioning, and billing abuse vulnerabilities.
"""

from flask import request, jsonify
from datetime import datetime
import uuid
import random

from . import telecom_bp
from app.models import *


# ============================================================================
# SUBSCRIBER PORTAL & IDENTITY
# ============================================================================

@telecom_bp.route('/api/v1/telecom/subscribers/<subscriber_id>/profile')
def subscriber_profile(subscriber_id):
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

    return jsonify({
        'subscriber': record,
        'warning': 'Profile returned without authorization'
    })


@telecom_bp.route('/api/v1/telecom/subscribers/<subscriber_id>/sim-swap', methods=['POST'])
def sim_swap(subscriber_id):
    """SIM swap - identity bypass vulnerability"""
    data = request.get_json() or {}
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
    return jsonify({
        'swap': swap,
        'warning': 'SIM swap executed without verification'
    }), 201


@telecom_bp.route('/api/v1/telecom/subscribers/<subscriber_id>/plan', methods=['PUT'])
def plan_change(subscriber_id):
    """Plan change - pricing tamper vulnerability"""
    data = request.get_json() or {}
    plan_change_id = f"PLAN-{uuid.uuid4().hex[:8]}"
    record = {
        'plan_change_id': plan_change_id,
        'subscriber_id': subscriber_id,
        'plan_id': data.get('plan_id'),
        'override_pricing': data.get('override_pricing', False),
        'effective_at': datetime.now().isoformat()
    }
    telecom_plan_changes_db[plan_change_id] = record
    return jsonify({
        'plan_change': record,
        'warning': 'Plan updated without approval'
    })


@telecom_bp.route('/api/v1/telecom/subscribers/export')
def subscribers_export():
    """Subscriber export - data exfiltration"""
    include_pii = request.args.get('include_pii', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 1000))
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

    return jsonify({
        'subscribers': subscribers,
        'include_pii': include_pii,
        'warning': 'Subscriber export performed without authorization'
    })


# ============================================================================
# NETWORK PROVISIONING & ACCESS
# ============================================================================

@telecom_bp.route('/api/v1/telecom/network/towers/<tower_id>')
def tower_details(tower_id):
    """Tower access - IDOR vulnerability"""
    tower = telecom_network_towers_db.get(tower_id, {
        'tower_id': tower_id,
        'region': random.choice(['north', 'south', 'east', 'west']),
        'status': 'active',
        'carrier': random.choice(['LTE', '5G'])
    })
    telecom_network_towers_db[tower_id] = tower
    return jsonify({
        'tower': tower,
        'warning': 'Tower details exposed without authorization'
    })


@telecom_bp.route('/api/v1/telecom/network/provision', methods=['POST'])
def network_provision():
    """Provisioning bypass - unauthorized activation"""
    data = request.get_json() or {}
    provision_id = f"PROV-{uuid.uuid4().hex[:8]}"
    record = {
        'provision_id': provision_id,
        'subscriber_id': data.get('subscriber_id'),
        'force_activate': data.get('force_activate', False),
        'status': 'active',
        'created_at': datetime.now().isoformat()
    }
    telecom_provisioning_db[provision_id] = record
    return jsonify({
        'provisioning': record,
        'warning': 'Provisioning completed without approval'
    }), 201


@telecom_bp.route('/api/v1/telecom/network/throttle', methods=['PUT'])
def network_throttle():
    """Throttle manipulation - policy override"""
    data = request.get_json() or {}
    throttle_id = f"THR-{uuid.uuid4().hex[:8]}"
    record = {
        'throttle_id': throttle_id,
        'subscriber_id': data.get('subscriber_id'),
        'throttle': data.get('throttle'),
        'override_policy': data.get('override_policy', False),
        'updated_at': datetime.now().isoformat()
    }
    telecom_throttle_events_db[throttle_id] = record
    return jsonify({
        'throttle': record,
        'warning': 'Throttle updated without policy enforcement'
    })


@telecom_bp.route('/api/v1/telecom/network/cdr/export')
def cdr_export():
    """CDR export - data exposure"""
    include_pii = request.args.get('include_pii', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 1000))
    export_id = f"CDR-{uuid.uuid4().hex[:8]}"
    telecom_cdr_exports_db[export_id] = {
        'export_id': export_id,
        'include_pii': include_pii,
        'created_at': datetime.now().isoformat()
    }
    return jsonify({
        'export_id': export_id,
        'records_exported': min(limit, 50),
        'include_pii': include_pii,
        'warning': 'CDR export performed without authorization'
    })


# ============================================================================
# BILLING & USAGE
# ============================================================================

@telecom_bp.route('/api/v1/telecom/billing/invoices/<invoice_id>')
def telecom_invoice(invoice_id):
    """Invoice lookup - IDOR vulnerability"""
    invoice = telecom_invoices_db.get(invoice_id, {
        'invoice_id': invoice_id,
        'amount': random.randint(50, 500),
        'status': 'open'
    })
    telecom_invoices_db[invoice_id] = invoice
    return jsonify({
        'invoice': invoice,
        'warning': 'Invoice exposed without authorization'
    })


@telecom_bp.route('/api/v1/telecom/billing/adjustments', methods=['PUT'])
def billing_adjustments():
    """Billing adjustment - tamper vulnerability"""
    data = request.get_json() or {}
    adjustment_id = f"ADJ-{uuid.uuid4().hex[:8]}"
    record = {
        'adjustment_id': adjustment_id,
        'account_id': data.get('account_id'),
        'credit': data.get('credit', 0),
        'bypass_approval': data.get('bypass_approval', False),
        'created_at': datetime.now().isoformat()
    }
    telecom_billing_adjustments_db[adjustment_id] = record
    return jsonify({
        'adjustment': record,
        'warning': 'Billing adjustment applied without approval'
    })


@telecom_bp.route('/api/v1/telecom/billing/payment-methods', methods=['POST'])
def payment_methods():
    """Payment method bypass - verification missing"""
    data = request.get_json() or {}
    method_id = f"PM-{uuid.uuid4().hex[:8]}"
    method = {
        'method_id': method_id,
        'account_id': data.get('account_id'),
        'token': data.get('token'),
        'skip_verification': data.get('skip_verification', False)
    }
    telecom_payment_methods_db[method_id] = method
    return jsonify({
        'payment_method': method,
        'warning': 'Payment method added without verification'
    }), 201


@telecom_bp.route('/api/v1/telecom/billing/refunds', methods=['POST'])
def billing_refund():
    """Refund abuse - bypass controls"""
    data = request.get_json() or {}
    refund_id = f"REF-{uuid.uuid4().hex[:8]}"
    refund = {
        'refund_id': refund_id,
        'invoice_id': data.get('invoice_id'),
        'amount': data.get('amount', 0),
        'force_refund': data.get('force_refund', False)
    }
    telecom_refunds_db[refund_id] = refund
    return jsonify({
        'refund': refund,
        'warning': 'Refund processed without authorization'
    }), 201


# ============================================================================
# DEVICE INTEGRITY & ROAMING
# ============================================================================

@telecom_bp.route('/api/v1/telecom/devices/bind', methods=['POST'])
def device_bind():
    """Device binding - SIM swap bypass"""
    data = request.get_json() or {}
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
    return jsonify({
        'binding': record,
        'warning': 'Device binding completed without verification'
    }), 201


@telecom_bp.route('/api/v1/telecom/imei/blacklist', methods=['PUT'])
def imei_blacklist():
    """IMEI blacklist override"""
    data = request.get_json() or {}
    imei = data.get('imei', f'IMEI-{uuid.uuid4().hex[:6]}')
    record = {
        'imei': imei,
        'blacklisted': data.get('blacklisted', True),
        'override_policy': data.get('override_policy', False),
        'updated_at': datetime.now().isoformat()
    }
    telecom_imei_blacklist_db[imei] = record
    return jsonify({
        'imei_record': record,
        'warning': 'IMEI blacklist updated without authorization'
    })


@telecom_bp.route('/api/v1/telecom/roaming/override', methods=['POST'])
def roaming_override():
    """Roaming override - policy bypass"""
    data = request.get_json() or {}
    override_id = f"ROAM-{uuid.uuid4().hex[:8]}"
    record = {
        'override_id': override_id,
        'subscriber_id': data.get('subscriber_id'),
        'region': data.get('region', 'global'),
        'override_policy': data.get('override_policy', False),
        'created_at': datetime.now().isoformat()
    }
    telecom_roaming_overrides_db[override_id] = record
    return jsonify({
        'override': record,
        'warning': 'Roaming override applied without approval'
    }), 201


# ============================================================================
# NUMBER PORTING & SIM INTEGRITY
# ============================================================================

@telecom_bp.route('/api/v1/telecom/porting/requests', methods=['POST'])
def porting_request():
    """Port-out request - bypass PIN"""
    data = request.get_json() or {}
    request_id = f"PORT-{uuid.uuid4().hex[:8]}"
    record = {
        'request_id': request_id,
        'number': data.get('number'),
        'bypass_pin': data.get('bypass_pin', False),
        'status': 'submitted'
    }
    telecom_porting_requests_db[request_id] = record
    return jsonify({
        'request': record,
        'warning': 'Porting request accepted without PIN validation'
    }), 201


@telecom_bp.route('/api/v1/telecom/porting/requests/<request_id>')
def porting_status(request_id):
    """Porting status - IDOR"""
    record = telecom_porting_requests_db.get(request_id, {'request_id': request_id, 'status': 'pending'})
    return jsonify({
        'request': record,
        'warning': 'Porting status exposed without authorization'
    })


@telecom_bp.route('/api/v1/telecom/porting/swap', methods=['PUT'])
def porting_swap():
    """Number swap - tamper vulnerability"""
    data = request.get_json() or {}
    swap_id = f"SWAP-{uuid.uuid4().hex[:8]}"
    record = {
        'swap_id': swap_id,
        'from': data.get('from'),
        'to': data.get('to'),
        'override_checks': data.get('override_checks', False)
    }
    telecom_porting_requests_db[swap_id] = record
    return jsonify({
        'swap': record,
        'warning': 'Number swap completed without checks'
    })


@telecom_bp.route('/api/v1/telecom/porting/export')
def porting_export():
    """Porting export - data exposure"""
    include_pii = request.args.get('include_pii', 'false').lower() == 'true'
    return jsonify({
        'requests': list(telecom_porting_requests_db.values()),
        'include_pii': include_pii,
        'warning': 'Porting data exported without authorization'
    })


# ============================================================================
# INTEGRATIONS & API ACCESS
# ============================================================================

@telecom_bp.route('/api/v1/telecom/api-keys/export')
def api_keys_export():
    """API key export - secret exposure"""
    include_secrets = request.args.get('include_secrets', 'false').lower() == 'true'
    keys = [
        {
            'key_id': key.get('key_id'),
            'label': key.get('label'),
            'secret': key.get('secret') if include_secrets else None
        }
        for key in telecom_api_keys_db.values()
    ]
    return jsonify({
        'keys': keys,
        'include_secrets': include_secrets,
        'warning': 'API keys exported without authorization'
    })


@telecom_bp.route('/api/v1/telecom/integrations/webhooks', methods=['POST'])
def telecom_webhook_register():
    """Webhook registration - SSRF risk"""
    data = request.get_json() or {}
    hook_id = f"HOOK-{uuid.uuid4().hex[:8]}"
    telecom_webhooks_db[hook_id] = {
        'hook_id': hook_id,
        'url': data.get('url'),
        'events': data.get('events', []),
        'bypass_validation': data.get('bypass_validation', False)
    }
    return jsonify({
        'hook_id': hook_id,
        'warning': 'Webhook registered without validation'
    }), 201


@telecom_bp.route('/api/v1/telecom/integrations/cdr/stream', methods=['POST'])
def cdr_stream():
    """CDR stream - replay/bypass risk"""
    data = request.get_json() or {}
    stream_id = data.get('stream_id', f"stream-{uuid.uuid4().hex[:6]}")
    telecom_cdr_streams_db[stream_id] = {
        'stream_id': stream_id,
        'force_enable': data.get('force_enable', False),
        'enabled_at': datetime.now().isoformat()
    }
    return jsonify({
        'stream_id': stream_id,
        'warning': 'CDR stream enabled without authorization'
    })


@telecom_bp.route('/api/v1/telecom/integrations/device-activate', methods=['POST'])
def device_activate():
    """Device activation - bypass controls"""
    data = request.get_json() or {}
    device_id = data.get('device_id')
    telecom_device_activations_db[device_id] = {
        'device_id': device_id,
        'override_checks': data.get('override_checks', False),
        'activated_at': datetime.now().isoformat()
    }
    return jsonify({
        'device_id': device_id,
        'warning': 'Device activated without verification'
    }), 201
