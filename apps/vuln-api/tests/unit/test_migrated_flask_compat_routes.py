"""Compatibility tests for migrated Starlette routes exposed via Flask create_app()."""

import io

from flask import Flask
import pytest
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, StreamingResponse
from starlette.testclient import TestClient

from app.asgi import http_exception_handler
from app.routing import DecoratorRouter, register_flask_compat_routes


def assert_matching_error_contract(flask_response, asgi_response):
    flask_data = flask_response.get_json()
    asgi_data = asgi_response.json()

    assert flask_data["error"] == asgi_data["error"]
    assert flask_data["status"] == asgi_data["status"]
    assert flask_data["path"] == asgi_data["path"]
    assert flask_data["method"] == asgi_data["method"]
    if "debug" in flask_data or "debug" in asgi_data:
        assert "debug" in flask_data
        assert "debug" in asgi_data
        assert flask_data["debug"]["query_params"] == asgi_data["debug"]["query_params"]


@pytest.mark.parametrize(
    ("path", "expected_status", "field", "expected_value"),
    [
        ("/api/v1/gov/cases/1", 200, "case_id", "1"),
        ("/api/v1/telecom/subscribers/sub-1/profile", 200, "subscriber", {"subscriber_id": "sub-1"}),
        ("/api/v1/energy-utilities/meters/meter-1/readings", 200, "reading", {"meter_id": "meter-1"}),
        ("/api/security/monitoring/bypass", 200, "monitoring_disabled", True),
        ("/api/loyalty/program/details", 200, "points_expiry_days", 365),
        ("/api/compliance/status", 200, "audit_ready", True),
        ("/api/v1/genai/models/config", 200, "active_model", "gpt-4-turbo"),
        ("/api/recon/advanced", 200, "tech_stack", ["kubernetes", "istio", "postgres", "redis"]),
    ],
)
def test_migrated_routes_remain_reachable_via_flask_compat(client, path, expected_status, field, expected_value):
    response = client.get(path)

    assert response.status_code == expected_status
    data = response.get_json()
    if isinstance(expected_value, dict):
        for key, value in expected_value.items():
            assert data[field][key] == value
    elif isinstance(expected_value, list):
        assert data[field] == expected_value
    else:
        assert data[field] == expected_value


def test_strict_json_routes_match_between_flask_and_asgi(client, asgi_client):
    flask_response = client.post("/api/reporting/sar", data=b"")
    asgi_response = asgi_client.post("/api/reporting/sar", content=b"")

    assert flask_response.status_code == 415
    assert asgi_response.status_code == 415
    assert_matching_error_contract(flask_response, asgi_response)


def test_vendor_json_media_types_work_for_flask_and_asgi(client, asgi_client):
    payload = '{"incident_type":"credential_theft","severity":"high"}'
    headers = {"content-type": "application/vnd.api+json"}

    flask_response = client.post("/api/incidents/create", data=payload, content_type=headers["content-type"])
    asgi_response = asgi_client.post("/api/incidents/create", content=payload, headers=headers)

    assert flask_response.status_code == 201
    assert asgi_response.status_code == 201
    assert flask_response.get_json()["severity"] == "high"
    assert asgi_response.json()["severity"] == "high"


def test_successful_mutation_parity_between_flask_and_asgi(client, asgi_client):
    payload = {
        "source_segment": "Control-LAN",
        "target_segment": "OT-DMZ",
        "bypass_firewall": True,
    }

    flask_response = client.post("/api/ot/network/segment", json=payload)
    asgi_response = asgi_client.post("/api/ot/network/segment", json=payload)

    assert flask_response.status_code == 201
    assert asgi_response.status_code == 201
    assert flask_response.get_json()["source_segment"] == "Control-LAN"
    assert asgi_response.json()["source_segment"] == "Control-LAN"
    assert flask_response.get_json()["lateral_movement_enabled"] is True
    assert asgi_response.json()["lateral_movement_enabled"] is True


def test_infrastructure_get_parity_between_flask_and_asgi(client, asgi_client):
    flask_response = client.get("/api/gateway/routes")
    asgi_response = asgi_client.get("/api/gateway/routes")

    assert flask_response.status_code == 200
    assert asgi_response.status_code == 200
    assert flask_response.get_json()["total_routes"] == 47
    assert asgi_response.json()["total_routes"] == 47
    assert flask_response.get_json()["gateway_version"] == "2.1.0"
    assert asgi_response.json()["gateway_version"] == "2.1.0"


