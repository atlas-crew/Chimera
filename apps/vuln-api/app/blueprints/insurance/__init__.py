"""
Insurance blueprint.
"""

from flask import Blueprint

insurance_bp = Blueprint('insurance', __name__)

from . import routes
