"""
Routes for insurance endpoints.
Demonstrates claims fraud, underwriting tampering, and policy abuse vulnerabilities.
"""

from flask import request, jsonify
from datetime import datetime
import uuid
import random

from . import insurance_bp
from app.models import *


# ============================================================================
# CLAIMS PORTAL & SUBMISSION
# ============================================================================

@insurance_bp.route('/claims/portal')
def claims_portal():
    """Claims portal entry point"""
    return jsonify({
        'service': ' Insurance Claims Portal',
        'version': '3.2.1',
        'supported_claim_types': ['auto', 'home', 'life', 'health'],
        'max_claim_amount': 1000000
    })


@insurance_bp.route('/api/claims/submit', methods=['POST'])
def claims_submit():
    """Claims submission endpoint"""
    data = request.get_json() or {}
    claim_id = f"CLM-{uuid.uuid4().hex[:8]}"

    claim = {
        'claim_id': claim_id,
        'policy_number': data.get('policy_number'),
        'claim_type': data.get('claim_type', 'auto'),
        'claim_amount': data.get('claim_amount', 0),
        'description': data.get('description', ''),
        'submitted_at': datetime.now().isoformat(),
        'status': 'submitted',
        'fraud_score': data.get('fraud_score', random.uniform(0.1, 0.9)),
        'override_checks': data.get('override_checks', False)
    }

    claims_db[claim_id] = claim

    return jsonify({
        'status': 'submitted',
        'claim': claim,
        'warning': 'Claim accepted without validation of policy ownership'
    }), 201


@insurance_bp.route('/api/claims/history')
def claims_history():
    """Claims history endpoint"""
    policy_number = request.args.get('policy_number', '')

    claims = []
    for claim in claims_db.values():
        if not policy_number or claim.get('policy_number') == policy_number:
            claims.append(claim)

    return jsonify({
        'policy_number': policy_number,
        'claims': claims,
        'count': len(claims),
        'warning': 'Claims history returned without access control'
    })


@insurance_bp.route('/api/claims/<claim_id>/status', methods=['PUT'])
def claims_status_update(claim_id):
    """Update the status of a claim"""
    data = request.get_json() or {}
    new_status = data.get('status', 'under_review')
    adjuster_id = data.get('adjuster_id', 'ADJ-UNKNOWN')

    claim = claims_db.get(claim_id, {'claim_id': claim_id})
    previous_status = claim.get('status', 'unknown')
    claim['status'] = new_status
    claim['adjuster'] = adjuster_id
    claim['updated_at'] = datetime.now().isoformat()
    claims_db[claim_id] = claim

    return jsonify({
        'claim_id': claim_id,
        'previous_status': previous_status,
        'new_status': new_status,
        'adjuster_id': adjuster_id,
        'warning': 'Status updated without authorization check'
    })


@insurance_bp.route('/api/claims/duplicate', methods=['POST'])
def claims_duplicate():
    """Duplicate an existing claim - fraud scenario"""
    data = request.get_json() or {}
    source_claim_id = data.get('claim_id')

    source_claim = claims_db.get(source_claim_id, {})
    duplicate_id = f"CLM-{uuid.uuid4().hex[:8]}"

    duplicate = {
        **source_claim,
        'claim_id': duplicate_id,
        'status': 'submitted',
        'submitted_at': datetime.now().isoformat(),
        'fraud_score': random.uniform(0.7, 0.95)
    }

    claims_db[duplicate_id] = duplicate

    return jsonify({
        'duplicated_from': source_claim_id,
        'duplicate_claim': duplicate,
        'warning': 'Claim duplicated without fraud controls'
    })


