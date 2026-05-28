"""Unit tests for security ops routes."""


def test_security_monitoring_bypass(asgi_client):
    response = asgi_client.get("/api/security/monitoring/bypass")
    assert response.status_code == 200
    data = response.json()
    assert data["monitoring_disabled"] is True
    assert "log_suppression" in data["strategies"]


def test_threats_indicators(asgi_client):
    response = asgi_client.get("/api/threats/indicators")
    assert response.status_code == 200
    data = response.json()
    assert data["total_indicators"] == 4
    assert data["indicators"][0]["type"] == "ip_address"


def test_incidents_create_rejects_empty_body(asgi_client):
    response = asgi_client.post("/api/incidents/create", content=b"")
    assert response.status_code == 415
    data = response.json()
    assert data["error"] == "Content-Type must be application/json"


def test_defense_metrics(asgi_client):
    response = asgi_client.get("/api/defense/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["metrics_period"] == "24_hours"
    assert "detection_metrics" in data


def test_defense_metrics_fedramp_evidence_is_deterministic(asgi_client):
    response = asgi_client.get("/api/defense/metrics?fedramp=true")
    assert response.status_code == 200
    data = response.json()
    assert data["detection_metrics"]["total_events_processed"] == 2400000
    assert data["vulnerability_metrics"]["systems_scanned"] == 640
    assert data["timestamp"] == "2026-05-01T00:00:00"
    assert data["fedramp_evidence"]["mode"] == "vulnerable"
    assert data["fedramp_evidence"]["controls"] == ["RA-5", "SI-4", "SI-10", "CA-7", "AU-6"]
    assert data["fedramp_evidence"]["risk_findings"][0]["finding_id"] == "FEDRAMP-RA-5-001"


def test_defense_metrics_fedramp_strict_comparison(asgi_client):
    response = asgi_client.get("/api/defense/metrics?fedramp=true&strict_mode=true")
    assert response.status_code == 200
    data = response.json()
    assert data["fedramp_evidence"]["mode"] == "strict"
    assert data["fedramp_evidence"]["risk_findings"][0]["status"] == "blocked"
    assert data["fedramp_evidence"]["strict_comparison"] == {
        "monitoring_disabled": False,
        "unauthorized_metric_tampering": "denied",
    }


def test_defense_metrics_fedramp_flags_are_case_insensitive(asgi_client):
    response = asgi_client.get("/api/defense/metrics?fedramp=True&strict_mode=TRUE")
    assert response.status_code == 200
    data = response.json()
    assert data["fedramp_evidence"]["mode"] == "strict"
    assert data["fedramp_evidence"]["strict_comparison"]["unauthorized_metric_tampering"] == "denied"


def test_defense_metrics_fedramp_requires_true_flag(asgi_client):
    for flag_value in ("1", "yes"):
        response = asgi_client.get(f"/api/defense/metrics?fedramp={flag_value}")
        assert response.status_code == 200
        data = response.json()
        assert "fedramp_evidence" not in data


def test_defense_metrics_strict_mode_requires_true_flag(asgi_client):
    response = asgi_client.get("/api/defense/metrics?fedramp=true&strict_mode=1")
    assert response.status_code == 200
    data = response.json()
    assert data["fedramp_evidence"]["mode"] == "vulnerable"
    assert data["fedramp_evidence"]["strict_comparison"]["unauthorized_metric_tampering"] == "not-enforced"
