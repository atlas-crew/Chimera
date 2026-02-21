"""
Ecommerce blueprint.
"""

from flask import Blueprint

ecommerce_bp = Blueprint('ecommerce', __name__)

from . import routes
