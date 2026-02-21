"""
Checkout blueprint.
"""

from flask import Blueprint

checkout_bp = Blueprint('checkout', __name__)

from . import routes
