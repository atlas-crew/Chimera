"""
Routes for main endpoints.
"""

from flask import request, jsonify, render_template_string, session
from datetime import datetime, timedelta
import uuid
import random
import json
import time

from . import main_bp
from app.models import *
from app.utils import DEMO_PAGE_TEMPLATE

@main_bp.route('/healthz')
@main_bp.route('/api/v1/healthz')
def healthz():
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
    return jsonify({"status": "healthy"}), 200


@main_bp.route('/')
def home():
    """Main demo page showing available endpoints"""
    return render_template_string(DEMO_PAGE_TEMPLATE)


