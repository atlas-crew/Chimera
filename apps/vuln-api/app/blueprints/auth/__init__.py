"""
Auth blueprint.
"""
from app.routing import DecoratorRouter as Router

auth_router = Router(routes=[])

from . import routes
