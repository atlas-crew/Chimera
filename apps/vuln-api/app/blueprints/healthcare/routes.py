"""
Routes for healthcare endpoints.
Demonstrates PHI data exposure, access control bypass, and healthcare-specific vulnerabilities.
"""

from flask import request, jsonify, render_template_string, session
from datetime import datetime, timedelta
import uuid
import random
import json
import time
import sqlite3
import os
import pickle
import base64

from . import healthcare_bp
from app.models import *


# ============================================================================
# PATIENT RECORDS - PHI Exposure Vulnerabilities
# ============================================================================

@healthcare_bp.route('/api/v1/healthcare/records')
def list_records():
    """List medical records - Missing pagination and access controls"""
    # Vulnerability: No authentication check, returns all records
    # Vulnerability: PHI data exposure without proper authorization
    records = []
    for record_id, record in medical_records_db.items():
        records.append({
            'record_id': record_id,
            'patient_id': record.get('patient_id'),
            'patient_name': record.get('patient_name'),
            'ssn': record.get('ssn'),  # PHI exposure
            'dob': record.get('dob'),
            'diagnosis': record.get('diagnosis'),
            'medications': record.get('medications', []),
            'last_visit': record.get('last_visit'),
            'provider_id': record.get('provider_id')
        })

    return jsonify({
        'records': records,
        'total_count': len(records),
        'warning': 'PHI data included without authorization check'
    })


@healthcare_bp.route('/api/v1/healthcare/records/<record_id>')
def get_record_details(record_id):
    """Get record details - IDOR vulnerability"""
    # Vulnerability: No authorization check - any user can access any record
    # Vulnerability: Full PHI exposure including sensitive fields

    if record_id not in medical_records_db:
        return jsonify({'error': 'Record not found'}), 404

    record = medical_records_db[record_id]

    return jsonify({
        'record_id': record_id,
        'patient_info': {
            'patient_id': record.get('patient_id'),
            'name': record.get('patient_name'),
            'ssn': record.get('ssn'),
            'dob': record.get('dob'),
            'address': record.get('address', '123 Main St, City, ST 12345'),
            'phone': record.get('phone', '555-0100'),
            'email': record.get('email', 'patient@example.com'),
            'insurance_id': record.get('insurance_id', 'INS-' + str(random.randint(100000, 999999)))
        },
        'medical_info': {
            'diagnosis': record.get('diagnosis'),
            'medications': record.get('medications', []),
            'allergies': record.get('allergies', ['Penicillin']),
            'conditions': record.get('conditions', ['Hypertension', 'Type 2 Diabetes']),
            'lab_results': record.get('lab_results', []),
            'treatment_plan': record.get('treatment_plan', 'Standard care protocol')
        },
        'visit_history': record.get('visit_history', []),
        'provider_notes': record.get('provider_notes', 'Patient presents with...'),
        'billing_codes': record.get('billing_codes', ['99213', '80053'])
    })


@healthcare_bp.route('/api/v1/healthcare/records/search')
def search_records():
    """Search records - SQL Injection vulnerability"""
    # Vulnerability: SQL injection through unsanitized search parameter
    # Vulnerability: Returns sensitive PHI without proper authorization

    search_query = request.args.get('q', '')
    patient_name = request.args.get('name', '')
    ssn = request.args.get('ssn', '')
    diagnosis = request.args.get('diagnosis', '')

    # Simulated SQL injection vulnerability
    if search_query:
        # Intentionally vulnerable: Direct string concatenation
        sql_query = f"SELECT * FROM medical_records WHERE patient_name LIKE '%{search_query}%' OR diagnosis LIKE '%{search_query}%'"

        # Simulate SQL injection detection
        if any(keyword in search_query.lower() for keyword in ['union', 'select', '--', ';', 'drop', 'delete']):
            # Simulate successful SQL injection
            return jsonify({
                'vulnerability': 'SQL_INJECTION_DETECTED',
                'query': sql_query,
                'message': 'SQL injection successful',
                'exposed_data': {
                    'database': 'healthcare_db',
                    'tables': ['medical_records', 'patients', 'providers', 'prescriptions'],
                    'admin_credentials': {'username': 'db_admin', 'password_hash': 'md5_hash_here'}
                }
            })

    # Normal search (still vulnerable to enumeration)
    results = []
    for record_id, record in medical_records_db.items():
        if (search_query and (search_query.lower() in record.get('patient_name', '').lower() or
                             search_query.lower() in record.get('diagnosis', '').lower())) or \
           (patient_name and patient_name.lower() in record.get('patient_name', '').lower()) or \
           (ssn and ssn in record.get('ssn', '')) or \
           (diagnosis and diagnosis.lower() in record.get('diagnosis', '').lower()):
            results.append({
                'record_id': record_id,
                'patient_name': record.get('patient_name'),
                'ssn': record.get('ssn'),
                'dob': record.get('dob'),
                'diagnosis': record.get('diagnosis')
            })

    return jsonify({
        'results': results,
        'count': len(results),
        'sql_query': sql_query if search_query else 'N/A'
    })


