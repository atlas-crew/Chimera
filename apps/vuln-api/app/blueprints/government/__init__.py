"""
Government blueprint.
"""
from app.routing import DecoratorRouter as Router

government_router = Router(routes=[])

from . import routes
