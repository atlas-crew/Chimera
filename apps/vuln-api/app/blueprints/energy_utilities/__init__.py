"""
Energy utilities blueprint.
"""
from app.routing import DecoratorRouter as Router

energy_utilities_router = Router(routes=[])

from . import routes
