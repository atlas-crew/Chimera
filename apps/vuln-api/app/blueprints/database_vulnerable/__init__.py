"""
Database vulnerable endpoints blueprint.

SECURITY WARNING: This blueprint contains INTENTIONALLY VULNERABLE endpoints
for WAF SQL injection testing. These endpoints bypass ORM safety and use
raw SQL queries with string interpolation.

DO NOT use these patterns in production code.
"""

from flask import Blueprint

db_vuln_bp = Blueprint('database_vulnerable', __name__)

from . import routes
