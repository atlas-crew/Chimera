"""Focused tests for the hotpatch decorator during the Flask -> Starlette cutover."""

import asyncio
import json

import pytest
from flask import Flask, jsonify

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.models import accounts_db
from app.utils.hotpatch import hotpatch
from app.utils.security_config import security_config


def _starlette_request(path: str, education: bool = False) -> Request:
    headers = []
    if education:
        headers.append((b"x-chimera-education", b"true"))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
    }
    return Request(scope)


@pytest.fixture(autouse=True)
def restore_security_config():
    original = security_config.to_dict().copy()
    yield
    security_config.update(original)


def test_hotpatch_headers_still_work_for_flask_routes(client):
    security_config.update({"bola_protection": False})
    accounts_db["ACC-HOTPATCH-001"] = {
        "account_id": "ACC-HOTPATCH-001",
        "user_id": "victim-user",
        "account_type": "checking",
        "balance": 42.0,
        "currency": "USD",
        "status": "active",
        "created_at": "2026-04-14T00:00:00",
    }

    response = client.get("/api/v1/banking/accounts/ACC-HOTPATCH-001")

    assert response.status_code == 200
    assert response.headers["X-Chimera-Patched"] == "false"
    assert response.headers["X-Chimera-Vuln-ID"] == "CHM-BANK-002"
    assert response.headers["X-Chimera-Vuln-Type"] == "BOLA / IDOR (Accounts)"
    assert response.headers["X-Chimera-OWASP"] == "A01:2021-Broken Access Control"
    assert response.headers["X-Chimera-CWE"] == "CWE-639"
    assert response.headers["X-Chimera-Severity"] == "high"
    assert response.headers["X-Chimera-Hint"] == (
        "Listing accounts without proper session validation allows viewing any user's balance by iterating account IDs"
    )


def test_hotpatch_education_metadata_still_works_for_flask_routes(client):
    security_config.update({"bola_protection": False})
    accounts_db["ACC-HOTPATCH-002"] = {
        "account_id": "ACC-HOTPATCH-002",
        "user_id": "victim-user",
        "account_type": "checking",
        "balance": 42.0,
        "currency": "USD",
        "status": "active",
        "created_at": "2026-04-14T00:00:00",
    }

    response = client.get(
        "/api/v1/banking/accounts/ACC-HOTPATCH-002",
        headers={"X-Chimera-Education": "true"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["_chimera"]["vuln_id"] == "CHM-BANK-002"
    assert data["_chimera"]["patched"] is False


def test_hotpatch_supports_async_starlette_handlers():
    security_config.update({"bola_protection": True})

    @hotpatch("bola")
    async def handler(request: Request, is_secure: bool = False):
        assert is_secure is True
        return JSONResponse({"ok": True})

    response = asyncio.run(handler(_starlette_request("/api/v1/banking/accounts", education=True)))
    body = json.loads(response.body)

    assert response.status_code == 200
    assert response.headers["X-Chimera-Patched"] == "true"
    assert response.headers["X-Chimera-Vuln-ID"] == "CHM-BANK-002"
    assert body["ok"] is True
    assert body["_chimera"]["patched"] is True
    assert "X-Chimera-Hint" not in response.headers


def test_hotpatch_finds_starlette_request_in_kwargs():
    security_config.update({"bola_protection": False})

    @hotpatch("bola")
    async def handler(account_id: str, request: Request, is_secure: bool = False):
        assert account_id == "ACC-KWARGS"
        assert is_secure is False
        return JSONResponse({"account_id": account_id})

    response = asyncio.run(
        handler("ACC-KWARGS", request=_starlette_request("/api/v1/banking/accounts", education=True))
    )
    body = json.loads(response.body)

    assert response.headers["X-Chimera-Vuln-ID"] == "CHM-BANK-002"
    assert body["_chimera"]["vuln_id"] == "CHM-BANK-002"


def test_hotpatch_leaves_non_json_starlette_responses_untouched():
    security_config.update({"bola_protection": False})

    @hotpatch("bola")
    async def handler(request: Request, is_secure: bool = False):
        return JSONResponse("not-a-dict")

    response = asyncio.run(handler(_starlette_request("/api/v1/banking/accounts", education=True)))
    body = json.loads(response.body)

    assert response.status_code == 200
    assert response.headers["X-Chimera-Vuln-ID"] == "CHM-BANK-002"
    assert body == "not-a-dict"


def test_hotpatch_async_flask_views_still_get_decorated():
    security_config.update({"bola_protection": False})
    app = Flask(__name__)
    app.secret_key = "test-secret"

    @hotpatch("bola")
    async def handler(is_secure: bool = False):
        assert is_secure is False
        return jsonify({"ok": True})

    with app.test_request_context("/api/v1/banking/accounts", headers={"X-Chimera-Education": "true"}):
        response = asyncio.run(handler())

    assert response.headers["X-Chimera-Vuln-ID"] == "CHM-BANK-002"
    assert response.get_json()["_chimera"]["vuln_id"] == "CHM-BANK-002"


# Removed: test_hotpatch_flask_routes_still_work_when_starlette_symbols_missing
# Banking is now an async Starlette route (task-16.3); its handler constructs a
# JSONResponse directly, so the "Starlette uninstalled" defensive scenario the
# test simulated no longer reflects any production code path. The other
# hotpatch tests still cover sync vs async dispatch and the Flask compat-shim
# header injection.
