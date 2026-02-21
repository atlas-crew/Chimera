"""
Testing blueprint for triggering various error conditions.

WARNING: This is a DEMO ENVIRONMENT with INTENTIONAL vulnerabilities.
These endpoints allow triggering errors for WAF testing purposes.
NEVER use this code in production.
"""

from flask import Blueprint

testing_bp = Blueprint('testing', __name__, url_prefix='/api/test')

from . import routes
