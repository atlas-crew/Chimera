"""
Unit tests for Healthcare Routes (WS4).

Tests cover:
- Patient record operations and PHI exposure
- IDOR vulnerabilities
- SQL injection in search endpoints
- Path traversal in file uploads
- SSRF vulnerabilities
- XXE injection
- Prescription handling
- Insurance operations
- Genetic and mental health data exposure
"""

import json
import base64
import pytest
from datetime import datetime


class TestPatientRecords:
    """Test patient record endpoints and PHI exposure vulnerabilities."""

    def test_list_records_no_auth(self, client, mock_medical_records):
        """Test that medical records are exposed without authentication."""
        response = client.get('/api/v1/healthcare/records')

        assert response.status_code == 200
        data = response.get_json()
        assert 'records' in data
        assert len(data['records']) > 0
        assert 'warning' in data
        assert 'PHI' in data['warning']

        # Verify PHI data is exposed
        record = data['records'][0]
        assert 'ssn' in record
        assert 'patient_name' in record
        assert 'diagnosis' in record

    def test_list_records_phi_exposure(self, client, mock_medical_records):
        """Test that sensitive PHI fields are exposed."""
        response = client.get('/api/v1/healthcare/records')
        data = response.get_json()

        for record in data['records']:
            # All PHI fields should be present
            assert 'ssn' in record
            assert 'dob' in record
            assert 'diagnosis' in record
            assert 'medications' in record
            assert 'patient_name' in record

    def test_get_record_details_idor(self, client, mock_medical_records):
        """Test IDOR vulnerability in record details endpoint."""
        # Can access any record without authorization
        response = client.get('/api/v1/healthcare/records/REC-001')

        assert response.status_code == 200
        data = response.get_json()
        assert data['record_id'] == 'REC-001'
        assert 'patient_info' in data
        assert 'ssn' in data['patient_info']
        assert 'medical_info' in data
        assert 'provider_notes' in data

    def test_get_record_nonexistent(self, client):
        """Test accessing non-existent record."""
        response = client.get('/api/v1/healthcare/records/REC-999')
        assert response.status_code == 404

    def test_record_details_complete_phi(self, client, mock_medical_records):
        """Test that complete PHI is exposed in details."""
        response = client.get('/api/v1/healthcare/records/REC-001')
        data = response.get_json()

        # Patient info PHI
        assert data['patient_info']['ssn'] == '123-45-6789'
        assert data['patient_info']['dob'] == '1980-05-15'
        assert 'address' in data['patient_info']
        assert 'phone' in data['patient_info']
        assert 'insurance_id' in data['patient_info']

        # Medical info PHI
        assert 'diagnosis' in data['medical_info']
        assert 'medications' in data['medical_info']
        assert 'allergies' in data['medical_info']


class TestRecordSearch:
    """Test search functionality and SQL injection vulnerabilities."""

    def test_search_sql_injection_detection(self, client, sql_injection_payloads):
        """Test SQL injection vulnerability in search endpoint."""
        for payload in sql_injection_payloads[:3]:  # Test subset
            response = client.get(f'/api/v1/healthcare/records/search?q={payload}')

            assert response.status_code == 200
            data = response.get_json()

            if 'vulnerability' in data:
                assert data['vulnerability'] == 'SQL_INJECTION_DETECTED'
                assert 'exposed_data' in data
                assert 'admin_credentials' in data['exposed_data']

    def test_search_union_injection(self, client):
        """Test UNION-based SQL injection."""
        payload = "' UNION SELECT * FROM users--"
        response = client.get(f'/api/v1/healthcare/records/search?q={payload}')

        data = response.get_json()
        assert data['vulnerability'] == 'SQL_INJECTION_DETECTED'
        assert 'query' in data
        assert 'UNION' in data['query']

    def test_search_boolean_injection(self, client):
        """Test boolean-based SQL injection."""
        payload = "' OR '1'='1"
        response = client.get(f'/api/v1/healthcare/records/search?q={payload}')

        data = response.get_json()
        assert response.status_code == 200

    def test_search_by_ssn_enumeration(self, client, mock_medical_records):
        """Test SSN-based search allows enumeration."""
        response = client.get('/api/v1/healthcare/records/search?ssn=123-45-6789')

        data = response.get_json()
        assert response.status_code == 200
        assert 'results' in data
        # SSN should be searchable, exposing records
        if len(data['results']) > 0:
            assert 'ssn' in data['results'][0]

    def test_search_normal_query(self, client, mock_medical_records):
        """Test normal search returns results."""
        response = client.get('/api/v1/healthcare/records/search?name=John')

        data = response.get_json()
        assert response.status_code == 200
        assert 'results' in data


