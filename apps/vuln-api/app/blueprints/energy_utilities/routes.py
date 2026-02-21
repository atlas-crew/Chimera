"""
Routes for energy & utilities endpoints.
Demonstrates grid operations, outage response, and metering vulnerabilities.
"""

from flask import request, jsonify
from datetime import datetime
import uuid
import random

from . import energy_utilities_bp
from app.models import *


# ============================================================================
# GRID OPERATIONS & DISPATCH
# ============================================================================

@energy_utilities_bp.route('/api/v1/energy-utilities/grid/dispatch', methods=['POST'])
def grid_dispatch():
    """Grid dispatch override"""
    data = request.get_json() or {}
    dispatch_id = f"DISP-{uuid.uuid4().hex[:8]}"
    record = {
        'dispatch_id': dispatch_id,
        'unit_id': data.get('unit_id'),
        'setpoint_mw': data.get('setpoint_mw', 0),
        'override_limits': data.get('override_limits', False),
        'dispatched_at': datetime.now().isoformat()
    }
    energy_dispatch_db[dispatch_id] = record
    return jsonify({
        'dispatch': record,
        'warning': 'Dispatch updated without approval'
    }), 201


@energy_utilities_bp.route('/api/v1/energy-utilities/grid/load-shed', methods=['POST'])
def load_shed():
    """Load shedding bypass"""
    data = request.get_json() or {}
    event_id = f"SHED-{uuid.uuid4().hex[:8]}"
    record = {
        'event_id': event_id,
        'region': data.get('region'),
        'percent': data.get('percent', 0),
        'bypass_approval': data.get('bypass_approval', False),
        'created_at': datetime.now().isoformat()
    }
    energy_load_shed_db[event_id] = record
    return jsonify({
        'event': record,
        'warning': 'Load shed executed without approval'
    }), 201


@energy_utilities_bp.route('/api/v1/energy-utilities/grid/breakers/<breaker_id>', methods=['PUT'])
def breaker_control(breaker_id):
    """Breaker control - IDOR vulnerability"""
    data = request.get_json() or {}
    record = energy_breakers_db.get(breaker_id, {'breaker_id': breaker_id})
    record.update({
        'state': data.get('state', 'open'),
        'override_lock': data.get('override_lock', False),
        'updated_at': datetime.now().isoformat()
    })
    energy_breakers_db[breaker_id] = record
    return jsonify({
        'breaker': record,
        'warning': 'Breaker control applied without authorization'
    })


@energy_utilities_bp.route('/api/v1/energy-utilities/grid/config/export')
def grid_config_export():
    """Grid configuration export"""
    include_sensitive = request.args.get('include_sensitive', 'false').lower() == 'true'
    export_id = f"GRID-{uuid.uuid4().hex[:8]}"
    return jsonify({
        'export_id': export_id,
        'include_sensitive': include_sensitive,
        'warning': 'Grid config exported without authorization'
    })


# ============================================================================
# DEMAND RESPONSE & TARIFFS
# ============================================================================

@energy_utilities_bp.route('/api/v1/energy-utilities/demand-response/dispatch', methods=['POST'])
def demand_response_dispatch():
    """Demand response dispatch override"""
    data = request.get_json() or {}
    event_id = f"DR-{uuid.uuid4().hex[:8]}"
    record = {
        'event_id': event_id,
        'region': data.get('region'),
        'percent': data.get('percent', 0),
        'override_limits': data.get('override_limits', False),
        'created_at': datetime.now().isoformat()
    }
    energy_demand_response_db[event_id] = record
    return jsonify({
        'event': record,
        'warning': 'Demand response executed without approval'
    }), 201


@energy_utilities_bp.route('/api/v1/energy-utilities/tariffs/override', methods=['PUT'])
def tariff_override():
    """Tariff override - billing tamper"""
    data = request.get_json() or {}
    tariff_id = data.get('tariff_id', f"TAR-{uuid.uuid4().hex[:6]}")
    record = {
        'tariff_id': tariff_id,
        'rate_override': data.get('rate_override', 0),
        'bypass_review': data.get('bypass_review', False),
        'updated_at': datetime.now().isoformat()
    }
    energy_tariff_overrides_db[tariff_id] = record
    return jsonify({
        'tariff': record,
        'warning': 'Tariff updated without approval'
    })


@energy_utilities_bp.route('/api/v1/energy-utilities/der/interconnection/approve', methods=['POST'])
def der_interconnection_approve():
    """DER interconnection approval bypass"""
    data = request.get_json() or {}
    interconnection_id = data.get('interconnection_id', f"DER-{uuid.uuid4().hex[:6]}")
    record = {
        'interconnection_id': interconnection_id,
        'system_id': data.get('system_id'),
        'bypass_review': data.get('bypass_review', False),
        'status': 'approved',
        'approved_at': datetime.now().isoformat()
    }
    energy_der_interconnections_db[interconnection_id] = record
    return jsonify({
        'interconnection': record,
        'warning': 'DER interconnection approved without validation'
    }), 201


