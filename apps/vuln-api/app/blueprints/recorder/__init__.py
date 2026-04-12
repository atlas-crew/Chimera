"""
Recorder blueprint.
"""
from app.routing import DecoratorRouter as Router

recorder_router = Router(routes=[])

from . import routes