@insurance_bp.route('/api/claims/photos/upload', methods=['POST'])
def claims_photos_upload():
    """Upload photographic evidence for claims"""
    data = request.get_json() or {}
    claim_id = data.get('claim_id')
    photos = data.get('photos', [])

    evidence_id = f"EVID-{uuid.uuid4().hex[:8]}"
    claims_evidence_db[evidence_id] = {
        'evidence_id': evidence_id,
        'claim_id': claim_id,
        'photos': photos,
        'uploaded_at': datetime.now().isoformat(),
        'validated': False
    }

    return jsonify({
        'status': 'uploaded',
        'evidence_id': evidence_id,
        'photo_count': len(photos),
        'warning': 'File type validation bypassed'
    })


@insurance_bp.route('/api/claims/bulk-export', methods=['POST'])
def claims_bulk_export():
    """Bulk export claims data - sensitive operation"""
    admin_token = request.headers.get('X-Claims-Admin')
    if admin_token != 'CLAIMS-EXPORT-KEY':
        return jsonify({'error': 'Claims admin authorization required'}), 403

    export = list(claims_db.values())
    return jsonify({
        'export_id': f"EXPORT-{uuid.uuid4().hex[:8]}",
        'claims': export,
        'count': len(export)
    })


@insurance_bp.route('/api/claims/fraud-indicators')
def claims_fraud_indicators():
    """Expose aggregated fraud indicators"""
    indicators = []
    for claim in claims_db.values():
        indicators.append({
            'claim_id': claim.get('claim_id'),
            'policy_number': claim.get('policy_number'),
            'fraud_score': claim.get('fraud_score', random.uniform(0.1, 0.9)),
            'indicators': claim.get('fraud_indicators', []),
            'last_updated': claim.get('updated_at', claim.get('submitted_at'))
        })

    return jsonify({
        'indicators': indicators,
        'count': len(indicators),
        'warning': 'Fraud indicators exposed without access controls'
    })


@insurance_bp.route('/api/claims/expedite', methods=['POST'])
def claims_expedite():
    """Expedite a claim processing"""
    data = request.get_json() or {}
    claim_id = data.get('claim_id')
    justification = data.get('justification', '')

    claim = claims_db.get(claim_id, {'claim_id': claim_id})
    claim['status'] = 'expedited'
    claim['expedite_reason'] = justification
    claim['expedited_at'] = datetime.now().isoformat()
    claims_db[claim_id] = claim

    return jsonify({
        'claim_id': claim_id,
        'status': claim['status'],
        'justification': justification,
        'warning': 'Expedite applied without review'
    })


@insurance_bp.route('/api/claims/amounts/inflate', methods=['PUT'])
def claims_amounts_inflate():
    """Artificially inflate claim amounts - abuse scenario"""
    data = request.get_json() or {}
    claim_id = data.get('claim_id')
    multiplier = float(data.get('multiplier', 1))

    claim = claims_db.get(claim_id)
    if not claim:
        return jsonify({'error': 'Claim not found'}), 404

    original_amount = float(claim.get('claim_amount', 0))
    claim['claim_amount'] = original_amount * multiplier
    claim['adjusted_at'] = datetime.now().isoformat()

    return jsonify({
        'claim_id': claim_id,
        'original_amount': original_amount,
        'new_amount': claim['claim_amount'],
        'multiplier': multiplier,
        'warning': 'Amount modified without approval'
    })


# ============================================================================
# POLICIES & UNDERWRITING
# ============================================================================

@insurance_bp.route('/api/policies/<policy_id>/limits', methods=['PUT'])
def policy_limits(policy_id):
    """Policy limits modification - administrative function"""
    data = request.get_json() or {}
    new_limit = data.get('coverage_limit', 0)

    policy = policies_db.get(policy_id, {'policy_id': policy_id, 'coverage_limit': 0, 'overrides': []})
    old_limit = policy.get('coverage_limit', 0)
    policy['coverage_limit'] = new_limit
    policy.setdefault('overrides', []).append({
        'type': 'limit_update',
        'value': new_limit,
        'timestamp': datetime.now().isoformat()
    })
    policies_db[policy_id] = policy

    return jsonify({
        'policy_id': policy_id,
        'previous_limit': old_limit,
        'new_limit': new_limit,
        'warning': 'Coverage limit updated without authorization'
    })