# ============================================================================
# OUTAGE MANAGEMENT
# ============================================================================

@energy_utilities_bp.route('/api/v1/energy-utilities/outages/<outage_id>')
def outage_status(outage_id):
    """Outage status - IDOR vulnerability"""
    outage = energy_outages_db.get(outage_id)
    if not outage:
        outage = {
            'outage_id': outage_id,
            'status': random.choice(['reported', 'in_progress', 'restored']),
            'customers_impacted': random.randint(100, 5000),
            'region': random.choice(['north', 'south', 'east', 'west'])
        }
        energy_outages_db[outage_id] = outage
    return jsonify({
        'outage': outage,
        'warning': 'Outage status exposed without authorization'
    })


@energy_utilities_bp.route('/api/v1/energy-utilities/outages/dispatch', methods=['POST'])
def outage_dispatch():
    """Crew dispatch tampering"""
    data = request.get_json() or {}
    dispatch_id = f"CREW-{uuid.uuid4().hex[:8]}"
    record = {
        'dispatch_id': dispatch_id,
        'outage_id': data.get('outage_id'),
        'crew_id': data.get('crew_id'),
        'override_priority': data.get('override_priority', False),
        'dispatched_at': datetime.now().isoformat()
    }
    energy_outage_dispatches_db[dispatch_id] = record
    return jsonify({
        'dispatch': record,
        'warning': 'Crew dispatched without approval'
    }), 201


@energy_utilities_bp.route('/api/v1/energy-utilities/outages/restore', methods=['PUT'])
def outage_restore():
    """Restoration override"""
    data = request.get_json() or {}
    restore_id = f"REST-{uuid.uuid4().hex[:8]}"
    record = {
        'restore_id': restore_id,
        'outage_id': data.get('outage_id'),
        'status': data.get('status', 'restored'),
        'force_restore': data.get('force_restore', False),
        'updated_at': datetime.now().isoformat()
    }
    energy_outage_restores_db[restore_id] = record
    return jsonify({
        'restoration': record,
        'warning': 'Restoration updated without validation'
    })


@energy_utilities_bp.route('/api/v1/energy-utilities/outages/export')
def outages_export():
    """Outage export - bulk data exposure"""
    include_pii = request.args.get('include_pii', 'false').lower() == 'true'
    return jsonify({
        'outages': list(energy_outages_db.values()),
        'include_pii': include_pii,
        'warning': 'Outage export performed without authorization'
    })


# ============================================================================
# SMART METERING
# ============================================================================

@energy_utilities_bp.route('/api/v1/energy-utilities/meters/<meter_id>/readings')
def meter_readings(meter_id):
    """Meter readings - IDOR"""
    reading = {
        'meter_id': meter_id,
        'kwh': round(random.uniform(100, 10000), 2),
        'timestamp': datetime.now().isoformat()
    }
    energy_meter_readings_db[meter_id] = reading
    return jsonify({
        'reading': reading,
        'warning': 'Meter reading exposed without authorization'
    })


@energy_utilities_bp.route('/api/v1/energy-utilities/meters/<meter_id>/disconnect', methods=['POST'])
def meter_disconnect(meter_id):
    """Remote disconnect - bypass safety"""
    data = request.get_json() or {}
    record = {
        'meter_id': meter_id,
        'reason': data.get('reason'),
        'override_safety': data.get('override_safety', False),
        'disconnected_at': datetime.now().isoformat()
    }
    energy_meter_disconnects_db[meter_id] = record
    return jsonify({
        'disconnect': record,
        'warning': 'Disconnect executed without safety checks'
    })


@energy_utilities_bp.route('/api/v1/energy-utilities/meters/firmware', methods=['PUT'])
def meter_firmware_update():
    """Firmware update tampering"""
    data = request.get_json() or {}
    update_id = f"FW-{uuid.uuid4().hex[:8]}"
    record = {
        'update_id': update_id,
        'version': data.get('version'),
        'bypass_signature': data.get('bypass_signature', False),
        'updated_at': datetime.now().isoformat()
    }
    energy_meter_firmware_db[update_id] = record
    return jsonify({
        'firmware_update': record,
        'warning': 'Firmware updated without signature validation'
    })


@energy_utilities_bp.route('/api/v1/energy-utilities/meters/export')
def meters_export():
    """Meter export - data exposure"""
    include_pii = request.args.get('include_pii', 'false').lower() == 'true'
    return jsonify({
        'meters': list(energy_meter_readings_db.values()),
        'include_pii': include_pii,
        'warning': 'Meter data exported without authorization'
    })