class TestFileUpload:
    """Test file upload and path traversal vulnerabilities."""

    def test_upload_path_traversal_detection(self, client, path_traversal_payloads):
        """Test path traversal vulnerability in file upload."""
        for payload in path_traversal_payloads[:3]:
            response = client.post(
                '/api/v1/healthcare/records/upload',
                json={
                    'record_id': 'REC-001',
                    'filename': payload,
                    'content': 'malicious content'
                }
            )

            data = response.get_json()
            assert response.status_code == 200
            assert data['vulnerability'] == 'PATH_TRAVERSAL'
            assert 'potential_paths' in data

    def test_upload_etc_passwd_traversal(self, client):
        """Test specific path traversal to /etc/passwd."""
        response = client.post(
            '/api/v1/healthcare/records/upload',
            json={
                'record_id': 'REC-001',
                'filename': '../../../etc/passwd',
                'content': 'test'
            }
        )

        data = response.get_json()
        assert data['vulnerability'] == 'PATH_TRAVERSAL'
        assert '/etc/passwd' in str(data['potential_paths'])

    def test_upload_config_traversal(self, client):
        """Test path traversal to config files."""
        response = client.post(
            '/api/v1/healthcare/records/upload',
            json={
                'record_id': 'REC-001',
                'filename': '../../config/database.yml',
                'content': 'test'
            }
        )

        data = response.get_json()
        assert data['vulnerability'] == 'PATH_TRAVERSAL'

    def test_upload_normal_file(self, client):
        """Test normal file upload without traversal."""
        response = client.post(
            '/api/v1/healthcare/records/upload',
            json={
                'record_id': 'REC-001',
                'filename': 'document.pdf',
                'content': 'legitimate content'
            }
        )

        data = response.get_json()
        assert response.status_code == 200
        assert data['status'] == 'uploaded'
        assert 'warning' in data  # Still vulnerable to unrestricted upload


class TestAppointments:
    """Test appointment management and authorization vulnerabilities."""

    def test_list_appointments_no_auth(self, client):
        """Test appointments are exposed without authentication."""
        response = client.get('/api/v1/healthcare/appointments')

        assert response.status_code == 200
        data = response.get_json()
        assert 'appointments' in data
        assert len(data['appointments']) > 0

        # Verify PHI exposure
        appt = data['appointments'][0]
        assert 'patient_name' in appt
        assert 'reason' in appt

    def test_schedule_appointment_no_validation(self, client):
        """Test scheduling appointment without provider verification."""
        response = client.post(
            '/api/v1/healthcare/appointments/schedule',
            json={
                'patient_id': 'PAT-1001',
                'provider_id': 'PROV-999',  # Can use any provider
                'date': '2025-11-01T10:00:00',
                'reason': 'Test appointment'
            }
        )

        data = response.get_json()
        assert response.status_code == 200
        assert data['status'] == 'scheduled'
        assert 'warning' in data

    def test_cancel_appointment_idor(self, client):
        """Test IDOR vulnerability in appointment cancellation."""
        response = client.post(
            '/api/v1/healthcare/appointments/cancel',
            json={'appointment_id': 'APT-12345678'}
        )

        data = response.get_json()
        assert response.status_code == 200
        assert data['status'] == 'cancelled'
        assert 'warning' in data
        assert 'authorization' in data['warning'].lower()


class TestPrescriptions:
    """Test prescription endpoints and controlled substance vulnerabilities."""

    def test_list_prescriptions_controlled_substances(self, client):
        """Test that controlled substances are exposed without authorization."""
        response = client.get('/api/v1/healthcare/prescriptions')

        assert response.status_code == 200
        data = response.get_json()
        assert 'prescriptions' in data
        assert len(data['prescriptions']) > 0
        assert 'warning' in data
        assert 'DEA' in data['warning']

        # Verify controlled substance details exposed
        rx = data['prescriptions'][0]
        assert 'dea_schedule' in rx
        assert 'provider_dea' in rx

    def test_prescription_refill_no_verification(self, client):
        """Test refill request without provider verification."""
        response = client.post(
            '/api/v1/healthcare/prescriptions/refill',
            json={
                'prescription_id': 'RX-12345678',
                'patient_id': 'PAT-1001'
            }
        )

        data = response.get_json()
        assert response.status_code == 200
        assert data['status'] == 'approved'
        assert 'warning' in data
        assert 'verification' in data['warning'].lower()

    def test_prescription_history_idor(self, client):
        """Test IDOR in prescription history endpoint."""
        response = client.get('/api/v1/healthcare/prescriptions/history?patient_id=PAT-9999')

        assert response.status_code == 200
        data = response.get_json()
        assert 'prescription_history' in data
        assert len(data['prescription_history']) > 0


