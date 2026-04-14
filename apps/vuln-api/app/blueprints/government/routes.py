"""
Routes for government endpoints.
Demonstrates citizen services, identity access, and mission data integrity vulnerabilities.
"""
from starlette.requests import Request
from starlette.responses import JSONResponse
from datetime import datetime, timedelta
import uuid
import random

from . import government_router
from app.models import *
from app.routing import get_json_or_default


# ============================================================================
# CITIZEN SERVICES & CASEWORK
# ============================================================================

@government_router.route('/api/v1/gov/cases/<case_id>')
async def get_case_details(request: Request, case_id):
    """Get case details - IDOR vulnerability"""
    # Vulnerability: No authorization check for case ownership
    case = gov_cases_db.get(case_id)

    if not case:
        case = {
            'case_id': case_id,
            'citizen_id': f'CIT-{random.randint(1000, 9999)}',
            'program': random.choice(['benefits', 'permits', 'licensing']),
            'status': random.choice(['pending', 'review', 'approved', 'denied']),
            'assigned_agent': f'AGT-{random.randint(100, 999)}',
            'ssn': f'{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}',
            'last_updated': datetime.now().isoformat()
        }
        gov_cases_db[case_id] = case

    return JSONResponse({
        'case_id': case['case_id'],
        'citizen_id': case['citizen_id'],
        'program': case['program'],
        'status': case['status'],
        'assigned_agent': case['assigned_agent'],
        'ssn': case.get('ssn'),
        'notes': case.get('notes', 'Case requires additional documentation.'),
        'last_updated': case['last_updated']
    })


@government_router.route('/api/v1/gov/benefits/search')
async def benefits_search(request: Request):
    """Benefits search - SQL injection vulnerability"""
    query = request.query_params.get('q', '')
    program = request.query_params.get('program', '')

    sql_query = f"SELECT * FROM benefits WHERE program='{program}' AND applicant LIKE '%{query}%'"

    if any(token in query.lower() for token in ['union', 'select', 'drop', '--', ';']):
        return JSONResponse({
            'vulnerability': 'SQL_INJECTION_DETECTED',
            'query': sql_query,
            'message': 'Query bypassed input validation',
            'exposed_data': {
                'database': 'gov_benefits',
                'tables': ['benefits', 'citizens', 'cases', 'users'],
                'admin_user': {'username': 'benefits_admin', 'password_hash': 'md5_hash_here'}
            }
        })

    results = []
    for application in gov_benefits_applications_db.values():
        if program and application.get('program') != program:
            continue
        if query and query.lower() not in application.get('citizen_id', '').lower():
            continue
        results.append(application)

    return JSONResponse({
        'results': results,
        'count': len(results),
        'sql_query': sql_query
    })


@government_router.route('/api/v1/gov/benefits/<application_id>/eligibility', methods=['PUT'])
async def benefits_eligibility_override(request: Request, application_id):
    """Eligibility override - bypass controls"""
    data = await get_json_or_default(request)
    application = gov_benefits_applications_db.get(application_id, {'application_id': application_id})
    application['eligible'] = data.get('eligible', True)
    application['override_checks'] = data.get('override_checks', False)
    application['updated_at'] = datetime.now().isoformat()
    gov_benefits_applications_db[application_id] = application

    return JSONResponse({
        'application': application,
        'warning': 'Eligibility updated without validation'
    })


@government_router.route('/api/v1/gov/service-requests', methods=['POST'])
async def service_request_submit(request: Request):
    """Submit service request - tampering vulnerability"""
    data = await get_json_or_default(request)
    request_id = f"SR-{uuid.uuid4().hex[:8]}"

    priority = data.get('priority', 'normal')
    bypass_validation = data.get('bypass_validation', False)

    if bypass_validation:
        priority = 'critical'

    service_request = {
        'request_id': request_id,
        'request_type': data.get('request_type', 'general'),
        'priority': priority,
        'status': 'open',
        'submitted_at': datetime.now().isoformat(),
        'bypass_validation': bypass_validation
    }

    gov_service_requests_db[request_id] = service_request

    return JSONResponse({
        'status': 'received',
        'service_request': service_request,
        'warning': 'Priority set without validation checks'
    }, status_code=201)


