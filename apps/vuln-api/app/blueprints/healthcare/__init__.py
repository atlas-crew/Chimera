"""
Healthcare blueprint.
"""

from flask import Blueprint

healthcare_bp = Blueprint('healthcare', __name__)

from . import routes
