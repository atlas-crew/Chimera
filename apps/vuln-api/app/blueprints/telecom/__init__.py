"""
Telecom blueprint.
"""
from app.routing import DecoratorRouter as Router

telecom_router = Router(routes=[])

from . import routes
