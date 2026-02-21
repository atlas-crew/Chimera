"""
Recorder blueprint.
"""

from flask import Blueprint

recorder_bp = Blueprint('recorder', __name__)

from . import routes
