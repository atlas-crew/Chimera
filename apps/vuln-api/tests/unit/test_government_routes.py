"""Unit tests for government routes."""


def test_get_case_details(client):
    response = client.get('/api/v1/gov/cases/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['case_id'] == '1'
    assert 'citizen_id' in data


def test_benefits_search_sql_injection(client):
    response = client.get("/api/v1/gov/benefits/search?q=' OR '1'='1")
    assert response.status_code == 200
    data = response.get_json()
    assert data['vulnerability'] == 'SQL_INJECTION_DETECTED'


def test_service_request_tampering(client):
    response = client.post(
        '/api/v1/gov/service-requests',
        json={'request_type': 'priority_override', 'priority': 'critical', 'bypass_validation': True}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['service_request']['priority'] == 'critical'


def test_benefits_eligibility_override(client):
    response = client.put(
        '/api/v1/gov/benefits/APP-1001/eligibility',
        json={'eligible': True, 'override_checks': True}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['application']['override_checks'] is True


def test_case_reassignment(client):
    response = client.put(
        '/api/v1/gov/cases/1/reassign',
        json={'assigned_agent': 'AGT-999', 'override_policy': True}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['new_agent'] == 'AGT-999'


def test_licenses_export(client):
    response = client.get('/api/v1/gov/licenses/export?include_pii=true')
    assert response.status_code == 200
    data = response.get_json()
    assert data['include_pii'] is True
