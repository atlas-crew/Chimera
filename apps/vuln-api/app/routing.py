"""
Decorator-friendly Router that wraps Starlette's Router.

Starlette uses declarative Route() lists, but our codemod produces
Flask-style @router.route('/path') decorators. This shim bridges the gap
so 486 route registrations don't need manual conversion to declarative style.
"""

import inspect
import re
from functools import wraps

from starlette.requests import Request
from starlette.routing import Route, Router as _StarletteRouter

_PATH_PARAM_RE = re.compile(r"<(?:(?P<converter>[a-zA-Z_][a-zA-Z0-9_]*):)?(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)>")
_CONVERTER_MAP = {
    "int": "int",
    "float": "float",
    "path": "path",
    "uuid": "uuid",
}


class DecoratorRouter(_StarletteRouter):
    """Router subclass that supports @router.route() decorators."""

    @staticmethod
    def _normalize_path(path: str) -> str:
        def _replace(match: re.Match[str]) -> str:
            converter = match.group("converter")
            name = match.group("name")
            starlette_converter = _CONVERTER_MAP.get(converter or "")
            if starlette_converter:
                return f"{{{name}:{starlette_converter}}}"
            return f"{{{name}}}"

        return _PATH_PARAM_RE.sub(_replace, path)

    def route(self, path: str, methods: list[str] | None = None, **kwargs):
        """Register a route handler via decorator, Flask-style."""
        if methods is None:
            methods = ["GET"]

        normalized_path = self._normalize_path(path)

        def decorator(func):
            @wraps(func)
            async def endpoint(request):
                result = func(request, **request.path_params)
                if inspect.isawaitable(result):
                    result = await result
                return result

            self.routes.append(Route(normalized_path, endpoint, methods=methods, **kwargs))
            # Preserve Flask/Werkzeug-like specificity so static paths
            # continue to win over dynamic wildcards after codemod.
            self.routes.sort(key=lambda route: (getattr(route, "path", "").count("{"), -len(getattr(route, "path", ""))))
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


async def get_json_or_default(request: Request, default=None):
    """Mirror Flask's lenient JSON parsing for migrated Starlette handlers."""
    try:
        data = await request.json()
    except Exception:
        return {} if default is None else default

    if data is None:
        return {} if default is None else default
    return data