def test_infrastructure_mutation_parity_between_flask_and_asgi(client, asgi_client):
    payload = {"key": "gw-shell"}

    flask_response = client.post("/api/gateway/backdoor", json=payload)
    asgi_response = asgi_client.post("/api/gateway/backdoor", json=payload)

    assert flask_response.status_code == 201
    assert asgi_response.status_code == 201
    assert flask_response.get_json()["backdoor_key"] == "gw-shell"
    assert asgi_response.json()["backdoor_key"] == "gw-shell"
    assert flask_response.get_json()["persistence_scope"] == "gateway"
    assert asgi_response.json()["persistence_scope"] == "gateway"


def test_genai_upload_text_parity_between_flask_and_asgi(client, asgi_client):
    payload = {"content": "knowledge base seed"}

    flask_response = client.post("/api/v1/genai/knowledge/upload", json=payload)
    asgi_response = asgi_client.post("/api/v1/genai/knowledge/upload", json=payload)

    assert flask_response.status_code == 200
    assert asgi_response.status_code == 200
    assert flask_response.get_json()["status"] == "success"
    assert asgi_response.json()["status"] == "success"
    assert flask_response.get_json()["message"] == "Text content indexed"
    assert asgi_response.json()["message"] == "Text content indexed"


def test_genai_upload_file_parity_between_flask_and_asgi(client, asgi_client):
    flask_response = client.post(
        "/api/v1/genai/knowledge/upload",
        data={"file": (io.BytesIO(b"#!/bin/sh"), "../../../../tmp/payload.sh")},
        content_type="multipart/form-data",
    )
    asgi_response = asgi_client.post(
        "/api/v1/genai/knowledge/upload",
        files={"file": ("../../../../tmp/payload.sh", b"#!/bin/sh", "text/plain")},
    )

    assert flask_response.status_code == 200
    assert asgi_response.status_code == 200
    assert flask_response.get_json()["vulnerability"] == "PATH_TRAVERSAL_DETECTED"
    assert asgi_response.json()["vulnerability"] == "PATH_TRAVERSAL_DETECTED"
    assert flask_response.get_json()["path"].endswith("../../../../tmp/payload.sh")
    assert asgi_response.json()["path"].endswith("../../../../tmp/payload.sh")


def test_genai_graphql_batch_parity_between_flask_and_asgi(client, asgi_client):
    payload = [{"query": "{ systemInfo { version } }"}, {"query": "{ systemInfo { version } }"}]

    flask_response = client.post("/api/v1/genai/graphql", json=payload)
    asgi_response = asgi_client.post("/api/v1/genai/graphql", json=payload)

    assert flask_response.status_code == 200
    assert asgi_response.status_code == 200
    assert len(flask_response.get_json()) == 2
    assert len(asgi_response.json()) == 2
    assert flask_response.get_json()[0]["data"]["systemInfo"]["version"] == "2.1.0"
    assert asgi_response.json()[0]["data"]["systemInfo"]["version"] == "2.1.0"


def test_attack_sim_coordination_parity_between_flask_and_asgi(client, asgi_client):
    payload = {"stage": "persistence", "agents": ["ghost", "ember"]}

    flask_response = client.post("/api/coordination", json=payload)
    asgi_response = asgi_client.post("/api/coordination", json=payload)

    assert flask_response.status_code == 200
    assert asgi_response.status_code == 200
    assert flask_response.get_json()["stage"] == "persistence"
    assert asgi_response.json()["stage"] == "persistence"
    assert flask_response.get_json()["agents"] == ["ghost", "ember"]
    assert asgi_response.json()["agents"] == ["ghost", "ember"]
    assert flask_response.get_json()["distributed_execution"] is True
    assert asgi_response.json()["distributed_execution"] is True


def test_attack_sim_command_execution_parity_between_flask_and_asgi(client, asgi_client):
    payload = {"command": "whoami", "targets": ["dc-01"], "mode": "sequential"}

    flask_response = client.post("/api/commands/execute", json=payload)
    asgi_response = asgi_client.post("/api/commands/execute", json=payload)

    assert flask_response.status_code == 200
    assert asgi_response.status_code == 200
    assert flask_response.get_json()["command"] == "whoami"
    assert asgi_response.json()["command"] == "whoami"
    assert flask_response.get_json()["mode"] == "sequential"
    assert asgi_response.json()["mode"] == "sequential"
    assert flask_response.get_json()["command_acknowledged"] is True
    assert asgi_response.json()["command_acknowledged"] is True