@insurance_bp.route('/api/policies/search')
def policies_search():
    """Policy search endpoint"""
    policy_type = request.args.get('type')
    status = request.args.get('status')

    policies = []
    for policy in policies_db.values():
        if policy_type and policy.get('type') != policy_type:
            continue
        if status and policy.get('status') != status:
            continue
        policies.append(policy)

    return jsonify({
        'policies': policies,
        'count': len(policies),
        'warning': 'Policy search returned without access control'
    })


@insurance_bp.route('/api/policies/coverage-limits', methods=['PUT'])
def policies_coverage_limits():
    """Policy coverage modification endpoint"""
    data = request.get_json() or {}
    policy_id = data.get('policy_id')
    new_limit = data.get('coverage_limit')
    justification = data.get('justification', '')

    policy = policies_db.get(policy_id, {'policy_id': policy_id, 'coverage_limit': 0, 'overrides': []})
    old_limit = policy.get('coverage_limit', 0)
    policy['coverage_limit'] = new_limit
    policy.setdefault('overrides', []).append({
        'type': 'coverage_limit',
        'value': new_limit,
        'justification': justification,
        'timestamp': datetime.now().isoformat()
    })
    policies_db[policy_id] = policy

    return jsonify({
        'policy_id': policy_id,
        'previous_limit': old_limit,
        'new_limit': new_limit,
        'justification': justification,
        'warning': 'Coverage limit updated without review'
    })


@insurance_bp.route('/api/policies/pricing-models')
def policies_pricing_models():
    """Expose pricing models for policies"""
    models = [
        {
            'model_id': 'PRICING-AUTO-2025',
            'policy_type': 'auto',
            'version': '2025.1',
            'factors': ['driver_age', 'vehicle_value', 'claims_history'],
            'status': 'active'
        },
        {
            'model_id': 'PRICING-HOME-2025',
            'policy_type': 'home',
            'version': '2025.3',
            'factors': ['zip_code', 'construction_type', 'weather_risk'],
            'status': 'active'
        }
    ]

    return jsonify({
        'models': models,
        'count': len(models)
    })


@insurance_bp.route('/api/policies/backdoor', methods=['POST'])
def policies_backdoor():
    """Policy backdoor access - administrative bypass"""
    data = request.get_json() or {}
    policy_id = data.get('policy_id')
    access_token = data.get('access_token', '')

    policy = policies_db.get(policy_id, {'policy_id': policy_id, 'status': 'active'})

    bypassed = access_token == 'BACKDOOR-KEY' or 'override' in access_token

    return jsonify({
        'policy': policy,
        'backdoor_used': bypassed,
        'warning': 'Backdoor access granted without validation'
    })


@insurance_bp.route('/api/policies/bulk-modify', methods=['POST'])
def policies_bulk_modify():
    """Bulk modify policies - mass manipulation vector"""
    data = request.get_json() or {}
    policy_ids = data.get('policy_ids', [])
    modifications = data.get('modifications', {})

    updated = []
    for policy_id in policy_ids:
        policy = policies_db.get(policy_id, {'policy_id': policy_id})
        policy.update(modifications)
        policies_db[policy_id] = policy
        updated.append(policy)

    return jsonify({
        'updated': updated,
        'count': len(updated),
        'warning': 'Bulk updates applied without review'
    })


@insurance_bp.route('/api/underwriting/risk-assessment', methods=['POST'])
def risk_assessment():
    """Risk assessment endpoint"""
    data = request.get_json() or {}
    policy_id = data.get('policy_id')
    override_score = data.get('override_score')

    risk_score = override_score if override_score is not None else random.uniform(0.1, 0.9)

    return jsonify({
        'policy_id': policy_id,
        'risk_score': risk_score,
        'override_used': override_score is not None,
        'warning': 'Risk assessment accepted without model validation'
    })


