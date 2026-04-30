"""
Database vulnerable endpoints router.

SECURITY WARNING: These routes are INTENTIONALLY VULNERABLE to SQL
injection for WAF testing. They bypass ORM safety and execute raw SQL
strings built via f-string interpolation. DO NOT use these patterns in
production code.
"""

from app.routing import DecoratorRouter as Router

db_vuln_router = Router(routes=[])

from . import routes  # noqa: E402,F401  (decorator side-effects)
