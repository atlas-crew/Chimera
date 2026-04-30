"""Unit tests for payments routes."""


def test_payment_methods_fall_back_to_session_customer(client, set_session):
    set_session(client, {"customer_id": "cust-session"})

    response = client.get("/api/v1/payments/methods")

    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "cust-session"
    assert data["payment_methods"][0]["method_id"].startswith("PM-cust-session-")


def test_payment_methods_add_uses_session_customer(client, set_session):
    set_session(client, {"customer_id": "cust-session"})

    response = client.post(
        "/api/v1/payments/methods/add",
        json={"card_number": "4111111111111111", "expiry": "12/29", "cvv": "123"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["method"]["customer_id"] == "cust-session"
    assert data["method"]["method_id"].startswith("PM-cust-session-")


def test_cards_validate_returns_luhn_details(client):
    response = client.post(
        "/api/cards/validate",
        json={"card_number": "4111111111111111", "expiry": "12/29", "cvv": "123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["expiry_valid"] is True
    assert data["cvv_valid"] is True
