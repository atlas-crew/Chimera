"""
Insurance blueprint.
"""
from app.routing import DecoratorRouter as Router

insurance_router = Router(routes=[])

from . import routes
