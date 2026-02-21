"""Unit tests for energy & utilities routes."""


def test_grid_dispatch_override(client):
    response = client.post(
        '/api/v1/energy-utilities/grid/dispatch',
        json={'unit_id': 'gen-1', 'setpoint_mw': 0, 'override_limits': True}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['dispatch']['override_limits'] is True


def test_meter_readings_idor(client):
    response = client.get('/api/v1/energy-utilities/meters/meter-1/readings')
    assert response.status_code == 200
    data = response.get_json()
    assert data['reading']['meter_id'] == 'meter-1'


def test_outage_export(client):
    response = client.get('/api/v1/energy-utilities/outages/export?include_pii=true')
    assert response.status_code == 200
    data = response.get_json()
    assert data['include_pii'] is True


def test_demand_response_override(client):
    response = client.post(
        '/api/v1/energy-utilities/demand-response/dispatch',
        json={'region': 'west', 'percent': 100, 'override_limits': True}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['event']['override_limits'] is True


def test_tariff_override(client):
    response = client.put(
        '/api/v1/energy-utilities/tariffs/override',
        json={'tariff_id': 'tariff-1', 'rate_override': 0.01, 'bypass_review': True}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['tariff']['bypass_review'] is True


def test_der_interconnection_override(client):
    response = client.post(
        '/api/v1/energy-utilities/der/interconnection/approve',
        json={'system_id': 'der-1', 'bypass_review': True}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['interconnection']['bypass_review'] is True