# ============================================================================
# BILLING & CUSTOMER OPERATIONS
# ============================================================================

@energy_utilities_bp.route('/api/v1/energy-utilities/billing/adjustments', methods=['PUT'])
def energy_billing_adjustments():
    """Billing adjustment tamper"""
    data = request.get_json() or {}
    adjustment_id = f"ADJ-{uuid.uuid4().hex[:8]}"
    record = {
        'adjustment_id': adjustment_id,
        'account_id': data.get('account_id'),
        'credit': data.get('credit', 0),
        'bypass_approval': data.get('bypass_approval', False)
    }
    energy_billing_adjustments_db[adjustment_id] = record
    return jsonify({
        'adjustment': record,
        'warning': 'Billing adjustment applied without approval'
    })


@energy_utilities_bp.route('/api/v1/energy-utilities/billing/autopay', methods=['PUT'])
def energy_autopay():
    """Autopay bypass"""
    data = request.get_json() or {}
    record = {
        'account_id': data.get('account_id'),
        'enabled': data.get('enabled', True),
        'bypass_mfa': data.get('bypass_mfa', False),
        'updated_at': datetime.now().isoformat()
    }
    energy_autopay_db[data.get('account_id', 'unknown')] = record
    return jsonify({
        'autopay': record,
        'warning': 'Autopay updated without MFA'
    })


@energy_utilities_bp.route('/api/v1/energy-utilities/billing/refunds', methods=['POST'])
def energy_refund():
    """Refund abuse"""
    data = request.get_json() or {}
    refund_id = f"REF-{uuid.uuid4().hex[:8]}"
    record = {
        'refund_id': refund_id,
        'invoice_id': data.get('invoice_id'),
        'amount': data.get('amount', 0),
        'force_refund': data.get('force_refund', False)
    }
    energy_refunds_db[refund_id] = record
    return jsonify({
        'refund': record,
        'warning': 'Refund processed without validation'
    }), 201


@energy_utilities_bp.route('/api/v1/energy-utilities/customers/<customer_id>')
def energy_customer(customer_id):
    """Customer lookup - IDOR"""
    customer = energy_customers_db.get(customer_id, {
        'customer_id': customer_id,
        'name': f'Customer {random.randint(100, 999)}',
        'status': 'active'
    })
    energy_customers_db[customer_id] = customer
    return jsonify({
        'customer': customer,
        'warning': 'Customer record exposed without authorization'
    })


# ============================================================================
# ASSET INTEGRITY & SCADA
# ============================================================================

@energy_utilities_bp.route('/api/v1/energy-utilities/scada/config/export')
def scada_config_export():
    """SCADA config export - data exposure"""
    include_sensitive = request.args.get('include_sensitive', 'false').lower() == 'true'
    return jsonify({
        'include_sensitive': include_sensitive,
        'warning': 'SCADA config exported without authorization'
    })


@energy_utilities_bp.route('/api/v1/energy-utilities/assets/maintenance', methods=['PUT'])
def asset_maintenance():
    """Maintenance override"""
    data = request.get_json() or {}
    record = {
        'asset_id': data.get('asset_id'),
        'skip_review': data.get('skip_review', False),
        'updated_at': datetime.now().isoformat()
    }
    energy_asset_maintenance_db[data.get('asset_id', 'unknown')] = record
    return jsonify({
        'maintenance': record,
        'warning': 'Maintenance updated without review'
    })


@energy_utilities_bp.route('/api/v1/energy-utilities/assets/calibration', methods=['POST'])
def asset_calibration():
    """Sensor calibration tamper"""
    data = request.get_json() or {}
    calibration_id = f"CAL-{uuid.uuid4().hex[:8]}"
    record = {
        'calibration_id': calibration_id,
        'asset_id': data.get('asset_id'),
        'calibration': data.get('calibration'),
        'override_limits': data.get('override_limits', False)
    }
    energy_asset_calibration_db[calibration_id] = record
    return jsonify({
        'calibration': record,
        'warning': 'Calibration applied without safeguards'
    }), 201


@energy_utilities_bp.route('/api/v1/energy-utilities/assets/<asset_id>')
def asset_registry(asset_id):
    """Asset registry - IDOR"""
    asset = energy_assets_db.get(asset_id, {
        'asset_id': asset_id,
        'type': random.choice(['transformer', 'substation', 'feeder']),
        'status': 'active'
    })
    energy_assets_db[asset_id] = asset
    return jsonify({
        'asset': asset,
        'warning': 'Asset data exposed without authorization'
    })