@government_router.route('/api/v1/gov/records/export')
async def records_export(request: Request):
    """Export public records - data exfiltration"""
    limit = int(request.query_params.get('limit', 100))
    include_sensitive = request.query_params.get('include_sensitive', 'false').lower() == 'true'

    records = list(gov_records_db.values())
    exported = []

    for record in records[:limit]:
        payload = dict(record)
        if not include_sensitive:
            payload.pop('ssn', None)
            payload.pop('address', None)
        exported.append(payload)

    return JSONResponse({
        'export_id': f'EXP-{uuid.uuid4().hex[:8]}',
        'records': exported,
        'total_records': len(records),
        'exported_records': len(exported),
        'include_sensitive': include_sensitive
    })


@government_router.route('/api/v1/gov/cases/<case_id>/status', methods=['PUT'])
async def update_case_status(request: Request, case_id):
    """Update case status - manipulation vulnerability"""
    data = await get_json_or_default(request)
    new_status = data.get('status', 'pending')
    override_checks = data.get('override_checks', False)

    case = gov_cases_db.get(case_id)
    if not case:
        case = {
            'case_id': case_id,
            'citizen_id': f'CIT-{random.randint(1000, 9999)}',
            'program': 'benefits',
            'status': 'pending',
            'assigned_agent': f'AGT-{random.randint(100, 999)}',
            'last_updated': datetime.now().isoformat()
        }
        gov_cases_db[case_id] = case

    old_status = case['status']
    case['status'] = new_status
    case['last_updated'] = datetime.now().isoformat()

    return JSONResponse({
        'case_id': case_id,
        'previous_status': old_status,
        'new_status': new_status,
        'override_checks': override_checks,
        'warning': 'Status change accepted without workflow validation'
    })


@government_router.route('/api/v1/gov/cases/<case_id>/reassign', methods=['PUT'])
async def reassign_case(request: Request, case_id):
    """Case reassignment - bypass workflow"""
    data = await get_json_or_default(request)
    case = gov_cases_db.get(case_id, {'case_id': case_id})
    previous_agent = case.get('assigned_agent')
    case['assigned_agent'] = data.get('assigned_agent', f'AGT-{random.randint(100, 999)}')
    case['override_policy'] = data.get('override_policy', False)
    case['last_updated'] = datetime.now().isoformat()
    gov_cases_db[case_id] = case

    return JSONResponse({
        'case_id': case_id,
        'previous_agent': previous_agent,
        'new_agent': case['assigned_agent'],
        'warning': 'Case reassigned without authorization'
    })


# ============================================================================
# IDENTITY & ACCESS CONTROL
# ============================================================================

@government_router.route('/api/v1/gov/identity/cards/<card_id>')
async def access_card_details(request: Request, card_id):
    """Access card details - IDOR vulnerability"""
    card = gov_access_cards_db.get(card_id)
    if not card:
        card = {
            'card_id': card_id,
            'holder': f'user-{random.randint(1, 5)}',
            'clearance': random.choice(['public', 'restricted', 'secret']),
            'active': True
        }
        gov_access_cards_db[card_id] = card

    return JSONResponse({
        'card_id': card['card_id'],
        'holder': card['holder'],
        'clearance': card['clearance'],
        'active': card['active'],
        'issued_at': card.get('issued_at', datetime.now().isoformat())
    })


@government_router.route('/api/v1/gov/users/<user_id>/roles', methods=['PUT'])
async def update_user_role(request: Request, user_id):
    """Update user roles - privilege escalation"""
    data = await get_json_or_default(request)
    role = data.get('role', 'user')
    skip_approval = data.get('skip_approval', False)

    user = gov_users_db.get(user_id, {'user_id': user_id, 'name': 'Unknown', 'agency': 'unknown'})
    old_role = user.get('role', 'user')
    user['role'] = role
    gov_users_db[user_id] = user

    return JSONResponse({
        'user_id': user_id,
        'previous_role': old_role,
        'new_role': role,
        'skip_approval': skip_approval,
        'warning': 'Role update applied without authorization workflow'
    })


@government_router.route('/api/v1/gov/auth/mfa/verify', methods=['POST'])
async def mfa_verify(request: Request):
    """MFA verification - bypass vulnerability"""
    data = await get_json_or_default(request)
    code = data.get('code', '')
    bypass = data.get('bypass', False)

    if code == '000000' or bypass:
        return JSONResponse({
            'status': 'verified',
            'bypass_used': True,
            'message': 'MFA bypass accepted'
        })

    return JSONResponse({
        'status': 'verified',
        'bypass_used': False,
        'message': 'MFA verification successful'
    })


