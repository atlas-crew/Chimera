"""
Diagnostics blueprint.
"""

from flask import Blueprint

diagnostics_bp = Blueprint('diagnostics', __name__)

from . import routes
