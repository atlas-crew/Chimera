from flask import Blueprint

education_bp = Blueprint('education', __name__)

from . import routes
