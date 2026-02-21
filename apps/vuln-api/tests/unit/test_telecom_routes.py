"""Unit tests for telecom routes."""


def test_subscriber_profile_idor(client):
    response = client.get('/api/v1/telecom/subscribers/sub-1/profile')
    assert response.status_code == 200
    data = response.get_json()
    assert data['subscriber']['subscriber_id'] == 'sub-1'


def test_sim_swap_bypass(client):
    response = client.post(
        '/api/v1/telecom/subscribers/sub-1/sim-swap',
        json={'new_sim': 'SIM-999', 'bypass_verification': True}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['swap']['bypass_verification'] is True


def test_porting_export(client):
    response = client.get('/api/v1/telecom/porting/export?include_pii=true')
    assert response.status_code == 200
    data = response.get_json()
    assert data['include_pii'] is True


def test_device_binding_bypass(client):
    response = client.post(
        '/api/v1/telecom/devices/bind',
        json={'subscriber_id': 'sub-1', 'device_id': 'dev-1', 'sim_id': 'SIM-999', 'override_checks': True}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['binding']['override_checks'] is True


def test_imei_blacklist_override(client):
    response = client.put(
        '/api/v1/telecom/imei/blacklist',
        json={'imei': 'IMEI-1001', 'blacklisted': False, 'override_policy': True}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['imei_record']['override_policy'] is True


def test_roaming_override(client):
    response = client.post(
        '/api/v1/telecom/roaming/override',
        json={'subscriber_id': 'sub-1', 'region': 'EU', 'override_policy': True}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['override']['override_policy'] is True
