"""
Throughput blueprint.
"""
from app.routing import DecoratorRouter as Router

throughput_router = Router(routes=[])

from . import routes