@insurance_bp.route('/api/underwriting/rules')
def underwriting_rules():
    """Underwriting rules enumeration"""
    return jsonify({
        'rules': underwriting_rules_db,
        'total_rules': len(underwriting_rules_db),
        'policy_types_impacted': ['auto', 'home', 'life']
    })


@insurance_bp.route('/api/underwriting/override', methods=['POST'])
def underwriting_override():
    """Override underwriting decisions"""
    data = request.get_json() or {}
    policy_id = data.get('policy_id')
    rule_id = data.get('rule_id')
    reason = data.get('reason', 'manual_override')

    policy = policies_db.get(policy_id, {'policy_id': policy_id, 'overrides': []})
    policy.setdefault('overrides', []).append({
        'rule_id': rule_id,
        'reason': reason,
        'timestamp': datetime.now().isoformat()
    })
    policies_db[policy_id] = policy

    return jsonify({
        'policy_id': policy_id,
        'rule_id': rule_id,
        'override_reason': reason,
        'warning': 'Underwriting override accepted'
    })


@insurance_bp.route('/api/underwriting/export')
def underwriting_export():
    """Export underwriting data - data exfiltration vector"""
    format_type = request.args.get('format', 'json')
    policy_type = request.args.get('policy_type', 'all')

    payload = {
        'rules': underwriting_rules_db,
        'policies': list(policies_db.values())
    }

    if format_type == 'sql_dump':
        return jsonify({
            'format': format_type,
            'dump': f"INSERT INTO underwriting_rules VALUES ({len(underwriting_rules_db)} rows);",
            'policy_type': policy_type
        })

    return jsonify({
        'format': format_type,
        'policy_type': policy_type,
        'data': payload
    })


@insurance_bp.route('/api/actuarial/models/modify', methods=['PUT'])
def actuarial_models_modify():
    """Modify actuarial models - tampering scenario"""
    data = request.get_json() or {}
    model_id = data.get('model_id')
    new_version = data.get('version')
    adjustment = data.get('adjustment_factor', 1.0)

    model = actuarial_models_db.get(model_id, {'model_id': model_id})
    model['version'] = new_version
    model['adjustment_factor'] = adjustment
    model['modified_at'] = datetime.now().isoformat()
    actuarial_models_db[model_id] = model

    return jsonify({
        'model': model,
        'warning': 'Actuarial model modified without approval'
    })


@insurance_bp.route('/api/risk/factors')
def risk_factors():
    """Risk factors enumeration endpoint"""
    return jsonify({
        'risk_factors': [
            {'factor_id': 'RF-001', 'name': 'age', 'weight': 0.15, 'category': 'demographic'},
            {'factor_id': 'RF-002', 'name': 'credit_score', 'weight': 0.25, 'category': 'financial'},
            {'factor_id': 'RF-003', 'name': 'location', 'weight': 0.20, 'category': 'geographic'},
            {'factor_id': 'RF-004', 'name': 'claims_history', 'weight': 0.30, 'category': 'behavioral'},
            {'factor_id': 'RF-005', 'name': 'occupation', 'weight': 0.10, 'category': 'demographic'}
        ],
        'total_factors': 5,
        'version': '2025.1',
        'sensitivity': 'confidential'
    })


@insurance_bp.route('/api/risk/scores/manipulate', methods=['PUT'])
def risk_scores_manipulate():
    """Manipulate risk scores - fraud vector"""
    data = request.get_json() or {}
    policy_id = data.get('policy_id')
    new_score = data.get('risk_score', 0.5)
    reason = data.get('reason', 'manual_adjustment')

    policy = policies_db.get(policy_id, {'policy_id': policy_id})
    policy['risk_score'] = new_score
    policy['risk_reason'] = reason
    policies_db[policy_id] = policy

    return jsonify({
        'policy_id': policy_id,
        'risk_score': new_score,
        'reason': reason,
        'warning': 'Risk score updated without validation'
    })


