"""
Attack Sim blueprint.
"""

from flask import Blueprint

attack_sim_bp = Blueprint('attack_sim', __name__)

from . import routes
