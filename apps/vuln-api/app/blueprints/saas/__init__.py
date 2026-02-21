"""
SaaS blueprint.
"""

from flask import Blueprint

saas_bp = Blueprint('saas', __name__)

from . import routes
