"""
Security Ops blueprint.
"""

from flask import Blueprint

security_ops_bp = Blueprint('security_ops', __name__)

from . import routes
