"""
Payments blueprint.
"""

from flask import Blueprint

payments_bp = Blueprint('payments', __name__)

from . import routes
