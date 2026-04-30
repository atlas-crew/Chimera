"""
Decorator-friendly Router that wraps Starlette's Router.

Starlette uses declarative Route() lists, but our codemod produces
Flask-style @router.route('/path') decorators. This shim bridges the gap
so 486 route registrations don't need manual conversion to declarative style.
"""

import inspect
import json
import re
from functools import wraps

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.routing import BaseRoute, Route, Router as _StarletteRouter


async def safe_json(request):
    """Tolerant JSON body parser matching Flask's `request.get_json() or {}`.

    Starlette's `request.json()` raises `json.JSONDecodeError` on empty or
    malformed bodies, which surfaces as a 500 from the global error handler.
    The original Flask handlers used `request.get_json() or {}` — empty body
    returned None → coerced to {}, malformed raised 400. To preserve the
    vulnerable-by-design code path on empty bodies (the handler still runs
    with an empty dict so the exploit fires), restore those semantics here.
    """
    try:
        data = await request.json()
    except json.JSONDecodeError:
        return {}
    return data if data is not None else {}

_PATH_PARAM_RE = re.compile(r"<(?:(?P<converter>[a-zA-Z_][a-zA-Z0-9_]*):)?(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)>")
_STARLETTE_PATH_PARAM_RE = re.compile(r"{(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)(?::(?P<converter>[a-zA-Z_][a-zA-Z0-9_]*))?}")
_CONVERTER_MAP = {
    "int": "int",
    "float": "float",
    "path": "path",
    "uuid": "uuid",
}


def _is_json_media_type(content_type: str | None) -> bool:
    if not content_type:
        return False

    media_type = content_type.split(";", 1)[0].strip().lower()
    return media_type == "application/json" or (
        media_type.startswith("application/") and media_type.endswith("+json")
    )


def build_http_exception_body(
    *,
    status_code: int,
    detail,
    path: str,
    method: str,
    headers: dict | None = None,
    query_params: dict | None = None,
) -> dict:
    """Build the shared JSON error payload used by ASGI and Flask-compat routes."""
    from app.config import app_config

    body = {
        "error": detail,
        "status": status_code,
        "path": path,
        "method": method,
    }

    if getattr(app_config, "debug", False):
        body["debug"] = {
            "headers": headers or {},
            "query_params": query_params or {},
        }

    return body


class DecoratorRouter(_StarletteRouter):
    """Router subclass that supports @router.route() decorators."""

    @staticmethod
    def _route_sort_key(route: Route) -> tuple:
        """Prefer static segments, then typed params, then untyped params, then path catch-alls."""
        path = getattr(route, "path", "")
        segments = [segment for segment in path.split("/") if segment]

        def _segment_key(segment: str) -> tuple:
            match = _STARLETTE_PATH_PARAM_RE.fullmatch(segment)
            if not match:
                return (0, -len(segment), segment)

            converter = match.group("converter")
            if converter == "path":
                return (3, 0, segment)
            if converter:
                return (1, 0, segment)
            return (2, 0, segment)

        return (tuple(_segment_key(segment) for segment in segments), -len(segments), path)

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

    @staticmethod
    def _denormalize_path(path: str) -> str:
        def _replace(match: re.Match[str]) -> str:
            converter = match.group("converter")
            name = match.group("name")
            if converter:
                return f"<{converter}:{name}>"
            return f"<{name}>"

        return _STARLETTE_PATH_PARAM_RE.sub(_replace, path)

    def route(self, path: str, methods: list[str] | None = None, **kwargs):
        """Register a route handler via decorator, Flask-style."""
        if methods is None:
            methods = ["GET"]

        normalized_path = self._normalize_path(path)

        def decorator(func):
            signature = inspect.signature(func)
            accepts_var_kwargs = any(
                parameter.kind == inspect.Parameter.VAR_KEYWORD
                for parameter in signature.parameters.values()
            )

            @wraps(func)
            async def endpoint(request):
                path_kwargs = request.path_params
                if not accepts_var_kwargs:
                    path_kwargs = {
                        name: value for name, value in request.path_params.items() if name in signature.parameters
                    }

                result = func(request, **path_kwargs)
                if inspect.isawaitable(result):
                    result = await result
                return result

            self.routes.append(Route(normalized_path, endpoint, methods=methods, **kwargs))
            # Preserve Flask/Werkzeug-like specificity so static paths
            # and typed params win over broad catch-all converters.
            self.routes.sort(key=self._route_sort_key)
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


def sort_routes_by_specificity(routes: list[BaseRoute]) -> None:
    """Sort a route list using the shared DecoratorRouter specificity rules."""
    routes.sort(key=DecoratorRouter._route_sort_key)


async def get_json_or_default(request: Request, default=None, *, strict: bool = False):
    """Mirror current Flask 3 request.get_json() semantics for migrated handlers.

    Non-JSON media types raise 415, malformed JSON raises 400, and a JSON null
    body falls back to the provided default to match request.get_json() or {}.
    """
    data = await get_json_value(request)

    if data is None:
        if strict:
            raise HTTPException(status_code=400, detail="JSON body is required")
        return {} if default is None else default
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="JSON body must be an object")
    return data


async def get_json_value(request: Request, default=None):
    """Parse a JSON request body using the same error contract as Flask 3."""
    content_type = str(request.headers.get("content-type", ""))
    if not _is_json_media_type(content_type):
        raise HTTPException(status_code=415, detail="Content-Type must be application/json")

    try:
        data = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Malformed JSON body") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Malformed JSON body") from exc

    if data is None:
        return default
    return data


