"""
Energy utilities blueprint.
"""

from flask import Blueprint

energy_utilities_bp = Blueprint('energy_utilities', __name__)

from . import routes
