"""
Banking blueprint.
"""

from flask import Blueprint

banking_bp = Blueprint('banking', __name__)

from . import routes
