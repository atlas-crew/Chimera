"""
Decorator-friendly Router that wraps Starlette's Router.

Starlette uses declarative Route() lists, but our codemod produces
Flask-style @router.route('/path') decorators. This shim bridges the gap
so 486 route registrations don't need manual conversion to declarative style.
"""

from starlette.routing import Router as _StarletteRouter, Route


class DecoratorRouter(_StarletteRouter):
    """Router subclass that supports @router.route() decorators."""

    def route(self, path: str, methods: list[str] | None = None, **kwargs):
        """Register a route handler via decorator, Flask-style."""
        if methods is None:
            methods = ['GET']

        def decorator(func):
            self.routes.append(Route(path, func, methods=methods, **kwargs))
            return func
        return decorator

    def get(self, path: str, **kwargs):
        return self.route(path, methods=['GET'], **kwargs)

    def post(self, path: str, **kwargs):
        return self.route(path, methods=['POST'], **kwargs)

    def put(self, path: str, **kwargs):
        return self.route(path, methods=['PUT'], **kwargs)

    def delete(self, path: str, **kwargs):
        return self.route(path, methods=['DELETE'], **kwargs)

    def patch(self, path: str, **kwargs):
        return self.route(path, methods=['PATCH'], **kwargs)