@government_router.route('/api/v1/gov/auth/sso/callback', methods=['POST'])
async def sso_callback(request: Request):
    """Federated login callback - assertion tampering"""
    data = await get_json_or_default(request)
    assertion = data.get('assertion', '')
    force_admin = data.get('force_admin', False)

    is_tampered = 'tampered' in assertion or force_admin
    role = 'admin' if is_tampered else 'user'

    return JSONResponse({
        'status': 'authenticated',
        'role': role,
        'assertion_validated': not is_tampered,
        'session_token': f'gov-sso-{uuid.uuid4().hex[:10]}'
    })


@government_router.route('/api/v1/gov/identity/credentials/export')
async def credentials_export(request: Request):
    """Export identity credentials - sensitive data exposure"""
    limit = int(request.query_params.get('limit', 100))
    credentials = list(gov_credentials_db.values())[:limit]

    return JSONResponse({
        'exported': credentials,
        'count': len(credentials),
        'warning': 'Credential export performed without authorization'
    })


# ============================================================================
# MISSION DATA INTEGRITY
# ============================================================================

@government_router.route('/api/v1/gov/audit-logs/<log_id>', methods=['DELETE'])
async def delete_audit_log(request: Request, log_id):
    """Audit log deletion - tampering vulnerability"""
    deleted = gov_audit_logs_db.pop(log_id, None)

    return JSONResponse({
        'log_id': log_id,
        'deleted': True,
        'previous_entry': deleted,
        'tamper_successful': True
    })


@government_router.route('/api/v1/gov/records/bulk-export')
async def records_bulk_export(request: Request):
    """Bulk export records - data exfiltration"""
    format_type = request.query_params.get('format', 'json')
    limit = int(request.query_params.get('limit', 1000))

    records = list(gov_records_db.values())[:limit]

    if format_type == 'sql_dump':
        return JSONResponse({
            'format': format_type,
            'dump': f"INSERT INTO records VALUES ({len(records)} rows);",
            'records_exported': len(records)
        })

    return JSONResponse({
        'format': format_type,
        'records': records,
        'records_exported': len(records)
    })


@government_router.route('/api/v1/gov/data/classify', methods=['POST'])
async def classify_record(request: Request):
    """Classification override - access control bypass"""
    data = await get_json_or_default(request)
    record_id = data.get('record_id')
    classification = data.get('classification', 'public')
    override_controls = data.get('override_controls', False)

    current = gov_classifications_db.get(record_id, 'restricted')
    gov_classifications_db[record_id] = classification

    record = gov_records_db.get(record_id)
    if record:
        record['classification'] = classification

    return JSONResponse({
        'record_id': record_id,
        'previous_classification': current,
        'new_classification': classification,
        'override_controls': override_controls
    })


@government_router.route('/api/v1/gov/cases/history')
async def case_history_search(request: Request):
    """Case history search - SQL injection vulnerability"""
    case_id = request.query_params.get('case_id', '')
    sql_query = f"SELECT * FROM cases WHERE case_id = '{case_id}'"

    if any(token in case_id.lower() for token in ['union', 'select', '--', ';']):
        return JSONResponse({
            'vulnerability': 'SQL_INJECTION_DETECTED',
            'query': sql_query,
            'exposed_tables': ['cases', 'citizens', 'audit_logs'],
            'admin_token': 'gov_admin_token_123'
        })

    history = []
    case = gov_cases_db.get(case_id)
    if case:
        history.append({
            'case_id': case_id,
            'status': case.get('status'),
            'updated_at': case.get('last_updated')
        })

    return JSONResponse({
        'case_id': case_id,
        'history': history,
        'sql_query': sql_query
    })


@government_router.route('/api/v1/gov/records/<record_id>', methods=['PUT'])
async def update_record(request: Request, record_id):
    """Update record - data tampering vulnerability"""
    data = await get_json_or_default(request)
    bypass_audit = data.get('bypass_audit', False)

    record = gov_records_db.get(record_id, {
        'record_id': record_id,
        'citizen_id': f'CIT-{random.randint(1000, 9999)}',
        'name': 'Unknown',
        'classification': 'restricted',
        'status': 'active'
    })

    record.update({
        'status': data.get('status', record.get('status')),
        'classification': data.get('classification', record.get('classification')),
        'last_modified': datetime.now().isoformat()
    })

    gov_records_db[record_id] = record

    return JSONResponse({
        'record': record,
        'bypass_audit': bypass_audit,
        'warning': 'Record updated without audit trail enforcement'
    })