def test_malformed_json_rejected_by_flask_and_asgi(client, asgi_client):
    payload = "{"

    flask_response = client.post("/api/incidents/create", data=payload, content_type="application/json")
    asgi_response = asgi_client.post("/api/incidents/create", content=payload, headers={"content-type": "application/json"})

    assert flask_response.status_code == 400
    assert asgi_response.status_code == 400
    assert_matching_error_contract(flask_response, asgi_response)


def test_non_object_json_rejected_by_flask_and_asgi(client, asgi_client):
    payload = "[]"

    flask_response = client.post("/api/incidents/create", data=payload, content_type="application/json")
    asgi_response = asgi_client.post("/api/incidents/create", content=payload, headers={"content-type": "application/json"})

    assert flask_response.status_code == 400
    assert asgi_response.status_code == 400
    assert_matching_error_contract(flask_response, asgi_response)


def test_structured_http_exception_detail_parity():
    router = DecoratorRouter(routes=[])

    @router.route("/api/test/structured-error", methods=["POST"])
    async def structured_error(request):
        raise HTTPException(status_code=409, detail={"code": "conflict", "fields": ["x"]})

    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    register_flask_compat_routes(flask_app, router, endpoint_prefix="structured")

    asgi_app = Starlette(
        routes=router.routes,
        exception_handlers={HTTPException: http_exception_handler, Exception: http_exception_handler},
    )

    with flask_app.test_client() as flask_client, TestClient(asgi_app) as asgi_client:
        flask_response = flask_client.post("/api/test/structured-error")
        asgi_response = asgi_client.post("/api/test/structured-error")

    assert flask_response.status_code == 409
    assert asgi_response.status_code == 409
    assert_matching_error_contract(flask_response, asgi_response)
    assert flask_response.get_json()["error"] == {"code": "conflict", "fields": ["x"]}


def test_streaming_response_compatibility():
    router = DecoratorRouter(routes=[])

    @router.route("/api/test/stream", methods=["GET"])
    async def stream_handler(request):
        async def chunks():
            yield b"hello "
            yield b"world"

        return StreamingResponse(chunks(), media_type="text/plain")

    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    register_flask_compat_routes(flask_app, router, endpoint_prefix="stream")

    asgi_app = Starlette(routes=router.routes)

    with flask_app.test_client() as flask_client, TestClient(asgi_app) as asgi_client:
        flask_response = flask_client.get("/api/test/stream")
        asgi_response = asgi_client.get("/api/test/stream")

    assert flask_response.status_code == 200
    assert asgi_response.status_code == 200
    assert flask_response.data == b"hello world"
    assert asgi_response.text == "hello world"


def test_flask_compat_adapter_exposes_basic_url_fields():
    router = DecoratorRouter(routes=[])

    @router.route("/api/test/url-meta", methods=["GET"])
    async def url_meta(request):
        return JSONResponse(
            {
                "path": request.url.path,
                "query": request.url.query,
                "scheme": request.url.scheme,
                "full": str(request.url),
                "secure": request.url.is_secure,
            }
        )

    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    register_flask_compat_routes(flask_app, router, endpoint_prefix="url_meta")

    asgi_app = Starlette(routes=router.routes)

    with flask_app.test_client() as flask_client, TestClient(asgi_app) as asgi_client:
        flask_response = flask_client.get("/api/test/url-meta?mode=compat")
        asgi_response = asgi_client.get("/api/test/url-meta?mode=compat")

    assert flask_response.status_code == 200
    assert asgi_response.status_code == 200
    assert flask_response.get_json()["path"] == "/api/test/url-meta"
    assert asgi_response.json()["path"] == "/api/test/url-meta"
    assert flask_response.get_json()["query"] == "mode=compat"
    assert asgi_response.json()["query"] == "mode=compat"
    assert flask_response.get_json()["scheme"] == "http"
    assert asgi_response.json()["scheme"] == "http"
    assert flask_response.get_json()["full"].endswith("/api/test/url-meta?mode=compat")
    assert asgi_response.json()["full"].endswith("/api/test/url-meta?mode=compat")
    assert flask_response.get_json()["secure"] is False
    assert asgi_response.json()["secure"] is False
