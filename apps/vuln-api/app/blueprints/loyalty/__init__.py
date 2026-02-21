"""
Loyalty blueprint.
"""

from flask import Blueprint

loyalty_bp = Blueprint('loyalty', __name__)

from . import routes
