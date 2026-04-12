"""
Routes for main endpoints.
"""
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from datetime import datetime, timedelta
import uuid
import random
import json
import time

from . import main_router
from app.models import *
from app.utils import DEMO_PAGE_TEMPLATE

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
    """Main demo page showing available endpoints"""
    return HTMLResponse(DEMO_PAGE_TEMPLATE)


