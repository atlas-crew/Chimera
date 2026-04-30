"""
Routes for main endpoints.
"""
import os

from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse, FileResponse

from . import main_router
from app.utils import DEMO_PAGE_TEMPLATE


_WEB_DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "web_dist")
_SPA_INDEX = os.path.join(_WEB_DIST_DIR, "index.html")

@main_router.route('/healthz')
@main_router.route('/api/v1/healthz')
async def healthz(request: Request):
    """
    Health check endpoint for Docker healthcheck and frontend connectivity
    ---
    tags:
      - System
    responses:
      200:
        description: System is healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: "healthy"
    """
    return JSONResponse({"status": "healthy"}, status_code = 200)


@main_router.route('/')
async def home(request: Request):
    """Serve the SPA when web_dist/index.html exists, else the demo template."""
    if os.path.isfile(_SPA_INDEX):
        return FileResponse(_SPA_INDEX, media_type="text/html")
    return HTMLResponse(DEMO_PAGE_TEMPLATE)


