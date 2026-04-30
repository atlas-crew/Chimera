"""
Application factory for the Chimera WAF Demo API.

After task-16.8 the app is Starlette-only. ``create_app`` and the
module-level ``app`` are re-exported from ``app.asgi`` so that any caller
that still imports ``from app import create_app`` (entry-point scripts,
older tests, drift checker) keeps resolving to the ASGI factory.
"""

from app.asgi import app, create_app

__all__ = ["app", "create_app"]
