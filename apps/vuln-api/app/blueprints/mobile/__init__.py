"""
Mobile blueprint.
"""

from flask import Blueprint

mobile_bp = Blueprint('mobile', __name__)

from . import routes
