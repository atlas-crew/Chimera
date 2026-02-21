"""Unit tests for ecommerce routes."""


def test_gift_card_balance_scrape(client):
    response = client.get('/api/v1/ecommerce/gift-cards/GC-1001/balance')
    assert response.status_code == 200
    data = response.get_json()
    assert data['gift_card']['code'] == 'GC-1001'


def test_pricing_override(client):
    response = client.put(
        '/api/v1/ecommerce/pricing/override',
        json={'product_id': 'prod-123', 'override_price': 0.01, 'bypass_approval': True}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['bypass_approval'] is True


def test_orders_export(client):
    response = client.get('/api/v1/ecommerce/orders/export?include_pii=true')
    assert response.status_code == 200
    data = response.get_json()
    assert data['include_pii'] is True
