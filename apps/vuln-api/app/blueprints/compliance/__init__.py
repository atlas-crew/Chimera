"""
Compliance blueprint.
"""

from flask import Blueprint

compliance_bp = Blueprint('compliance', __name__)

from . import routes
