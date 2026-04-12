"""
Diagnostics blueprint.
"""
from app.routing import DecoratorRouter as Router

diagnostics_router = Router(routes=[])

from . import routes
