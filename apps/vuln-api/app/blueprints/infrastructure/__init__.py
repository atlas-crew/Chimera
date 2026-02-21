"""
Infrastructure blueprint.
"""

from flask import Blueprint

infrastructure_bp = Blueprint('infrastructure', __name__)

from . import routes
