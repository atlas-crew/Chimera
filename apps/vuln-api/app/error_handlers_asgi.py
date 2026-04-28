"""
Starlette/ASGI counterpart to app.error_handlers.DemoErrorHandler.

Replicates the intentional info-leak surface of the Flask handler — every
piece of data the WAF demo expects to leak (headers, query, cookies, body,
exception details, stack frames, frame locals, route table for 404s) is
preserved here. Behavior parity is the contract; if a leak shifts shape,
the WAF tests fail.

The Starlette runtime makes one piece harder than Flask: by the time an
exception fires, the request body has typically been consumed by the
handler. The companion middleware BodyBufferMiddleware stashes raw bytes
on request.state.raw_body so error handlers can still leak them.
"""

import json
import sys
import traceback
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse


class BodyBufferMiddleware:
    """ASGI middleware that pre-buffers the request body and exposes raw
    bytes on request.state.raw_body for downstream consumers (notably the
    error handlers).

    Pre-buffers (rather than wrapping receive lazily) so that error handlers
    can leak the body even when the route handler raises before consuming
    it — matching Flask/Werkzeug's WSGI semantics where the body is fully
    read before the handler runs. Acceptable cost for a demo workload; not
    suitable for streaming uploads.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        body_chunks: list[bytes] = []
        more_body = True
        while more_body:
            message = await receive()
            mtype = message['type']
            if mtype == 'http.request':
                body_chunks.append(message.get('body', b''))
                more_body = message.get('more_body', False)
            elif mtype == 'http.disconnect':
                break

        scope.setdefault('state', {})
        scope['state']['_body_chunks'] = body_chunks

        # Replay the buffered body to downstream handlers exactly once, then
        # signal disconnect on subsequent receive() calls.
        replayed = False

        async def replay_receive():
            nonlocal replayed
            if not replayed:
                replayed = True
                return {
                    'type': 'http.request',
                    'body': b''.join(body_chunks),
                    'more_body': False,
                }
            return {'type': 'http.disconnect'}

        await self.app(scope, replay_receive, send)


def _raw_body_from_request(request: Request) -> bytes:
    chunks = getattr(request.state, '_body_chunks', None)
    if not chunks:
        return b''
    return b''.join(chunks)


def _build_error_body(
    request: Request,
    error_type: str,
    status_code: int,
    detail: str,
    exc: Exception | None,
    include_trace: bool,
) -> Dict[str, Any]:
    """Build the verbose error body.

    Top-level field shape (`error`, `status`, `path`, `method`) matches the
    Flask compat-shim contract from build_http_exception_body so existing
    clients and tests that depend on those keys keep working. The
    DemoErrorHandler-style verbose info-leak fields are added alongside.
    """
    from app.config import app_config

    raw_body = _raw_body_from_request(request)
    content_type = request.headers.get('content-type', '')
    content_length = request.headers.get('content-length')
    user_agent = request.headers.get('user-agent', 'Unknown')
    request_id = request.headers.get('x-request-id', 'N/A')

    body: Dict[str, Any] = {
        'error': detail,
        'status': status_code,
        'path': request.url.path,
        'method': request.method,
        'error_type': error_type,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'demo_warning': 'THIS IS A DEMO ENVIRONMENT - INTENTIONALLY INSECURE FOR TESTING',
        'remote_addr': request.client.host if request.client else None,
        'user_agent': user_agent,
        'request_id': request_id,
    }

    leaked: Dict[str, Any] = {
        'headers': dict(request.headers),
        'args': dict(request.query_params),
        # Starlette has no synchronous form(); error path can't await safely.
        # Match the Flask shape (None when no form data) but skip parsing.
        'form': None,
        'cookies': dict(request.cookies),
        'content_type': content_type or None,
        'content_length': int(content_length) if content_length and content_length.isdigit() else None,
    }

    if 'application/json' in content_type and raw_body:
        try:
            leaked['json_body'] = json.loads(raw_body)
        except (json.JSONDecodeError, ValueError) as e:
            leaked['json_parse_error'] = str(e)

    if raw_body:
        try:
            leaked['raw_body'] = raw_body.decode('utf-8', errors='replace')
        except Exception as e:
            leaked['raw_body_error'] = str(e)

    body['leaked_data'] = leaked

    body['environment'] = {
        'python_version': sys.version,
        'debug': bool(getattr(app_config, 'debug', False)),
    }

    # Mirror build_http_exception_body's `debug` block so the ASGI exception
    # handler stays parity-compatible with the Flask compat shim's contract.
    if getattr(app_config, 'debug', False):
        body['debug'] = {
            'headers': dict(request.headers),
            'query_params': dict(request.query_params),
        }

    if exc is not None:
        body['exception_details'] = {
            'type': type(exc).__name__,
            'message': str(exc),
            'args': list(exc.args) if exc.args else [],
        }

        if include_trace:
            body['stack_trace'] = traceback.format_exception(
                type(exc), exc, exc.__traceback__
            )
            tb = exc.__traceback__
            frames = []
            while tb is not None:
                frame = tb.tb_frame
                frames.append({
                    'filename': frame.f_code.co_filename,
                    'function': frame.f_code.co_name,
                    'line_number': tb.tb_lineno,
                    'local_vars': {k: repr(v) for k, v in frame.f_locals.items()},
                })
                tb = tb.tb_next
            body['stack_frames'] = frames

    return body


async def handle_400(request: Request, exc: Exception) -> JSONResponse:
    detail = getattr(exc, 'detail', str(exc))
    body = _build_error_body(
        request,
        error_type='BadRequest',
        status_code=400,
        detail=detail,
        exc=exc,
        include_trace=True,
    )
    return JSONResponse(body, status_code=400)


async def handle_401(request: Request, exc: Exception) -> JSONResponse:
    detail = getattr(exc, 'detail', None) or 'Authentication required or invalid credentials'
    body = _build_error_body(
        request,
        error_type='Unauthorized',
        status_code=401,
        detail=detail,
        exc=exc,
        include_trace=True,
    )
    auth_header = request.headers.get('authorization', 'Not provided')
    basic_username = None
    if auth_header.lower().startswith('basic '):
        # Intentionally surface attempted Basic-auth username (decoded, no
        # password) for the demo — same shape as Flask's request.authorization.
        try:
            import base64
            decoded = base64.b64decode(auth_header[6:]).decode('utf-8', errors='replace')
            basic_username = decoded.split(':', 1)[0]
        except Exception:
            basic_username = None
    body['auth_debug'] = {
        'authorization_header': auth_header,
        'basic_auth_username': basic_username,
        'session_data': dict(request.cookies),
    }
    return JSONResponse(body, status_code=401)


async def handle_403(request: Request, exc: Exception) -> JSONResponse:
    detail = getattr(exc, 'detail', None) or 'Access denied - insufficient permissions'
    body = _build_error_body(
        request,
        error_type='Forbidden',
        status_code=403,
        detail=detail,
        exc=exc,
        include_trace=True,
    )
    body['permission_debug'] = {
        'required_permissions': 'Not implemented in demo',
        'user_permissions': 'Not implemented in demo',
        'resource_owner': 'Not implemented in demo',
    }
    return JSONResponse(body, status_code=403)


async def handle_404(request: Request, exc: Exception) -> JSONResponse:
    detail = getattr(exc, 'detail', None) or f'Resource not found: {request.url.path}'
    body = _build_error_body(
        request,
        error_type='NotFound',
        status_code=404,
        detail=detail,
        exc=exc,
        include_trace=True,
    )
    available = []
    try:
        for route in request.app.routes:
            path = getattr(route, 'path', None)
            if path:
                available.append(path)
    except Exception:
        pass
    body['routing_debug'] = {
        'requested_path': request.url.path,
        'available_endpoints': available,
        'blueprint': None,
        'endpoint': None,
    }
    return JSONResponse(body, status_code=404)


async def handle_500(request: Request, exc: Exception) -> JSONResponse:
    detail = getattr(exc, 'detail', None) or 'Internal server error - see debug details below'
    body = _build_error_body(
        request,
        error_type='InternalServerError',
        status_code=500,
        detail=detail,
        exc=exc,
        include_trace=True,
    )
    config_keys = []
    blueprints = []
    try:
        config_keys = sorted(vars(getattr(request.app, 'state', object())).keys())
    except Exception:
        pass
    try:
        # Approximate Flask's app.blueprints listing by deriving prefixes
        # from registered route paths.
        prefixes = set()
        for route in request.app.routes:
            path = getattr(route, 'path', '') or ''
            parts = path.strip('/').split('/')
            if parts and parts[0]:
                prefixes.add(parts[0])
        blueprints = sorted(prefixes)
    except Exception:
        pass
    body['system_debug'] = {
        'config_keys': config_keys,
        'registered_blueprints': blueprints,
        'extensions': [],
    }
    return JSONResponse(body, status_code=500)


async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Dispatch HTTPException by status code to the matching handler."""
    code = getattr(exc, 'status_code', 500)
    if code == 400:
        return await handle_400(request, exc)
    if code == 401:
        return await handle_401(request, exc)
    if code == 403:
        return await handle_403(request, exc)
    if code == 404:
        return await handle_404(request, exc)
    if code == 500:
        return await handle_500(request, exc)

    # Other status codes get the verbose body too, with no per-status extras.
    body = _build_error_body(
        request,
        error_type=type(exc).__name__,
        status_code=code,
        detail=getattr(exc, 'detail', str(exc)),
        exc=exc,
        include_trace=True,
    )
    return JSONResponse(body, status_code=code)


async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for non-HTTPException exceptions — treated as 500."""
    if isinstance(exc, HTTPException):
        return await handle_http_exception(request, exc)
    body = _build_error_body(
        request,
        error_type=type(exc).__name__,
        status_code=500,
        detail=str(exc) or f'Unhandled {type(exc).__name__}',
        exc=exc,
        include_trace=True,
    )
    body['debugging_hint'] = (
        'This is an unhandled exception. In production, this would be logged '
        'and a generic error shown. This demo intentionally exposes all details.'
    )
    return JSONResponse(body, status_code=500)


EXCEPTION_HANDLERS: Dict[Any, Callable[[Request, Exception], Awaitable[JSONResponse]]] = {
    HTTPException: handle_http_exception,
    Exception: handle_generic_exception,
}
