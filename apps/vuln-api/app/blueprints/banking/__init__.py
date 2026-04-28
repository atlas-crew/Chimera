"""
Banking blueprint.
"""
from app.routing import DecoratorRouter as Router

banking_router = Router(routes=[])

from . import routes