# ============================================================================
# LICENSING & PERMITS
# ============================================================================

@government_router.route('/api/v1/gov/permits/apply', methods=['POST'])
async def apply_permit(request: Request):
    """Permit application - validation bypass"""
    data = await get_json_or_default(request)
    permit_id = f"PERM-{uuid.uuid4().hex[:8]}"

    permit = {
        'permit_id': permit_id,
        'permit_type': data.get('permit_type', 'general'),
        'priority': data.get('priority', 'standard'),
        'submitted_at': datetime.now().isoformat(),
        'bypass_validation': data.get('bypass_validation', False),
        'status': 'submitted'
    }
    gov_permits_db[permit_id] = permit

    return JSONResponse({
        'permit': permit,
        'warning': 'Permit accepted without validation checks'
    }, status_code=201)


@government_router.route('/api/v1/gov/licenses/<license_id>')
async def get_license(request: Request, license_id):
    """License lookup - IDOR vulnerability"""
    license_record = gov_licenses_db.get(license_id)
    if not license_record:
        license_record = {
            'license_id': license_id,
            'holder': f'holder-{random.randint(100, 999)}',
            'type': random.choice(['business', 'contractor', 'driver']),
            'status': random.choice(['active', 'suspended', 'expired']),
            'expires_at': (datetime.now() + timedelta(days=365)).isoformat()
        }
        gov_licenses_db[license_id] = license_record

    return JSONResponse({
        'license': license_record,
        'warning': 'License data exposed without access control'
    })


@government_router.route('/api/v1/gov/licenses/export')
async def licenses_export(request: Request):
    """License export - data exfiltration"""
    include_pii = request.query_params.get('include_pii', 'false').lower() == 'true'
    limit = int(request.query_params.get('limit', 1000))
    licenses = list(gov_licenses_db.values())[:limit]

    if include_pii:
        for entry in licenses:
            entry.setdefault('ssn', f'{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}')

    return JSONResponse({
        'licenses': licenses,
        'include_pii': include_pii,
        'count': len(licenses),
        'warning': 'License export performed without authorization'
    })


@government_router.route('/api/v1/gov/permits/<permit_id>/approve', methods=['PUT'])
async def approve_permit(request: Request, permit_id):
    """Permit approval - override vulnerability"""
    data = await get_json_or_default(request)
    permit = gov_permits_db.get(permit_id, {'permit_id': permit_id})
    permit['status'] = 'approved' if data.get('approved', True) else 'denied'
    permit['override_checks'] = data.get('override_checks', False)
    permit['updated_at'] = datetime.now().isoformat()
    gov_permits_db[permit_id] = permit

    return JSONResponse({
        'permit': permit,
        'warning': 'Permit approval applied without review'
    })


# ============================================================================
# GRANTS & ASSISTANCE PROGRAMS
# ============================================================================

@government_router.route('/api/v1/gov/grants/apply', methods=['POST'])
async def apply_grant(request: Request):
    """Grant application - injection and bypass risks"""
    data = await get_json_or_default(request)
    grant_id = f"GRANT-{uuid.uuid4().hex[:8]}"

    grant = {
        'grant_id': grant_id,
        'program_id': data.get('program_id', 'GENERAL'),
        'amount': data.get('amount', 0),
        'submitted_at': datetime.now().isoformat(),
        'override_checks': data.get('override_checks', False),
        'status': 'submitted'
    }
    gov_grants_db[grant_id] = grant

    return JSONResponse({
        'grant': grant,
        'warning': 'Grant accepted without eligibility validation'
    }, status_code=201)


@government_router.route('/api/v1/gov/grants/<grant_id>/award', methods=['PUT'])
async def award_grant(request: Request, grant_id):
    """Grant award manipulation"""
    data = await get_json_or_default(request)
    grant = gov_grants_db.get(grant_id, {'grant_id': grant_id})
    grant['award_amount'] = data.get('award_amount', 0)
    grant['bypass_review'] = data.get('bypass_review', False)
    grant['status'] = 'awarded'
    grant['awarded_at'] = datetime.now().isoformat()
    gov_grants_db[grant_id] = grant

    return JSONResponse({
        'grant': grant,
        'warning': 'Award updated without review workflow'
    })


