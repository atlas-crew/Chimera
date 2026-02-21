"""
Integrations blueprint.
"""

from flask import Blueprint

integrations_bp = Blueprint('integrations', __name__)

from . import routes
