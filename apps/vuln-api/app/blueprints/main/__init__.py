"""
Main blueprint.
"""
from app.routing import DecoratorRouter as Router

main_router = Router(routes=[])

from . import routes