class TestInsurance:
    """Test insurance operations and claim vulnerabilities."""

    def test_list_policies_no_auth(self, client):
        """Test insurance policies exposed without authorization."""
        response = client.get('/api/v1/insurance/policies')

        assert response.status_code == 200
        data = response.get_json()
        assert 'policies' in data
        assert len(data['policies']) > 0

    def test_submit_claim_no_validation(self, client):
        """Test claim submission without validation."""
        response = client.post(
            '/api/v1/insurance/claims',
            json={
                'policy_number': 'HI999999999',
                'patient_id': 'PAT-1001',
                'provider_id': 'PROV-501',
                'service_date': '2025-10-01',
                'billed_amount': 99999  # No amount validation
            }
        )

        data = response.get_json()
        assert response.status_code == 200
        assert data['status'] == 'submitted'
        assert data['claim']['billed_amount'] == 99999

    def test_get_claim_status_idor(self, client, mock_claims):
        """Test IDOR vulnerability in claim status check."""
        response = client.get('/api/v1/insurance/claims/CLM-001')

        assert response.status_code == 200
        data = response.get_json()
        assert data['claim_id'] == 'CLM-001'

    def test_check_coverage_enumeration(self, client):
        """Test coverage check allows policy enumeration."""
        response = client.get(
            '/api/v1/insurance/coverage?policy_number=HI123456789&procedure_code=99213'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'covered' in data
        assert 'coverage_percentage' in data


class TestLegacyEndpoints:
    """Test legacy HIPAA endpoints and vulnerabilities."""

    def test_hipaa_directory_exposure(self, client):
        """Test HIPAA directory exposes system information."""
        response = client.get('/api/hipaa/directory')

        assert response.status_code == 200
        data = response.get_json()
        assert 'healthcare_systems' in data
        assert 'total_providers' in data
        assert 'api_endpoints' in data

    def test_phi_endpoints_discovery(self, client):
        """Test PHI endpoints are discoverable."""
        response = client.get('/api/medical/phi/endpoints')

        assert response.status_code == 200
        data = response.get_json()
        assert 'phi_endpoints' in data
        assert len(data['phi_endpoints']) > 0
        assert 'access_levels' in data


class TestGeneticData:
    """Test genetic information exposure vulnerabilities."""

    def test_genetics_profile_no_auth(self, client):
        """Test genetic data exposed without authorization."""
        response = client.get('/api/medical/genetics/profiles?patient_id=PAT-1001')

        assert response.status_code == 200
        data = response.get_json()
        assert 'genetic_profile' in data
        assert 'risk_factors' in data['genetic_profile']
        assert 'ancestry' in data['genetic_profile']
        assert 'warning' in data
        assert 'genetic' in data['warning'].lower()

    def test_genetics_profile_complete_exposure(self, client):
        """Test complete genetic profile is exposed."""
        response = client.get('/api/medical/genetics/profiles')

        data = response.get_json()
        profile = data['genetic_profile']
        assert 'risk_factors' in profile
        assert 'pharmacogenomics' in profile
        assert 'ancestry' in profile
        assert len(profile['risk_factors']) > 0


class TestMentalHealth:
    """Test mental health records exposure vulnerabilities."""

    def test_mental_health_sessions_no_auth(self, client):
        """Test mental health records exposed without authorization."""
        response = client.get('/api/medical/mental-health/sessions?patient_id=PAT-1001')

        assert response.status_code == 200
        data = response.get_json()
        assert 'mental_health_sessions' in data
        assert len(data['mental_health_sessions']) > 0
        assert 'warning' in data

    def test_mental_health_sensitive_data(self, client):
        """Test that sensitive mental health data is exposed."""
        response = client.get('/api/medical/mental-health/sessions')

        data = response.get_json()
        session = data['mental_health_sessions'][0]
        assert 'diagnosis' in session
        assert 'notes' in session
        assert 'medications_prescribed' in session
        assert 'risk_assessment' in session


class TestBulkExport:
    """Test bulk data export vulnerabilities."""

    def test_bulk_export_no_auth(self, client):
        """Test bulk PHI export without authorization."""
        response = client.get('/api/hipaa/export/bulk?format=json&count=100')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'completed'
        assert data['record_count'] == 100
        assert 'warning' in data
        assert 'authorization' in data['warning'].lower()

    def test_bulk_export_large_dataset(self, client):
        """Test exporting large dataset without limits."""
        response = client.get('/api/hipaa/export/bulk?count=10000')

        assert response.status_code == 200
        data = response.get_json()
        assert data['record_count'] == 10000


class TestSSRF:
    """Test SSRF vulnerabilities in data transfer."""

    def test_transfer_ssrf_localhost(self, client, ssrf_payloads):
        """Test SSRF to localhost."""
        response = client.post(
            '/api/hipaa/transfer/encrypted',
            json={
                'destination': 'http://localhost:8080/admin',
                'patient_ids': ['PAT-1001']
            }
        )

        data = response.get_json()
        assert data['vulnerability'] == 'SSRF_DETECTED'
        assert 'accessible_services' in data

    def test_transfer_ssrf_metadata(self, client):
        """Test SSRF to cloud metadata service."""
        response = client.post(
            '/api/hipaa/transfer/encrypted',
            json={
                'destination': 'http://169.254.169.254/latest/meta-data/',
                'patient_ids': ['PAT-1001']
            }
        )

        data = response.get_json()
        assert data['vulnerability'] == 'SSRF_DETECTED'

    def test_transfer_ssrf_internal_network(self, client):
        """Test SSRF to internal network."""
        response = client.post(
            '/api/hipaa/transfer/encrypted',
            json={
                'destination': 'http://10.0.0.5:3306/mysql',
                'patient_ids': ['PAT-1001']
            }
        )

        data = response.get_json()
        assert data['vulnerability'] == 'SSRF_DETECTED'

    def test_transfer_normal(self, client):
        """Test normal transfer to external URL."""
        response = client.post(
            '/api/hipaa/transfer/encrypted',
            json={
                'destination': 'https://example.com/api/receive',
                'patient_ids': ['PAT-1001']
            }
        )

        data = response.get_json()
        assert data['status'] == 'completed'
        assert 'warning' in data  # Still warns about no encryption


class TestXXE:
    """Test XXE injection vulnerabilities."""

    def test_xxe_file_inclusion(self, client, xxe_injection_payloads):
        """Test XXE file inclusion vulnerability."""
        response = client.post(
            '/api/hipaa/system/configuration',
            json={'config_xml': xxe_injection_payloads[0]}
        )

        data = response.get_json()
        assert data['vulnerability'] == 'XXE_INJECTION_DETECTED'
        assert 'exposed_files' in data
        assert '/etc/passwd' in data['exposed_files']

    def test_xxe_external_entity(self, client):
        """Test XXE with external entity."""
        xml = """<?xml version="1.0"?>
<!DOCTYPE foo [
<!ENTITY xxe SYSTEM "file:///etc/shadow">
]>
<foo>&xxe;</foo>"""

        response = client.post(
            '/api/hipaa/system/configuration',
            json={'config_xml': xml}
        )

        data = response.get_json()
        assert data['vulnerability'] == 'XXE_INJECTION_DETECTED'


class TestDeserialization:
    """Test insecure deserialization vulnerabilities."""

    def test_insecure_deserialization_pickle(self, client, deserialization_payloads):
        """Test insecure deserialization with pickle payload."""
        response = client.post(
            '/api/hipaa/system/configuration',
            json={'config_data': deserialization_payloads[0]}
        )

        data = response.get_json()
        assert data['vulnerability'] == 'INSECURE_DESERIALIZATION'
        assert data['message'] == 'Arbitrary code execution possible'

    def test_deserialization_rce(self, client):
        """Test RCE via deserialization."""
        malicious_payload = base64.b64encode(b'pickle___reduce__malicious').decode()

        response = client.post(
            '/api/hipaa/system/configuration',
            json={'config_data': malicious_payload}
        )

        data = response.get_json()
        assert data['vulnerability'] == 'INSECURE_DESERIALIZATION'


class TestAuditLogManipulation:
    """Test audit log tampering vulnerabilities."""

    def test_delete_audit_logs(self, client):
        """Test ability to delete HIPAA audit logs."""
        response = client.put(
            '/api/hipaa/audit-logs',
            json={
                'action': 'delete',
                'target_logs': ['log-001', 'log-002', 'log-003']
            }
        )

        data = response.get_json()
        assert response.status_code == 200
        assert data['status'] == 'deleted'
        assert data['logs_deleted'] == 3
        assert 'warning' in data
        assert 'HIPAA' in data['warning']

    def test_modify_audit_logs(self, client):
        """Test ability to modify HIPAA audit logs."""
        response = client.put(
            '/api/hipaa/audit-logs',
            json={
                'action': 'modify',
                'target_logs': ['log-001']
            }
        )

        data = response.get_json()
        assert data['status'] == 'modified'
        assert data['integrity_check'] == 'failed'


class TestSecurityControls:
    """Test missing security controls across healthcare endpoints."""

    def test_no_rate_limiting(self, client, mock_medical_records):
        """Test absence of rate limiting on sensitive endpoints."""
        # Make multiple rapid requests
        for _ in range(10):
            response = client.get('/api/v1/healthcare/records')
            assert response.status_code == 200

    def test_no_audit_logging(self, client, mock_medical_records):
        """Test that sensitive operations aren't audited."""
        # Access sensitive data
        response = client.get('/api/v1/healthcare/records/REC-001')
        assert response.status_code == 200
        # No audit trail is created (verified by inspection)

    def test_no_encryption_in_transit_warning(self, client):
        """Test warning about missing encryption."""
        response = client.post(
            '/api/hipaa/transfer/encrypted',
            json={
                'destination': 'https://example.com',
                'patient_ids': ['PAT-1001']
            }
        )

        data = response.get_json()
        assert data['encryption'] == 'none'


class TestCriticalVulnerabilities:
    """Test critical security vulnerabilities requiring immediate attention."""

    def test_critical_phi_exposure_without_auth(self, client, mock_medical_records):
        """Critical: PHI exposed without any authentication."""
        response = client.get('/api/v1/healthcare/records')

        assert response.status_code == 200
        data = response.get_json()
        # This is a critical HIPAA violation
        assert any('ssn' in record for record in data['records'])

    def test_critical_sql_injection_data_breach(self, client):
        """Critical: SQL injection enables database compromise."""
        response = client.get('/api/v1/healthcare/records/search?q=\' UNION SELECT * FROM users--')

        data = response.get_json()
        if 'vulnerability' in data:
            # Admin credentials exposed via SQL injection
            assert 'admin_credentials' in data['exposed_data']

    def test_critical_genetic_data_exposure(self, client):
        """Critical: Genetic information exposed without consent."""
        response = client.get('/api/medical/genetics/profiles?patient_id=PAT-1001')

        data = response.get_json()
        # Genetic data is highest sensitivity PHI
        assert 'genetic_profile' in data
        assert 'risk_factors' in data['genetic_profile']

    def test_critical_audit_log_deletion(self, client):
        """Critical: Audit logs can be deleted to hide evidence."""
        response = client.put(
            '/api/hipaa/audit-logs',
            json={'action': 'delete', 'target_logs': ['all']}
        )

        data = response.get_json()
        assert data['recovery_possible'] is False


class TestProviderAndImaging:
    """Test provider directory and imaging export vulnerabilities."""

    def test_provider_directory_idor(self, client):
        response = client.get('/api/v1/healthcare/providers/PROV-777')
        assert response.status_code == 200
        data = response.get_json()
        assert data['provider']['provider_id'] == 'PROV-777'

    def test_imaging_download_idor(self, client, mock_medical_records):
        response = client.get('/api/v1/healthcare/imaging/REC-001/download?include_phi=true')
        assert response.status_code == 200
        data = response.get_json()
        assert data['imaging']['record_id'] == 'REC-001'
        assert data['include_phi'] is True

    def test_lab_results_export(self, client, mock_medical_records):
        response = client.get('/api/v1/healthcare/lab-results/export?include_phi=true')
        assert response.status_code == 200
        data = response.get_json()
        assert data['include_phi'] is True
        assert isinstance(data['results'], list)
