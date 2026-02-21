"""
Ics Ot blueprint.
"""

from flask import Blueprint

ics_ot_bp = Blueprint('ics_ot', __name__)

from . import routes
