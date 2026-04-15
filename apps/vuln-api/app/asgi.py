"""
Starlette application factory for the Chimera WAF Demo API.

This is the ASGI counterpart to the Flask factory in app/__init__.py.
During migration, both coexist — Flask continues serving all routes while
this skeleton proves out the Starlette infrastructure (middleware, error
handling, static serving).  Routes are mounted here as they are ported.
"""

import os

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse, FileResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from app.config import init_config, app_config
from app.routing import build_http_exception_body, sort_routes_by_specificity


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class CSPMiddleware:
    """Inject Content-Security-Policy header based on request path."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        path = scope.get('path', '')

        if path in {'/swagger', '/openapi.yaml'}:
            csp = (
                "default-src 'self' https://unpkg.com; "
                "style-src 'self' https://unpkg.com 'unsafe-inline'; "
                "script-src 'self' https://unpkg.com 'unsafe-inline'; "
                "img-src 'self' data: https://unpkg.com; "
                "font-src 'self' https://unpkg.com; "
                "connect-src 'self'"
            )
        elif not path.startswith(('/api/', '/apidocs')):
            csp = (
                "default-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "script-src 'self'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'"
            )
        else:
            csp = (
                "default-src 'self'; "
                "style-src 'self'; "
                "script-src 'self'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'"
            )

        async def send_with_csp(message):
            if message['type'] == 'http.response.start':
                headers = list(message.get('headers', []))
                headers.append((b'content-security-policy', csp.encode()))
                message = {**message, 'headers': headers}
            await send(message)

        await self.app(scope, receive, send_with_csp)


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

async def http_exception_handler(request: Request, exc: Exception):
    """Catch-all error handler that mirrors Flask DemoErrorHandler behavior."""
    from starlette.exceptions import HTTPException

    status_code = getattr(exc, 'status_code', 500)
    detail = getattr(exc, 'detail', str(exc))

    body = build_http_exception_body(
        status_code=status_code,
        detail=detail,
        path=str(request.url.path),
        method=request.method,
        headers=dict(request.headers),
        query_params=dict(request.query_params),
    )
    return JSONResponse(body, status_code=status_code)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

async def healthz(request: Request):
    return JSONResponse({'status': 'healthy'})


async def openapi_spec(request: Request):
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs'))
    spec_path = os.path.join(docs_dir, 'openapi.yaml')
    if os.path.isfile(spec_path):
        return FileResponse(spec_path, media_type='application/x-yaml')
    return JSONResponse({'error': 'openapi.yaml not found'}, status_code=404)


SWAGGER_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Chimera TestBed Swagger UI</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    <style>
      body { margin: 0; background: #0f172a; }
      #swagger-ui { padding: 12px 24px; }
    </style>
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.onload = function () {
        SwaggerUIBundle({
          url: '/openapi.yaml',
          dom_id: '#swagger-ui',
          deepLinking: true,
          presets: [SwaggerUIBundle.presets.apis],
          layout: 'BaseLayout'
        });
      };
    </script>
  </body>
</html>"""


async def swagger_ui(request: Request):
    return HTMLResponse(SWAGGER_HTML)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app(config: dict | None = None) -> Starlette:
    """
    Create and configure the Starlette application.

    Mirrors the structure of the Flask create_app() in app/__init__.py.
    """
    cfg = init_config(config)

    # Ported blueprint routers (Tier 1 + Tier 2 waves)
    from app.blueprints.main import main_router
    from app.blueprints.recorder import recorder_router
    from app.blueprints.diagnostics import diagnostics_router
    from app.blueprints.throughput import throughput_router
    from app.blueprints.admin import admin_router
    from app.blueprints.attack_sim import attack_sim_router
    from app.blueprints.government import government_router
    from app.blueprints.telecom import telecom_router
    from app.blueprints.energy_utilities import energy_utilities_router
    from app.blueprints.security_ops import security_ops_router
    from app.blueprints.loyalty import loyalty_router
    from app.blueprints.compliance import compliance_router
    from app.blueprints.ics_ot import ics_ot_router
    from app.blueprints.infrastructure import infrastructure_router
    from app.blueprints.genai import genai_router

    # Core infrastructure routes + routes from ported blueprints
    routes = [
        Route('/openapi.yaml', openapi_spec),
        Route('/swagger', swagger_ui),
        *main_router.routes,
        *recorder_router.routes,
        *diagnostics_router.routes,
        *throughput_router.routes,
        *admin_router.routes,
        *attack_sim_router.routes,
        *government_router.routes,
        *telecom_router.routes,
        *energy_utilities_router.routes,
        *security_ops_router.routes,
        *loyalty_router.routes,
        *compliance_router.routes,
        *ics_ot_router.routes,
        *infrastructure_router.routes,
        *genai_router.routes,
    ]

    # SPA static files
    web_dist_dir = os.path.join(os.path.dirname(__file__), 'web_dist')
    if os.path.isdir(web_dist_dir):
        routes.append(Mount('/assets', app=StaticFiles(directory=web_dist_dir), name='static'))
    # Keep precedence stable in both API-only and built-frontend environments.
    sort_routes_by_specificity(routes)

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_methods=['*'],
            allow_headers=['*'],
        ),
        Middleware(
            SessionMiddleware,
            secret_key=cfg.secret_key,
        ),
        Middleware(CSPMiddleware),
    ]

    from starlette.exceptions import HTTPException
    exception_handlers = {
        HTTPException: http_exception_handler,
        Exception: http_exception_handler,
    }

    app = Starlette(
        debug=cfg.debug,
        routes=routes,
        middleware=middleware,
        exception_handlers=exception_handlers,
    )

    # Initialize demo data (same as Flask factory)
    from app.utils import init_demo_data
    init_demo_data()

    return app


# Module-level app instance for `uvicorn app.asgi:app`
app = create_app()
