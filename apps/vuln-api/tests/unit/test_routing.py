"""Unit tests for the Starlette decorator router shim."""

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from app.routing import DecoratorRouter


def test_decorator_router_preserves_simple_flask_style_paths():
    router = DecoratorRouter(routes=[])

    @router.route("/api/v1/things/<thing_id>")
    async def handler(request, thing_id):  # pragma: no cover - route registration only
        return {"thing_id": thing_id}

    assert router.routes[0].path == "/api/v1/things/{thing_id}"


def test_decorator_router_converts_typed_path_parameters():
    router = DecoratorRouter(routes=[])

    @router.route("/api/test/status/<int:code>")
    async def handler(request, code):  # pragma: no cover - route registration only
        return {"code": code}

    assert router.routes[0].path == "/api/test/status/{code:int}"


def test_decorator_router_forwards_path_params_to_handler():
    router = DecoratorRouter(routes=[])

    @router.route("/api/v1/things/<thing_id>")
    async def handler(request, thing_id):
        return JSONResponse({"thing_id": thing_id})

    app = Starlette(routes=router.routes)

    with TestClient(app) as client:
        response = client.get("/api/v1/things/abc123")

    assert response.status_code == 200
    assert response.json() == {"thing_id": "abc123"}


def test_decorator_router_prioritizes_static_routes_over_dynamic_matches():
    router = DecoratorRouter(routes=[])

    @router.route("/api/v1/licenses/<license_id>")
    async def dynamic_handler(request, license_id):
        return JSONResponse({"license_id": license_id})

    @router.route("/api/v1/licenses/export")
    async def static_handler(request):
        return JSONResponse({"export": True})

    app = Starlette(routes=router.routes)

    with TestClient(app) as client:
        response = client.get("/api/v1/licenses/export")

    assert response.status_code == 200
    assert response.json() == {"export": True}
