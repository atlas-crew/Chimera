"""
Attack Sim blueprint.
"""
from app.routing import DecoratorRouter as Router

attack_sim_router = Router(routes=[])

from . import routes