@insurance_bp.route('/api/premiums/calculate', methods=['POST'])
def premiums_calculate():
    """Premium calculation endpoint"""
    data = request.get_json() or {}
    policy_type = data.get('policy_type', 'auto')
    base_premium = float(data.get('base_premium', 1000))
    risk_score = float(data.get('risk_score', 0.5))
    discounts = data.get('discounts', [])

    premium = base_premium * (1 + risk_score)
    if discounts:
        premium = premium * max(0.0, 1 - (0.05 * len(discounts)))

    return jsonify({
        'policy_type': policy_type,
        'base_premium': base_premium,
        'risk_score': risk_score,
        'discounts': discounts,
        'estimated_premium': round(premium, 2),
        'warning': 'Premium calculated without validation of discounts'
    })


# ============================================================================
# INSURANCE V1 ENDPOINTS (GAUNTLET TARGETS)
# ============================================================================

@insurance_bp.route('/api/v1/insurance/claims/<claim_id>')
def v1_claim_details(claim_id):
    """Claim details - IDOR"""
    claim = claims_db.get(claim_id, {'claim_id': claim_id})
    return jsonify({
        'claim': claim,
        'warning': 'Claim data exposed without authorization'
    })


@insurance_bp.route('/api/v1/insurance/claims/search')
def v1_claims_search():
    """Claims search - SQLi vector"""
    query = request.args.get('q', '')
    if any(token in query.lower() for token in ['union', 'select', '--', ';']):
        return jsonify({
            'vulnerability': 'SQL_INJECTION_DETECTED',
            'query': query,
            'exposed_tables': ['claims', 'policies', 'customers']
        })
    return jsonify({
        'query': query,
        'results': list(claims_db.values())[:10]
    })


@insurance_bp.route('/api/v1/insurance/claims/<claim_id>/payout', methods=['PUT'])
def v1_claim_payout(claim_id):
    """Payout manipulation"""
    data = request.get_json() or {}
    claim = claims_db.get(claim_id, {'claim_id': claim_id})
    claim['payout_amount'] = data.get('amount', 0)
    claim['override_limits'] = data.get('override_limits', False)
    claims_db[claim_id] = claim
    return jsonify({
        'claim': claim,
        'warning': 'Payout updated without approval'
    })


@insurance_bp.route('/api/v1/insurance/claims/export')
def v1_claims_export():
    """Claims export - data exfiltration"""
    include_pii = request.args.get('include_pii', 'false').lower() == 'true'
    claims = list(claims_db.values())
    return jsonify({
        'claims': claims,
        'include_pii': include_pii,
        'warning': 'Claims exported without authorization'
    })


@insurance_bp.route('/api/v1/insurance/claims/evidence/upload', methods=['POST'])
def v1_claims_evidence_upload():
    """Evidence upload - file validation bypass"""
    data = request.get_json() or {}
    evidence_id = f"EVID-{uuid.uuid4().hex[:8]}"
    claims_evidence_db[evidence_id] = {
        'evidence_id': evidence_id,
        'claim_id': data.get('claim_id'),
        'file_name': data.get('file_name'),
        'bypass_scanner': data.get('bypass_scanner', False)
    }
    return jsonify({
        'evidence_id': evidence_id,
        'warning': 'Evidence uploaded without file validation'
    }), 201


@insurance_bp.route('/api/v1/insurance/claims/override', methods=['POST'])
def v1_claims_override():
    """Claims override - fraud controls bypass"""
    data = request.get_json() or {}
    claim_id = data.get('claim_id')
    claim = claims_db.get(claim_id, {'claim_id': claim_id})
    claim['override_fraud_checks'] = data.get('override_fraud_checks', False)
    claims_db[claim_id] = claim
    return jsonify({
        'claim': claim,
        'warning': 'Fraud controls overridden without approval'
    })


