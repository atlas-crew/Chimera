"""
Admin blueprint.
"""
from app.routing import DecoratorRouter as Router

admin_router = Router(routes=[])

from . import routes
