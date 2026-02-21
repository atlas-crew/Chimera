"""
GenAI blueprint.
"""

from flask import Blueprint

genai_bp = Blueprint('genai', __name__)

from . import routes