@insurance_bp.route('/api/v1/insurance/claims/settlement', methods=['POST'])
def v1_claims_settlement():
    """Claims settlement override"""
    data = request.get_json() or {}
    settlement_id = f"SET-{uuid.uuid4().hex[:8]}"
    record = {
        'settlement_id': settlement_id,
        'claim_id': data.get('claim_id'),
        'amount': data.get('amount', 0),
        'override_limits': data.get('override_limits', False),
        'approved_at': datetime.now().isoformat()
    }
    claims_db[settlement_id] = record
    return jsonify({
        'settlement': record,
        'warning': 'Settlement approved without authorization'
    }), 201


@insurance_bp.route('/api/v1/insurance/policies/<policy_id>')
def v1_policy_details(policy_id):
    """Policy details - IDOR"""
    policy = policies_db.get(policy_id, {'policy_id': policy_id, 'status': 'active'})
    return jsonify({
        'policy': policy,
        'warning': 'Policy data exposed without authorization'
    })


@insurance_bp.route('/api/v1/insurance/policies/<policy_id>/endorse', methods=['POST'])
def v1_policy_endorse(policy_id):
    """Policy endorsement tampering"""
    data = request.get_json() or {}
    policy = policies_db.get(policy_id, {'policy_id': policy_id, 'endorsements': []})
    endorsement = {
        'endorsement_id': f'END-{uuid.uuid4().hex[:8]}',
        'type': data.get('type', 'coverage_change'),
        'override_checks': data.get('override_checks', False),
        'created_at': datetime.now().isoformat()
    }
    policy.setdefault('endorsements', []).append(endorsement)
    policies_db[policy_id] = policy
    return jsonify({
        'policy_id': policy_id,
        'endorsement': endorsement,
        'warning': 'Endorsement applied without approval'
    }), 201


@insurance_bp.route('/api/v1/insurance/policies/<policy_id>/cancel', methods=['PUT'])
def v1_policy_cancel(policy_id):
    """Policy cancellation override"""
    data = request.get_json() or {}
    policy = policies_db.get(policy_id, {'policy_id': policy_id})
    policy['status'] = 'cancelled'
    policy['bypass_validation'] = data.get('bypass_validation', False)
    policy['cancelled_at'] = datetime.now().isoformat()
    policies_db[policy_id] = policy
    return jsonify({
        'policy': policy,
        'warning': 'Policy cancelled without validation'
    })


@insurance_bp.route('/api/v1/insurance/underwriting/approve', methods=['POST'])
def v1_underwriting_approve():
    """Underwriting approval bypass"""
    data = request.get_json() or {}
    policy_id = data.get('policy_id')
    policy = policies_db.get(policy_id, {'policy_id': policy_id})
    policy['approved'] = True
    policy['override_controls'] = data.get('override_controls', False)
    policies_db[policy_id] = policy
    return jsonify({
        'policy': policy,
        'warning': 'Underwriting approved without validation'
    })


@insurance_bp.route('/api/v1/insurance/policies/<policy_id>/premium', methods=['PUT'])
def v1_policy_premium(policy_id):
    """Premium tampering"""
    data = request.get_json() or {}
    policy = policies_db.get(policy_id, {'policy_id': policy_id})
    policy['annual_premium'] = data.get('annual_premium', 0)
    policy['bypass_audit'] = data.get('bypass_audit', False)
    policies_db[policy_id] = policy
    return jsonify({
        'policy': policy,
        'warning': 'Premium updated without audit controls'
    })


@insurance_bp.route('/api/v1/insurance/policies/<policy_id>/beneficiary', methods=['POST'])
def v1_policy_beneficiary(policy_id):
    """Beneficiary change abuse"""
    data = request.get_json() or {}
    policy = policies_db.get(policy_id, {'policy_id': policy_id})
    policy['beneficiary'] = data.get('beneficiary')
    policy['skip_verification'] = data.get('skip_verification', False)
    policies_db[policy_id] = policy
    return jsonify({
        'policy': policy,
        'warning': 'Beneficiary updated without verification'
    })


