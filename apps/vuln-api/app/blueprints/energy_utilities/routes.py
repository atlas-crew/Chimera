"""
Routes for energy & utilities endpoints.
Demonstrates grid operations, outage response, and metering vulnerabilities.
"""
from starlette.requests import Request
from starlette.responses import JSONResponse
from datetime import datetime
import uuid
import random

from . import energy_utilities_router
from app.models import *
from app.routing import get_json_or_default


# ============================================================================
# GRID OPERATIONS & DISPATCH
# ============================================================================

@energy_utilities_router.route('/api/v1/energy-utilities/grid/dispatch', methods=['POST'])
async def grid_dispatch(request: Request):
    """Grid dispatch override"""
    data = await get_json_or_default(request)
    dispatch_id = f"DISP-{uuid.uuid4().hex[:8]}"
    record = {
        'dispatch_id': dispatch_id,
        'unit_id': data.get('unit_id'),
        'setpoint_mw': data.get('setpoint_mw', 0),
        'override_limits': data.get('override_limits', False),
        'dispatched_at': datetime.now().isoformat()
    }
    energy_dispatch_db[dispatch_id] = record
    return JSONResponse({
        'dispatch': record,
        'warning': 'Dispatch updated without approval'
    }, status_code=201)


@energy_utilities_router.route('/api/v1/energy-utilities/grid/load-shed', methods=['POST'])
async def load_shed(request: Request):
    """Load shedding bypass"""
    data = await get_json_or_default(request)
    event_id = f"SHED-{uuid.uuid4().hex[:8]}"
    record = {
        'event_id': event_id,
        'region': data.get('region'),
        'percent': data.get('percent', 0),
        'bypass_approval': data.get('bypass_approval', False),
        'created_at': datetime.now().isoformat()
    }
    energy_load_shed_db[event_id] = record
    return JSONResponse({
        'event': record,
        'warning': 'Load shed executed without approval'
    }, status_code=201)


@energy_utilities_router.route('/api/v1/energy-utilities/grid/breakers/<breaker_id>', methods=['PUT'])
async def breaker_control(request: Request, breaker_id):
    """Breaker control - IDOR vulnerability"""
    data = await get_json_or_default(request)
    record = energy_breakers_db.get(breaker_id, {'breaker_id': breaker_id})
    record.update({
        'state': data.get('state', 'open'),
        'override_lock': data.get('override_lock', False),
        'updated_at': datetime.now().isoformat()
    })
    energy_breakers_db[breaker_id] = record
    return JSONResponse({
        'breaker': record,
        'warning': 'Breaker control applied without authorization'
    })


@energy_utilities_router.route('/api/v1/energy-utilities/grid/config/export')
async def grid_config_export(request: Request):
    """Grid configuration export"""
    include_sensitive = request.query_params.get('include_sensitive', 'false').lower() == 'true'
    export_id = f"GRID-{uuid.uuid4().hex[:8]}"
    return JSONResponse({
        'export_id': export_id,
        'include_sensitive': include_sensitive,
        'warning': 'Grid config exported without authorization'
    })


# ============================================================================
# DEMAND RESPONSE & TARIFFS
# ============================================================================

@energy_utilities_router.route('/api/v1/energy-utilities/demand-response/dispatch', methods=['POST'])
async def demand_response_dispatch(request: Request):
    """Demand response dispatch override"""
    data = await get_json_or_default(request)
    event_id = f"DR-{uuid.uuid4().hex[:8]}"
    record = {
        'event_id': event_id,
        'region': data.get('region'),
        'percent': data.get('percent', 0),
        'override_limits': data.get('override_limits', False),
        'created_at': datetime.now().isoformat()
    }
    energy_demand_response_db[event_id] = record
    return JSONResponse({
        'event': record,
        'warning': 'Demand response executed without approval'
    }, status_code=201)


@energy_utilities_router.route('/api/v1/energy-utilities/tariffs/override', methods=['PUT'])
async def tariff_override(request: Request):
    """Tariff override - billing tamper"""
    data = await get_json_or_default(request)
    tariff_id = data.get('tariff_id', f"TAR-{uuid.uuid4().hex[:6]}")
    record = {
        'tariff_id': tariff_id,
        'rate_override': data.get('rate_override', 0),
        'bypass_review': data.get('bypass_review', False),
        'updated_at': datetime.now().isoformat()
    }
    energy_tariff_overrides_db[tariff_id] = record
    return JSONResponse({
        'tariff': record,
        'warning': 'Tariff updated without approval'
    })