@healthcare_bp.route('/api/v1/healthcare/records/upload', methods=['POST'])
def upload_documents():
    """Upload documents - Path traversal vulnerability"""
    # Vulnerability: Path traversal in filename handling
    # Vulnerability: Unrestricted file upload

    data = request.get_json() or {}
    record_id = data.get('record_id')
    filename = data.get('filename', '')
    content = data.get('content', '')

    # Vulnerability: No filename sanitization allows path traversal
    # Example: filename="../../../etc/passwd" or "../../config/secrets.json"

    if '..' in filename or '/' in filename:
        # Simulate path traversal attack
        return jsonify({
            'status': 'uploaded',
            'vulnerability': 'PATH_TRAVERSAL',
            'file_path': f'/var/www/uploads/{filename}',
            'warning': 'File written outside upload directory',
            'potential_paths': [
                '/var/www/uploads/../../../etc/passwd',
                '/var/www/uploads/../config/database.yml',
                '/var/www/uploads/../.env'
            ]
        })

    # Normal upload (still vulnerable to unrestricted file types)
    upload_id = str(uuid.uuid4())
    return jsonify({
        'status': 'uploaded',
        'upload_id': upload_id,
        'filename': filename,
        'record_id': record_id,
        'size_bytes': len(content),
        'warning': 'No file type validation performed'
    })


# ============================================================================
# APPOINTMENTS - Missing Authorization Controls
# ============================================================================

