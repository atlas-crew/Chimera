"""Unit tests for banking routes."""


def test_wire_transfer_bypass(client):
    response = client.post(
        '/api/v1/banking/wire-transfer',
        json={'amount': 250000, 'beneficiary': 'Recipient', 'bypass_aml': True}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['wire']['bypass_aml'] is True


def test_beneficiary_idor(client):
    response = client.get('/api/v1/banking/beneficiaries/BEN-1001')
    assert response.status_code == 200
    data = response.get_json()
    assert data['beneficiary']['beneficiary_id'] == 'BEN-1001'


def test_kyc_documents_export(client):
    response = client.get('/api/v1/banking/kyc/documents/export?include_pii=true')
    assert response.status_code == 200
    data = response.get_json()
    assert data['include_pii'] is True
