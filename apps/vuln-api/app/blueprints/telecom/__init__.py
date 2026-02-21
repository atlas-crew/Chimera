"""
Telecom blueprint.
"""

from flask import Blueprint

telecom_bp = Blueprint('telecom', __name__)

from . import routes