@energy_utilities_router.route('/api/v1/energy-utilities/der/interconnection/approve', methods=['POST'])
async def der_interconnection_approve(request: Request):
    """DER interconnection approval bypass"""
    data = await get_json_or_default(request)
    interconnection_id = data.get('interconnection_id', f"DER-{uuid.uuid4().hex[:6]}")
    record = {
        'interconnection_id': interconnection_id,
        'system_id': data.get('system_id'),
        'bypass_review': data.get('bypass_review', False),
        'status': 'approved',
        'approved_at': datetime.now().isoformat()
    }
    energy_der_interconnections_db[interconnection_id] = record
    return JSONResponse({
        'interconnection': record,
        'warning': 'DER interconnection approved without validation'
    }, status_code=201)


# ============================================================================
# OUTAGE MANAGEMENT
# ============================================================================

@energy_utilities_router.route('/api/v1/energy-utilities/outages/<outage_id>')
async def outage_status(request: Request, outage_id):
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
    return JSONResponse({
        'outage': outage,
        'warning': 'Outage status exposed without authorization'
    })


@energy_utilities_router.route('/api/v1/energy-utilities/outages/dispatch', methods=['POST'])
async def outage_dispatch(request: Request):
    """Crew dispatch tampering"""
    data = await get_json_or_default(request)
    dispatch_id = f"CREW-{uuid.uuid4().hex[:8]}"
    record = {
        'dispatch_id': dispatch_id,
        'outage_id': data.get('outage_id'),
        'crew_id': data.get('crew_id'),
        'override_priority': data.get('override_priority', False),
        'dispatched_at': datetime.now().isoformat()
    }
    energy_outage_dispatches_db[dispatch_id] = record
    return JSONResponse({
        'dispatch': record,
        'warning': 'Crew dispatched without approval'
    }, status_code=201)


@energy_utilities_router.route('/api/v1/energy-utilities/outages/restore', methods=['PUT'])
async def outage_restore(request: Request):
    """Restoration override"""
    data = await get_json_or_default(request)
    restore_id = f"REST-{uuid.uuid4().hex[:8]}"
    record = {
        'restore_id': restore_id,
        'outage_id': data.get('outage_id'),
        'status': data.get('status', 'restored'),
        'force_restore': data.get('force_restore', False),
        'updated_at': datetime.now().isoformat()
    }
    energy_outage_restores_db[restore_id] = record
    return JSONResponse({
        'restoration': record,
        'warning': 'Restoration updated without validation'
    })


@energy_utilities_router.route('/api/v1/energy-utilities/outages/export')
async def outages_export(request: Request):
    """Outage export - bulk data exposure"""
    include_pii = request.query_params.get('include_pii', 'false').lower() == 'true'
    return JSONResponse({
        'outages': list(energy_outages_db.values()),
        'include_pii': include_pii,
        'warning': 'Outage export performed without authorization'
    })


# ============================================================================
# SMART METERING
# ============================================================================

@energy_utilities_router.route('/api/v1/energy-utilities/meters/<meter_id>/readings')
async def meter_readings(request: Request, meter_id):
    """Meter readings - IDOR"""
    reading = {
        'meter_id': meter_id,
        'kwh': round(random.uniform(100, 10000), 2),
        'timestamp': datetime.now().isoformat()
    }
    energy_meter_readings_db[meter_id] = reading
    return JSONResponse({
        'reading': reading,
        'warning': 'Meter reading exposed without authorization'
    })


@energy_utilities_router.route('/api/v1/energy-utilities/meters/<meter_id>/disconnect', methods=['POST'])
async def meter_disconnect(request: Request, meter_id):
    """Remote disconnect - bypass safety"""
    data = await get_json_or_default(request)
    record = {
        'meter_id': meter_id,
        'reason': data.get('reason'),
        'override_safety': data.get('override_safety', False),
        'disconnected_at': datetime.now().isoformat()
    }
    energy_meter_disconnects_db[meter_id] = record
    return JSONResponse({
        'disconnect': record,
        'warning': 'Disconnect executed without safety checks'
    })


@energy_utilities_router.route('/api/v1/energy-utilities/meters/firmware', methods=['PUT'])
async def meter_firmware_update(request: Request):
    """Firmware update tampering"""
    data = await get_json_or_default(request)
    update_id = f"FW-{uuid.uuid4().hex[:8]}"
    record = {
        'update_id': update_id,
        'version': data.get('version'),
        'bypass_signature': data.get('bypass_signature', False),
        'updated_at': datetime.now().isoformat()
    }
    energy_meter_firmware_db[update_id] = record
    return JSONResponse({
        'firmware_update': record,
        'warning': 'Firmware updated without signature validation'
    })


@energy_utilities_router.route('/api/v1/energy-utilities/meters/export')
async def meters_export(request: Request):
    """Meter export - data exposure"""
    include_pii = request.query_params.get('include_pii', 'false').lower() == 'true'
    return JSONResponse({
        'meters': list(energy_meter_readings_db.values()),
        'include_pii': include_pii,
        'warning': 'Meter data exported without authorization'
    })


