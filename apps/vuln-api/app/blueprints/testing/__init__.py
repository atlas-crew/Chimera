"""
Testing blueprint for triggering various error conditions.

WARNING: This is a DEMO ENVIRONMENT with INTENTIONAL vulnerabilities.
These endpoints allow triggering errors for WAF testing purposes.
NEVER use this code in production.
"""
from app.routing import DecoratorRouter as Router

testing_router = Router(routes=[])

from . import routes