@insurance_bp.route('/api/v1/insurance/policies/<policy_id>/documents/export')
def v1_policy_documents_export(policy_id):
    """Policy document export - PII exposure"""
    include_pii = request.args.get('include_pii', 'false').lower() == 'true'
    return jsonify({
        'policy_id': policy_id,
        'include_pii': include_pii,
        'documents': ['policy.pdf', 'coverage.pdf'],
        'warning': 'Documents exported without authorization'
    })


@insurance_bp.route('/api/v1/insurance/risk/scores/manipulate', methods=['PUT'])
def v1_risk_score_manipulate():
    """Risk score manipulation"""
    data = request.get_json() or {}
    policy_id = data.get('policy_id')
    policy = policies_db.get(policy_id, {'policy_id': policy_id})
    policy['risk_score'] = data.get('risk_score', 0.5)
    policy['risk_reason'] = data.get('reason', 'manual_override')
    policies_db[policy_id] = policy
    return jsonify({
        'policy': policy,
        'warning': 'Risk score updated without validation'
    })


@insurance_bp.route('/api/v1/insurance/billing/tokenize', methods=['POST'])
def v1_billing_tokenize():
    """Tokenization abuse"""
    data = request.get_json() or {}
    return jsonify({
        'token': f'TOK-{uuid.uuid4().hex[:8]}',
        'force_token': data.get('force_token'),
        'warning': 'Payment token issued without validation'
    })


@insurance_bp.route('/api/v1/insurance/billing/invoices/<invoice_id>')
def v1_billing_invoice(invoice_id):
    """Invoice IDOR"""
    invoice = {
        'invoice_id': invoice_id,
        'amount': random.randint(100, 5000),
        'status': 'open'
    }
    return jsonify({
        'invoice': invoice,
        'warning': 'Invoice exposed without authorization'
    })


@insurance_bp.route('/api/v1/insurance/billing/refund', methods=['POST'])
def v1_billing_refund():
    """Refund abuse"""
    data = request.get_json() or {}
    return jsonify({
        'invoice_id': data.get('invoice_id'),
        'amount': data.get('amount', 0),
        'warning': 'Refund processed without validation'
    })


@insurance_bp.route('/api/v1/insurance/billing/autopay', methods=['PUT'])
def v1_billing_autopay():
    """Autopay bypass"""
    data = request.get_json() or {}
    return jsonify({
        'enabled': data.get('enabled', True),
        'bypass_mfa': data.get('bypass_mfa', False),
        'warning': 'Autopay updated without MFA'
    })


@insurance_bp.route('/api/v1/insurance/billing/statements')
def v1_billing_statements():
    """Statements scraping"""
    limit = int(request.args.get('limit', 100))
    return jsonify({
        'statements': [{'statement_id': f'ST-{i}'} for i in range(min(limit, 10))],
        'warning': 'Statements listed without authorization'
    })


@insurance_bp.route('/api/v1/insurance/brokers/<broker_id>')
def v1_broker_details(broker_id):
    """Broker portal IDOR"""
    broker = insurance_brokers_db.get(broker_id, {'broker_id': broker_id})
    return jsonify({
        'broker': broker,
        'warning': 'Broker data exposed without authorization'
    })


@insurance_bp.route('/api/v1/insurance/brokers/commissions/export')
def v1_broker_commissions_export():
    """Commissions export"""
    include_pii = request.args.get('include_pii', 'false').lower() == 'true'
    return jsonify({
        'commissions': list(insurance_commissions_db.values()),
        'include_pii': include_pii,
        'warning': 'Commissions exported without authorization'
    })


@insurance_bp.route('/api/v1/insurance/brokers/clients/<client_id>', methods=['PUT'])
def v1_broker_client_update(client_id):
    """Broker client tampering"""
    data = request.get_json() or {}
    insurance_broker_clients_db[client_id] = {
        'client_id': client_id,
        'override_policy': data.get('override_policy', False),
        'updated_at': datetime.now().isoformat()
    }
    return jsonify({
        'client_id': client_id,
        'warning': 'Client updated without authorization'
    })