# ============================================================================
# BILLING & CUSTOMER OPERATIONS
# ============================================================================

@energy_utilities_router.route('/api/v1/energy-utilities/billing/adjustments', methods=['PUT'])
async def energy_billing_adjustments(request: Request):
    """Billing adjustment tamper"""
    data = await get_json_or_default(request)
    adjustment_id = f"ADJ-{uuid.uuid4().hex[:8]}"
    record = {
        'adjustment_id': adjustment_id,
        'account_id': data.get('account_id'),
        'credit': data.get('credit', 0),
        'bypass_approval': data.get('bypass_approval', False)
    }
    energy_billing_adjustments_db[adjustment_id] = record
    return JSONResponse({
        'adjustment': record,
        'warning': 'Billing adjustment applied without approval'
    })


@energy_utilities_router.route('/api/v1/energy-utilities/billing/autopay', methods=['PUT'])
async def energy_autopay(request: Request):
    """Autopay bypass"""
    data = await get_json_or_default(request)
    record = {
        'account_id': data.get('account_id'),
        'enabled': data.get('enabled', True),
        'bypass_mfa': data.get('bypass_mfa', False),
        'updated_at': datetime.now().isoformat()
    }
    energy_autopay_db[data.get('account_id', 'unknown')] = record
    return JSONResponse({
        'autopay': record,
        'warning': 'Autopay updated without MFA'
    })


@energy_utilities_router.route('/api/v1/energy-utilities/billing/refunds', methods=['POST'])
async def energy_refund(request: Request):
    """Refund abuse"""
    data = await get_json_or_default(request)
    refund_id = f"REF-{uuid.uuid4().hex[:8]}"
    record = {
        'refund_id': refund_id,
        'invoice_id': data.get('invoice_id'),
        'amount': data.get('amount', 0),
        'force_refund': data.get('force_refund', False)
    }
    energy_refunds_db[refund_id] = record
    return JSONResponse({
        'refund': record,
        'warning': 'Refund processed without validation'
    }, status_code=201)


@energy_utilities_router.route('/api/v1/energy-utilities/customers/<customer_id>')
async def energy_customer(request: Request, customer_id):
    """Customer lookup - IDOR"""
    customer = energy_customers_db.get(customer_id, {
        'customer_id': customer_id,
        'name': f'Customer {random.randint(100, 999)}',
        'status': 'active'
    })
    energy_customers_db[customer_id] = customer
    return JSONResponse({
        'customer': customer,
        'warning': 'Customer record exposed without authorization'
    })


# ============================================================================
# ASSET INTEGRITY & SCADA
# ============================================================================

@energy_utilities_router.route('/api/v1/energy-utilities/scada/config/export')
async def scada_config_export(request: Request):
    """SCADA config export - data exposure"""
    include_sensitive = request.query_params.get('include_sensitive', 'false').lower() == 'true'
    return JSONResponse({
        'include_sensitive': include_sensitive,
        'warning': 'SCADA config exported without authorization'
    })


@energy_utilities_router.route('/api/v1/energy-utilities/assets/maintenance', methods=['PUT'])
async def asset_maintenance(request: Request):
    """Maintenance override"""
    data = await get_json_or_default(request)
    record = {
        'asset_id': data.get('asset_id'),
        'skip_review': data.get('skip_review', False),
        'updated_at': datetime.now().isoformat()
    }
    energy_asset_maintenance_db[data.get('asset_id', 'unknown')] = record
    return JSONResponse({
        'maintenance': record,
        'warning': 'Maintenance updated without review'
    })


@energy_utilities_router.route('/api/v1/energy-utilities/assets/calibration', methods=['POST'])
async def asset_calibration(request: Request):
    """Sensor calibration tamper"""
    data = await get_json_or_default(request)
    calibration_id = f"CAL-{uuid.uuid4().hex[:8]}"
    record = {
        'calibration_id': calibration_id,
        'asset_id': data.get('asset_id'),
        'calibration': data.get('calibration'),
        'override_limits': data.get('override_limits', False)
    }
    energy_asset_calibration_db[calibration_id] = record
    return JSONResponse({
        'calibration': record,
        'warning': 'Calibration applied without safeguards'
    }, status_code=201)


@energy_utilities_router.route('/api/v1/energy-utilities/assets/<asset_id>')
async def asset_registry(request: Request, asset_id):
    """Asset registry - IDOR"""
    asset = energy_assets_db.get(asset_id, {
        'asset_id': asset_id,
        'type': random.choice(['transformer', 'substation', 'feeder']),
        'status': 'active'
    })
    energy_assets_db[asset_id] = asset
    return JSONResponse({
        'asset': asset,
        'warning': 'Asset data exposed without authorization'
    })
