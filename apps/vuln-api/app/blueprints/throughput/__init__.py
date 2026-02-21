"""
Throughput blueprint.
"""

from flask import Blueprint

throughput_bp = Blueprint('throughput', __name__)

from . import routes