@government_router.route('/api/v1/gov/grants/disburse', methods=['POST'])
async def disburse_grant(request: Request):
    """Grant disbursement - bypass controls"""
    data = await get_json_or_default(request)
    disbursement = {
        'grant_id': data.get('grant_id'),
        'account': data.get('account', 'acct-unknown'),
        'amount': data.get('amount', 0),
        'force_disbursement': data.get('force_disbursement', False),
        'disbursed_at': datetime.now().isoformat()
    }

    return JSONResponse({
        'disbursement': disbursement,
        'warning': 'Disbursement executed without approval'
    }, status_code=201)


# ============================================================================
# PUBLIC RECORDS & FOIA
# ============================================================================

@government_router.route('/api/v1/gov/foia/requests', methods=['POST'])
async def create_foia_request(request: Request):
    """FOIA request submission"""
    data = await get_json_or_default(request)
    request_id = f"FOIA-{uuid.uuid4().hex[:8]}"

    request_record = {
        'request_id': request_id,
        'requester_id': data.get('requester_id', 'unknown'),
        'records': data.get('records', []),
        'bypass_filters': data.get('bypass_filters', False),
        'status': 'open',
        'submitted_at': datetime.now().isoformat()
    }
    gov_foia_requests_db[request_id] = request_record

    return JSONResponse({
        'request': request_record,
        'warning': 'FOIA request accepted without validation'
    }, status_code=201)


@government_router.route('/api/v1/gov/foia/export')
async def export_foia_records(request: Request):
    """FOIA export - data exfiltration"""
    include_sensitive = request.query_params.get('include_sensitive', 'false').lower() == 'true'
    limit = int(request.query_params.get('limit', 1000))
    records = list(gov_records_db.values())[:limit]

    exported = []
    for record in records:
        payload = dict(record)
        if not include_sensitive:
            payload.pop('ssn', None)
            payload.pop('address', None)
        exported.append(payload)

    return JSONResponse({
        'records': exported,
        'include_sensitive': include_sensitive,
        'count': len(exported)
    })


@government_router.route('/api/v1/gov/foia/requests/<request_id>/status', methods=['PUT'])
async def update_foia_status(request: Request, request_id):
    """FOIA status update - bypass controls"""
    data = await get_json_or_default(request)
    request_record = gov_foia_requests_db.get(request_id, {'request_id': request_id})
    request_record['status'] = data.get('status', 'approved')
    request_record['override_checks'] = data.get('override_checks', False)
    request_record['updated_at'] = datetime.now().isoformat()
    gov_foia_requests_db[request_id] = request_record

    return JSONResponse({
        'request': request_record,
        'warning': 'FOIA status updated without review'
    })


# ============================================================================
# EMERGENCY ALERTS & BROADCASTS
# ============================================================================

@government_router.route('/api/v1/gov/alerts/broadcast', methods=['POST'])
async def alert_broadcast(request: Request):
    """Alert broadcast - unauthorized broadcast"""
    data = await get_json_or_default(request)
    alert_id = f"ALERT-{uuid.uuid4().hex[:8]}"

    alert = {
        'alert_id': alert_id,
        'message': data.get('message', 'Test alert'),
        'severity': data.get('severity', 'info'),
        'bypass_authorization': data.get('bypass_authorization', False),
        'sent_at': datetime.now().isoformat()
    }
    gov_alerts_db[alert_id] = alert

    return JSONResponse({
        'alert': alert,
        'warning': 'Alert broadcast without authorization'
    }, status_code=201)


@government_router.route('/api/v1/gov/alerts/<alert_id>/suppress', methods=['PUT'])
async def alert_suppress(request: Request, alert_id):
    """Suppress alert - tampering vulnerability"""
    data = await get_json_or_default(request)
    alert = gov_alerts_db.get(alert_id, {'alert_id': alert_id})
    alert['suppressed'] = True
    alert['reason'] = data.get('reason', 'maintenance')
    alert['force_suppress'] = data.get('force_suppress', False)
    alert['suppressed_at'] = datetime.now().isoformat()
    gov_alerts_db[alert_id] = alert

    return JSONResponse({
        'alert': alert,
        'warning': 'Alert suppressed without authorization'
    })


@government_router.route('/api/v1/gov/alerts/target')
async def alert_geo_target(request: Request):
    """Targeted alerts - override limits"""
    region = request.query_params.get('region', 'all')
    override_limits = request.query_params.get('override_limits', 'false').lower() == 'true'

    return JSONResponse({
        'region': region,
        'override_limits': override_limits,
        'warning': 'Geo targeting executed without validation'
    })