@healthcare_bp.route('/api/v1/healthcare/appointments')
def list_appointments():
    """List appointments - Exposes all patient appointments"""
    # Vulnerability: No authorization check
    # Vulnerability: Returns PHI (patient names, conditions)

    appointments = [
        {
            'appointment_id': f'APT-{uuid.uuid4().hex[:8]}',
            'patient_id': f'PAT-{random.randint(1000, 9999)}',
            'patient_name': random.choice(['John Smith', 'Jane Doe', 'Robert Johnson']),
            'provider_id': f'PROV-{random.randint(100, 999)}',
            'provider_name': random.choice(['Dr. Williams', 'Dr. Brown', 'Dr. Davis']),
            'appointment_date': (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat(),
            'reason': random.choice(['Annual checkup', 'Follow-up', 'Lab results review', 'New symptoms']),
            'status': random.choice(['scheduled', 'confirmed', 'completed', 'cancelled'])
        }
        for _ in range(20)
    ]

    return jsonify({
        'appointments': appointments,
        'total_count': len(appointments)
    })


@healthcare_bp.route('/api/v1/healthcare/appointments/schedule', methods=['POST'])
def schedule_appointment():
    """Schedule appointment - Missing validation"""
    # Vulnerability: No provider credential verification
    # Vulnerability: Can schedule for any patient

    data = request.get_json() or {}
    patient_id = data.get('patient_id')
    provider_id = data.get('provider_id')
    appointment_date = data.get('date')
    reason = data.get('reason', '')

    appointment_id = f'APT-{uuid.uuid4().hex[:8]}'

    return jsonify({
        'status': 'scheduled',
        'appointment_id': appointment_id,
        'patient_id': patient_id,
        'provider_id': provider_id,
        'date': appointment_date,
        'reason': reason,
        'warning': 'No authorization check performed'
    })


@healthcare_bp.route('/api/v1/healthcare/appointments/cancel', methods=['POST'])
def cancel_appointment():
    """Cancel appointment - IDOR vulnerability"""
    # Vulnerability: Can cancel any appointment without authorization

    data = request.get_json() or {}
    appointment_id = data.get('appointment_id')

    return jsonify({
        'status': 'cancelled',
        'appointment_id': appointment_id,
        'cancelled_by': 'unauthenticated_user',
        'warning': 'No authorization check - can cancel any appointment'
    })


# ============================================================================
# PRESCRIPTIONS - Controlled Substance Abuse
# ============================================================================

@healthcare_bp.route('/api/v1/healthcare/prescriptions')
def list_prescriptions():
    """List prescriptions - DEA controlled substances exposed"""
    # Vulnerability: Exposes controlled substance prescriptions
    # Vulnerability: No authorization check

    prescriptions = [
        {
            'prescription_id': f'RX-{uuid.uuid4().hex[:8]}',
            'patient_id': f'PAT-{random.randint(1000, 9999)}',
            'patient_name': random.choice(['John Smith', 'Jane Doe', 'Robert Johnson']),
            'medication': random.choice(['Oxycodone 10mg', 'Hydrocodone 5mg', 'Alprazolam 1mg', 'Adderall 20mg']),
            'dea_schedule': random.choice(['II', 'III', 'IV']),
            'quantity': random.randint(30, 90),
            'refills': random.randint(0, 3),
            'provider_id': f'PROV-{random.randint(100, 999)}',
            'provider_name': random.choice(['Dr. Williams', 'Dr. Brown', 'Dr. Davis']),
            'provider_dea': f'B{random.choice(["W", "B", "D"])}{random.randint(1000000, 9999999)}',
            'issued_date': (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
            'status': random.choice(['active', 'filled', 'expired'])
        }
        for _ in range(15)
    ]

    return jsonify({
        'prescriptions': prescriptions,
        'total_count': len(prescriptions),
        'warning': 'DEA controlled substances exposed without authorization'
    })


@healthcare_bp.route('/api/v1/healthcare/prescriptions/refill', methods=['POST'])
def request_refill():
    """Request refill - Missing controls on controlled substances"""
    # Vulnerability: Can request refills without provider verification
    # Vulnerability: No check on refill limits for controlled substances

    data = request.get_json() or {}
    prescription_id = data.get('prescription_id')
    patient_id = data.get('patient_id')

    refill_id = f'REFILL-{uuid.uuid4().hex[:8]}'

    return jsonify({
        'status': 'approved',
        'refill_id': refill_id,
        'prescription_id': prescription_id,
        'patient_id': patient_id,
        'approved_date': datetime.now().isoformat(),
        'warning': 'No provider verification or refill limit check'
    })


@healthcare_bp.route('/api/v1/healthcare/prescriptions/history')
def prescription_history():
    """Prescription history - Full medication history exposed"""
    # Vulnerability: IDOR - can access any patient's prescription history

    patient_id = request.args.get('patient_id', f'PAT-{random.randint(1000, 9999)}')

    history = [
        {
            'date': (datetime.now() - timedelta(days=days)).isoformat(),
            'medication': random.choice(['Oxycodone', 'Lisinopril', 'Metformin', 'Sertraline', 'Alprazolam']),
            'dosage': f'{random.randint(5, 100)}mg',
            'provider': random.choice(['Dr. Williams', 'Dr. Brown', 'Dr. Davis']),
            'indication': random.choice(['Pain management', 'Hypertension', 'Diabetes', 'Anxiety', 'Depression'])
        }
        for days in range(0, 365, 30)
    ]

    return jsonify({
        'patient_id': patient_id,
        'prescription_history': history,
        'total_prescriptions': len(history)
    })


@healthcare_bp.route('/api/v1/healthcare/prescriptions/export')
def prescriptions_export():
    """Export prescriptions - bulk PHI exposure"""
    limit = int(request.args.get('limit', 1000))
    include_phi = request.args.get('include_phi', 'false').lower() == 'true'

    prescriptions = [
        {
            'prescription_id': f'RX-{uuid.uuid4().hex[:8]}',
            'patient_id': f'PAT-{random.randint(1000, 9999)}',
            'patient_name': random.choice(['John Smith', 'Jane Doe', 'Robert Johnson']),
            'medication': random.choice(['Oxycodone', 'Lisinopril', 'Metformin', 'Sertraline']),
            'issued_date': datetime.now().isoformat()
        }
        for _ in range(min(limit, 50))
    ]

    if not include_phi:
        for entry in prescriptions:
            entry.pop('patient_name', None)

    return jsonify({
        'exported': prescriptions,
        'count': len(prescriptions),
        'include_phi': include_phi,
        'warning': 'Prescription export performed without authorization'
    })


# ============================================================================
# PROVIDER DIRECTORY & LAB RESULTS
# ============================================================================

@healthcare_bp.route('/api/v1/healthcare/providers/<provider_id>')
def provider_directory(provider_id):
    """Provider directory lookup - IDOR vulnerability"""
    provider = providers_db.get(provider_id)
    if not provider:
        provider = {
            'provider_id': provider_id,
            'name': random.choice(['Dr. Lee', 'Dr. Patel', 'Dr. Williams']),
            'specialty': random.choice(['cardiology', 'oncology', 'primary_care']),
            'network': random.choice(['in-network', 'out-of-network']),
            'dea': f'B{random.choice(["W", "B", "D"])}{random.randint(1000000, 9999999)}'
        }
        providers_db[provider_id] = provider

    return jsonify({
        'provider': provider,
        'warning': 'Provider data exposed without access control'
    })


@healthcare_bp.route('/api/v1/healthcare/lab-results/export')
def lab_results_export():
    """Lab results export - PHI exposure"""
    include_phi = request.args.get('include_phi', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 1000))
    exports = []

    for record in list(medical_records_db.values())[:limit]:
        payload = {
            'record_id': record.get('record_id'),
            'patient_id': record.get('patient_id'),
            'lab_results': record.get('lab_results', ['A1C: 7.2', 'LDL: 128'])
        }
        if include_phi:
            payload['patient_name'] = record.get('patient_name')
            payload['ssn'] = record.get('ssn')
        exports.append(payload)

    return jsonify({
        'results': exports,
        'include_phi': include_phi,
        'count': len(exports),
        'warning': 'Lab results exported without authorization'
    })


@healthcare_bp.route('/api/v1/healthcare/imaging/<record_id>/download')
def imaging_download(record_id):
    """Imaging download - IDOR vulnerability"""
    include_phi = request.args.get('include_phi', 'false').lower() == 'true'
    record = medical_records_db.get(record_id, {'record_id': record_id, 'patient_id': f'PAT-{random.randint(1000, 9999)}'})
    payload = {
        'record_id': record_id,
        'study_id': f'IMG-{uuid.uuid4().hex[:6]}',
        'modality': random.choice(['CT', 'MRI', 'XRAY']),
        'download_url': f'/static/imaging/{record_id}.dcm'
    }
    if include_phi:
        payload['patient_id'] = record.get('patient_id')
        payload['patient_name'] = record.get('patient_name', 'Unknown')

    return jsonify({
        'imaging': payload,
        'include_phi': include_phi,
        'warning': 'Imaging record downloaded without authorization'
    })


# ============================================================================
# TELEHEALTH & PHARMACY SERVICES
# ============================================================================

@healthcare_bp.route('/api/v1/healthcare/telehealth/session', methods=['POST'])
def telehealth_session():
    """Telehealth session access - session hijack vulnerability"""
    data = request.get_json() or {}
    session_id = data.get('session_id', f'TELE-{uuid.uuid4().hex[:6]}')

    session_payload = {
        'session_id': session_id,
        'provider_id': data.get('provider_id', f'PROV-{random.randint(100, 999)}'),
        'patient_id': data.get('patient_id', f'PAT-{random.randint(1000, 9999)}'),
        'recording_enabled': data.get('force_recording', False),
        'bypass_waiting_room': data.get('bypass_waiting_room', False),
        'status': 'connected'
    }
    telehealth_sessions_db[session_id] = session_payload

    return jsonify({
        'session': session_payload,
        'warning': 'Telehealth session joined without authorization'
    })


@healthcare_bp.route('/api/v1/healthcare/pharmacy/prior-auth', methods=['POST'])
def pharmacy_prior_auth():
    """Prior authorization override - approval bypass"""
    data = request.get_json() or {}
    auth_id = f'PA-{uuid.uuid4().hex[:8]}'

    auth_record = {
        'auth_id': auth_id,
        'patient_id': data.get('patient_id'),
        'drug_code': data.get('drug_code'),
        'force_approval': data.get('force_approval', False),
        'status': 'approved',
        'approved_at': datetime.now().isoformat()
    }
    prior_auth_db[auth_id] = auth_record

    return jsonify({
        'prior_auth': auth_record,
        'warning': 'Prior authorization approved without review'
    }), 201


# ============================================================================
# INSURANCE - Claims and Coverage (from insurance blueprint)
# ============================================================================

@healthcare_bp.route('/api/v1/insurance/policies')
def list_policies():
    """List insurance policies"""
    # Vulnerability: Exposes all policies without authorization

    policies = [
        {
            'policy_id': f'POL-{uuid.uuid4().hex[:8]}',
            'policy_number': f'HI{random.randint(100000000, 999999999)}',
            'patient_id': f'PAT-{random.randint(1000, 9999)}',
            'patient_name': random.choice(['John Smith', 'Jane Doe', 'Robert Johnson']),
            'insurance_provider': random.choice(['Blue Cross', 'Aetna', 'UnitedHealthcare', 'Cigna']),
            'policy_type': random.choice(['PPO', 'HMO', 'EPO', 'POS']),
            'coverage_start': '2025-01-01',
            'coverage_end': '2025-12-31',
            'deductible': random.randint(1000, 5000),
            'out_of_pocket_max': random.randint(5000, 10000),
            'premium_monthly': random.randint(300, 1200)
        }
        for _ in range(10)
    ]

    return jsonify({
        'policies': policies,
        'total_count': len(policies)
    })


@healthcare_bp.route('/api/v1/insurance/claims', methods=['POST'])
def submit_claim():
    """Submit insurance claim"""
    # Vulnerability: Can submit claims for any policy
    # Vulnerability: No validation of claim amounts

    data = request.get_json() or {}
    claim_id = f'CLM-{uuid.uuid4().hex[:8]}'

    claim = {
        'claim_id': claim_id,
        'policy_number': data.get('policy_number'),
        'patient_id': data.get('patient_id'),
        'provider_id': data.get('provider_id'),
        'service_date': data.get('service_date'),
        'diagnosis_codes': data.get('diagnosis_codes', []),
        'procedure_codes': data.get('procedure_codes', []),
        'billed_amount': data.get('billed_amount', 0),
        'status': 'submitted',
        'submitted_date': datetime.now().isoformat()
    }

    claims_db[claim_id] = claim

    return jsonify({
        'status': 'submitted',
        'claim': claim
    })


@healthcare_bp.route('/api/v1/insurance/claims/<claim_id>')
def get_claim_status(claim_id):
    """Get claim status - IDOR vulnerability"""
    # Vulnerability: Can check status of any claim

    if claim_id in claims_db:
        return jsonify(claims_db[claim_id])

    # Return mock data for any claim_id
    return jsonify({
        'claim_id': claim_id,
        'status': random.choice(['submitted', 'processing', 'approved', 'denied', 'paid']),
        'billed_amount': random.randint(100, 10000),
        'approved_amount': random.randint(50, 8000),
        'patient_responsibility': random.randint(20, 2000),
        'processing_date': datetime.now().isoformat()
    })


@healthcare_bp.route('/api/v1/insurance/coverage')
def check_coverage():
    """Check coverage - Exposes policy details"""
    # Vulnerability: Can check coverage for any policy

    policy_number = request.args.get('policy_number', '')
    procedure_code = request.args.get('procedure_code', '')

    return jsonify({
        'policy_number': policy_number,
        'procedure_code': procedure_code,
        'covered': random.choice([True, False]),
        'coverage_percentage': random.choice([80, 90, 100]),
        'requires_preauth': random.choice([True, False]),
        'in_network': random.choice([True, False]),
        'estimated_patient_cost': random.randint(50, 2000)
    })


# ============================================================================
# HEALTHCARE INSURANCE - V1 PREFIXED ROUTES
# ============================================================================

@healthcare_bp.route('/api/v1/healthcare/insurance/claims', methods=['POST'])
def healthcare_insurance_claims():
    """Submit insurance claim (healthcare namespace)"""
    data = request.get_json() or {}
    claim_id = f'CLM-{uuid.uuid4().hex[:8]}'

    claim = {
        'claim_id': claim_id,
        'policy_number': data.get('policy_number'),
        'patient_id': data.get('patient_id'),
        'billed_amount': data.get('billed_amount', 0),
        'status': 'submitted',
        'submitted_date': datetime.now().isoformat(),
        'bypass_validation': data.get('bypass_validation', False)
    }
    claims_db[claim_id] = claim

    return jsonify({
        'status': 'submitted',
        'claim': claim,
        'warning': 'Claim accepted without authorization'
    })


@healthcare_bp.route('/api/v1/healthcare/insurance/eligibility')
def healthcare_insurance_eligibility():
    """Eligibility check - IDOR exposure"""
    member_id = request.args.get('member_id', f'MEM-{random.randint(1000, 9999)}')
    include_pii = request.args.get('include_pii', 'false').lower() == 'true'

    eligibility = {
        'member_id': member_id,
        'eligible': True,
        'plan': random.choice(['PPO', 'HMO', 'EPO']),
        'copay': random.randint(20, 75),
        'deductible_remaining': random.randint(0, 5000)
    }
    if include_pii:
        eligibility['ssn'] = f'{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}'

    eligibility_checks_db[member_id] = eligibility

    return jsonify({
        'eligibility': eligibility,
        'warning': 'Eligibility returned without authorization'
    })


@healthcare_bp.route('/api/v1/healthcare/insurance/preauth', methods=['POST'])
def healthcare_insurance_preauth():
    """Pre-authorization override"""
    data = request.get_json() or {}
    preauth_id = f'PRE-{uuid.uuid4().hex[:8]}'

    record = {
        'preauth_id': preauth_id,
        'procedure_code': data.get('procedure_code'),
        'force_approval': data.get('force_approval', False),
        'status': 'approved',
        'approved_at': datetime.now().isoformat()
    }

    return jsonify({
        'preauth': record,
        'warning': 'Pre-authorization approved without review'
    }), 201


# ============================================================================
# LEGACY ENDPOINTS - Additional PHI Exposure
# ============================================================================

@healthcare_bp.route('/api/hipaa/directory')
def hipaa_directory():
    """Healthcare system discovery - reconnaissance target"""
    return jsonify({
        'healthcare_systems': [
            {
                'system_id': 'HS-001',
                'name': 'City General Hospital Network',
                'type': 'hospital_network',
                'locations': 12,
                'specialties': ['emergency', 'surgery', 'cardiology', 'oncology']
            },
            {
                'system_id': 'HS-002',
                'name': 'Mental Health Associates',
                'type': 'behavioral_health',
                'locations': 5,
                'specialties': ['psychiatry', 'therapy', 'addiction']
            }
        ],
        'total_providers': 2847,
        'hipaa_compliance_version': '2013',
        'api_endpoints': {
            'providers': '/api/providers/',
            'medical_records': '/api/v1/healthcare/records/',
            'phi_access': '/api/medical/phi/'
        }
    })


@healthcare_bp.route('/api/medical/phi/endpoints')
def medical_phi_endpoints():
    """PHI access points discovery - HIPAA violation vector"""
    return jsonify({
        'phi_endpoints': [
            '/api/v1/healthcare/records',
            '/api/medical/genetics/profiles',
            '/api/medical/mental-health/sessions',
            '/api/v1/healthcare/prescriptions/history',
            '/api/medical/lab-results/download'
        ],
        'access_levels': {
            'patient': 'own_records_only',
            'provider': 'assigned_patients',
            'admin': 'all_records',
            'emergency': 'break_glass_access'
        },
        'encryption_required': True,
        'audit_logging': True
    })


@healthcare_bp.route('/api/medical/genetics/profiles')
def medical_genetics_profiles():
    """Genetic information theft - highly sensitive PHI"""
    patient_id = request.args.get('patient_id', f'PAT-{random.randint(1000, 9999)}')

    # Vulnerability: No authorization check for highly sensitive genetic data
    return jsonify({
        'patient_id': patient_id,
        'genetic_profile': {
            'genome_sequenced': True,
            'sequence_date': '2024-03-15',
            'risk_factors': [
                {'condition': 'Breast Cancer', 'gene': 'BRCA1', 'risk_level': 'high', 'percentage': 65},
                {'condition': 'Alzheimers', 'gene': 'APOE4', 'risk_level': 'moderate', 'percentage': 45},
                {'condition': 'Type 2 Diabetes', 'gene': 'TCF7L2', 'risk_level': 'moderate', 'percentage': 38}
            ],
            'pharmacogenomics': {
                'warfarin_sensitivity': 'high',
                'codeine_metabolism': 'poor',
                'statin_response': 'normal'
            },
            'ancestry': {
                'european': 62.3,
                'african': 18.7,
                'asian': 12.1,
                'native_american': 6.9
            }
        },
        'warning': 'Highly sensitive genetic data exposed without authorization'
    })


@healthcare_bp.route('/api/medical/mental-health/sessions')
def medical_mental_health_sessions():
    """Mental health records - highly sensitive PHI"""
    patient_id = request.args.get('patient_id', f'PAT-{random.randint(1000, 9999)}')

    # Vulnerability: Mental health records exposed without authorization
    sessions = [
        {
            'session_id': f'SESSION-{uuid.uuid4().hex[:8]}',
            'date': (datetime.now() - timedelta(days=days)).isoformat(),
            'therapist': random.choice(['Dr. Sarah Miller', 'Dr. James Chen', 'Dr. Emily Rodriguez']),
            'session_type': random.choice(['individual', 'group', 'family']),
            'diagnosis': random.choice(['Major Depressive Disorder', 'Generalized Anxiety Disorder', 'PTSD', 'Bipolar Disorder']),
            'notes': 'Patient discussed ongoing challenges with...',
            'medications_prescribed': random.choice([
                ['Sertraline 50mg', 'Alprazolam 0.5mg'],
                ['Escitalopram 10mg'],
                ['Aripiprazole 5mg', 'Lithium 300mg']
            ]),
            'risk_assessment': {
                'suicide_risk': random.choice(['low', 'moderate']),
                'self_harm_risk': random.choice(['low', 'moderate']),
                'violence_risk': 'low'
            }
        }
        for days in [7, 14, 21, 28, 35, 42]
    ]

    return jsonify({
        'patient_id': patient_id,
        'mental_health_sessions': sessions,
        'total_sessions': len(sessions),
        'warning': 'Highly sensitive mental health data exposed'
    })


@healthcare_bp.route('/api/hipaa/export/bulk')
def hipaa_bulk_export():
    """Mass HIPAA data extraction - data exfiltration"""
    # Vulnerability: Bulk export without proper authorization
    # Vulnerability: No rate limiting or audit logging

    export_format = request.args.get('format', 'json')
    record_count = int(request.args.get('count', 100))

    export_id = f'EXPORT-{uuid.uuid4().hex[:8]}'

    return jsonify({
        'export_id': export_id,
        'format': export_format,
        'record_count': record_count,
        'status': 'completed',
        'download_url': f'/api/hipaa/export/{export_id}/download',
        'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
        'warning': 'Bulk PHI export without authorization or audit logging'
    })


@healthcare_bp.route('/api/hipaa/transfer/encrypted', methods=['POST'])
def hipaa_transfer_encrypted():
    """HIPAA data transfer - SSRF vulnerability"""
    # Vulnerability: SSRF through unvalidated destination URL
    # Vulnerability: Insecure data transfer

    data = request.get_json() or {}
    destination = data.get('destination', '')
    patient_ids = data.get('patient_ids', [])

    # Vulnerability: No URL validation allows SSRF
    if destination:
        if any(keyword in destination.lower() for keyword in ['localhost', '127.0.0.1', '169.254', '10.', '192.168', 'metadata']):
            return jsonify({
                'vulnerability': 'SSRF_DETECTED',
                'destination': destination,
                'message': 'Internal network access detected',
                'accessible_services': [
                    'http://localhost:8080/admin',
                    'http://169.254.169.254/latest/meta-data/',
                    'http://10.0.0.5:3306/mysql'
                ]
            })

    transfer_id = f'TRANSFER-{uuid.uuid4().hex[:8]}'

    return jsonify({
        'transfer_id': transfer_id,
        'destination': destination,
        'patient_count': len(patient_ids),
        'status': 'completed',
        'encryption': 'none',  # Vulnerability: No actual encryption
        'warning': 'Data transferred without proper encryption'
    })


@healthcare_bp.route('/api/hipaa/system/configuration', methods=['POST'])
def hipaa_system_configuration():
    """HIPAA system configuration - XXE vulnerability"""
    # Vulnerability: XXE injection through XML configuration
    # Vulnerability: Deserialization attack

    data = request.get_json() or {}
    config_xml = data.get('config_xml', '')
    config_serialized = data.get('config_data', '')

    # Vulnerability: XXE injection detection
    if config_xml and any(keyword in config_xml for keyword in ['<!ENTITY', '<!DOCTYPE', 'SYSTEM']):
        return jsonify({
            'vulnerability': 'XXE_INJECTION_DETECTED',
            'message': 'External entity processing enabled',
            'exposed_files': [
                '/etc/passwd',
                '/etc/shadow',
                '/app/config/database.yml',
                '/app/config/secrets.json'
            ],
            'file_content': 'root:x:0:0:root:/root:/bin/bash\n...'
        })

    # Vulnerability: Insecure deserialization
    if config_serialized:
        try:
            # Simulate deserialization vulnerability
            decoded = base64.b64decode(config_serialized)
            if b'pickle' in decoded or b'__reduce__' in decoded:
                return jsonify({
                    'vulnerability': 'INSECURE_DESERIALIZATION',
                    'message': 'Arbitrary code execution possible',
                    'payload_executed': True
                })
        except:
            pass

    return jsonify({
        'status': 'configuration_updated',
        'warning': 'XML processing vulnerable to XXE, deserialization vulnerable to RCE'
    })


@healthcare_bp.route('/api/hipaa/audit-logs', methods=['PUT'])
def hipaa_audit_logs():
    """HIPAA audit log manipulation - evidence tampering"""
    # Vulnerability: Can modify or delete audit logs
    # Vulnerability: No integrity protection

    data = request.get_json() or {}
    action = data.get('action', '')
    target_logs = data.get('target_logs', [])

    if action == 'delete':
        return jsonify({
            'status': 'deleted',
            'logs_deleted': len(target_logs),
            'warning': 'HIPAA audit logs deleted - compliance violation',
            'recovery_possible': False
        })
    elif action == 'modify':
        return jsonify({
            'status': 'modified',
            'logs_modified': len(target_logs),
            'warning': 'HIPAA audit logs modified - evidence tampering',
            'integrity_check': 'failed'
        })

    return jsonify({
        'status': 'unknown_action',
        'action': action
    })
