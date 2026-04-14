"""Unit tests for migrated attack_sim Starlette routes."""


def test_attack_sim_recon_advanced(asgi_client):
    response = asgi_client.get("/api/recon/advanced")

    assert response.status_code == 200
    data = response.json()
    assert "vpn-gateway" in data["external_services"]
    assert "postgres" in data["tech_stack"]


def test_attack_sim_intelligence_gather(asgi_client):
    response = asgi_client.post("/api/intelligence/gather", json={"target": "board"})

    assert response.status_code == 200
    data = response.json()
    assert data["target"] == "board"
    assert data["cred_leak_detected"] is True


def test_attack_sim_coordination_returns_operation_contract(asgi_client):
    response = asgi_client.post(
        "/api/coordination",
        json={"stage": "lateral-movement", "agents": ["atlas", "ghost"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "lateral-movement"
    assert data["agents"] == ["atlas", "ghost"]
    assert data["distributed_execution"] is True


def test_attack_sim_exfiltration_channels(asgi_client):
    response = asgi_client.get("/api/exfiltration/channels")

    assert response.status_code == 200
    data = response.json()
    assert data["recommended"] == "dns-tunnel"
    assert len(data["available_channels"]) == 5


def test_attack_sim_command_execution(asgi_client):
    response = asgi_client.post(
        "/api/commands/execute",
        json={"command": "ls -la", "targets": ["workstation-01"], "mode": "parallel"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["command"] == "ls -la"
    assert data["targets"] == ["workstation-01"]
    assert data["command_acknowledged"] is True


def test_attack_sim_mission_objectives(asgi_client):
    response = asgi_client.get("/api/mission/objectives")

    assert response.status_code == 200
    data = response.json()
    assert data["campaign_name"] == "OPERATION_PERSISTENT_ACCESS"
    assert len(data["primary_objectives"]) == 4
    assert data["success_metrics"]["systems_compromised"] == 50
