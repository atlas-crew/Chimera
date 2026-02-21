"""Unit tests for insurance routes."""

from app.models import claims_db, policies_db


def test_claim_submit(client):
    response = client.post(
        '/api/claims/submit',
        json={'policy_number': 'POL-123', 'claim_type': 'auto', 'claim_amount': 2500}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['claim']['policy_number'] == 'POL-123'


def test_claims_history(client):
    claims_db['CLM-TEST'] = {
        'claim_id': 'CLM-TEST',
        'policy_number': 'POL-999',
        'claim_type': 'home',
        'claim_amount': 54000,
        'status': 'submitted'
    }

    response = client.get('/api/claims/history?policy_number=POL-999')
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 1


def test_policy_limits_update(client):
    policies_db['POL-555'] = {
        'policy_id': 'POL-555',
        'coverage_limit': 100000,
        'status': 'active',
        'overrides': []
    }

    response = client.put(
        '/api/policies/POL-555/limits',
        json={'coverage_limit': 250000}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['new_limit'] == 250000


def test_policy_endorsement_tamper(client):
    response = client.post(
        '/api/v1/insurance/policies/POL-777/endorse',
        json={'type': 'coverage_change', 'override_checks': True}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['endorsement']['override_checks'] is True


def test_policy_cancel_override(client):
    response = client.put(
        '/api/v1/insurance/policies/POL-777/cancel',
        json={'bypass_validation': True}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['policy']['status'] == 'cancelled'


def test_claim_settlement_override(client):
    response = client.post(
        '/api/v1/insurance/claims/settlement',
        json={'claim_id': 'claim-1', 'amount': 500000, 'override_limits': True}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['settlement']['override_limits'] is True
