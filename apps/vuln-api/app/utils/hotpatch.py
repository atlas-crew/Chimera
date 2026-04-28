from __future__ import annotations

import inspect
import json as _json
import logging
from functools import wraps
from typing import Any

try:
    from starlette.requests import Request as StarletteRequest
    from starlette.responses import JSONResponse, Response as StarletteResponse
except (
    ImportError
):  # pragma: no cover - Flask-first environments may not have Starlette yet.
    StarletteRequest = None
    JSONResponse = None
    StarletteResponse = None

from app.utils.security_config import security_config
from app.utils.vuln_registry import VULN_REGISTRY

try:
    from flask import Response as FlaskResponse
    from flask import make_response, request as flask_request
except ImportError:  # pragma: no cover - Flask remains installed during cutover.
    FlaskResponse = None
    make_response = None
    flask_request = None

logger = logging.getLogger(__name__)


def _lookup_vulnerability_meta(
    request_path: str, config_attr: str, vuln_id: str | None
):
    vid = vuln_id
    meta = VULN_REGISTRY.get(vid) if vid else None

    if not meta:
        for entry_id, entry_meta in VULN_REGISTRY.items():
            endpoint_path = (
                entry_meta["endpoint"]
                .split(" ")[-1]
                .split("?")[0]
                .split("{")[0]
                .rstrip("/")
            )
            if entry_meta["portal"] in request_path and endpoint_path in request_path:
                vid = entry_id
                meta = entry_meta
                break

    if not meta:
        for entry_id, entry_meta in VULN_REGISTRY.items():
            if (
                entry_meta["config_key"] == config_attr
                and f'/{entry_meta["portal"]}/' in request_path
            ):
                vid = entry_id
                meta = entry_meta
                break

    return vid, meta


def _add_headers(
    response: Any, is_secure: bool, vid: str | None, meta: dict[str, Any] | None
) -> None:
    response.headers["X-Chimera-Patched"] = str(is_secure).lower()

    if not meta:
        return

    if vid is None:
        logger.warning(
            "Vulnerability metadata resolved without an id for endpoint %s",
            meta.get("endpoint"),
        )
        return

    response.headers["X-Chimera-Vuln-ID"] = vid
    response.headers["X-Chimera-Vuln-Type"] = meta["name"]
    response.headers["X-Chimera-OWASP"] = meta["owasp"]
    response.headers["X-Chimera-CWE"] = meta["cwe"]
    response.headers["X-Chimera-Severity"] = meta["severity"]

    if not is_secure:
        response.headers["X-Chimera-Hint"] = meta["description"].split(".")[0]


def _chimera_metadata(
    vid: str, meta: dict[str, Any], is_secure: bool
) -> dict[str, Any]:
    return {
        "vuln_id": vid,
        "vuln_type": meta["name"],
        "owasp": meta["owasp"],
        "cwe": meta["cwe"],
        "severity": meta["severity"],
        "description": meta["description"],
        "patched": is_secure,
        "endpoint": meta["endpoint"],
    }


def _wants_education_headers(headers: Any) -> bool:
    header_value = headers.get("X-Chimera-Education")
    return isinstance(header_value, str) and header_value.lower() == "true"


def _parse_response_json(response: Any) -> dict[str, Any] | None:
    if FlaskResponse is not None and isinstance(response, FlaskResponse):
        return response.get_json(silent=True)

    if StarletteResponse is None or not isinstance(response, StarletteResponse):
        return None

    content_type = response.headers.get("content-type", "")
    if "json" not in content_type:
        return None

    body = response.body
    if isinstance(body, memoryview):
        body = body.tobytes()

    if not body:
        return None

    return _json.loads(body)


def _inject_education_metadata(
    response: Any,
    vid: str,
    meta: dict[str, Any],
    is_secure: bool,
) -> Any:
    try:
        data = _parse_response_json(response)
        if not isinstance(data, dict):
            return response

        data["_chimera"] = _chimera_metadata(vid, meta, is_secure)

        if FlaskResponse is not None and isinstance(response, FlaskResponse):
            response.set_data(_json.dumps(data))
            response.headers["Content-Length"] = str(len(response.get_data()))
            return response

        if JSONResponse is None:
            return response

        if StarletteResponse is not None and isinstance(response, StarletteResponse):
            existing_headers = {
                key: value
                for key, value in response.headers.items()
                if key.lower() != "content-length"
            }
            response.body = response.render(data)
            response.init_headers(existing_headers)
            return response

        headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() != "content-length"
        }
        return JSONResponse(data, status_code=response.status_code, headers=headers)
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        logger.warning("Error injecting Chimera education metadata: %s", exc)
        return response


def _ensure_starlette_response(result: Any) -> StarletteResponse:
    if JSONResponse is None or StarletteResponse is None:
        raise RuntimeError("Starlette response helpers are unavailable")

    if isinstance(result, StarletteResponse):
        return result

    if isinstance(result, tuple):
        payload = result[0]
        status_code = result[1] if len(result) > 1 else 200
        headers = result[2] if len(result) > 2 else None
    else:
        payload = result
        status_code = 200
        headers = None

    if isinstance(payload, (dict, list)):
        return JSONResponse(payload, status_code=status_code, headers=headers)

    return StarletteResponse(payload, status_code=status_code, headers=headers)


def _finalize_response(
    response: Any,
    request_path: str,
    headers: Any,
    config_attr: str,
    vuln_id: str | None,
    is_secure: bool,
):
    vid, meta = _lookup_vulnerability_meta(request_path, config_attr, vuln_id)
    _add_headers(response, is_secure, vid, meta)

    if meta and vid and _wants_education_headers(headers):
        return _inject_education_metadata(response, vid, meta, is_secure)

    return response


def _get_starlette_request(
    args: tuple[Any, ...], kwargs: dict[str, Any]
) -> StarletteRequest | None:
    candidates = list(args) + list(kwargs.values())

    if StarletteRequest is not None:
        for value in candidates:
            if isinstance(value, StarletteRequest):
                return value

    # Accept duck-typed adapters (e.g. routing.FlaskRequestAdapter used by
    # the Flask compat shim) that expose the .url.path / .headers surface
    # _finalize_response actually consumes. Without this, async hotpatch
    # routes invoked from the WSGI side fall through to make_response()
    # against a Starlette JSONResponse, which Flask can't unwrap.
    for value in candidates:
        url = getattr(value, "url", None)
        if url is not None and hasattr(url, "path") and hasattr(value, "headers"):
            return value

    return None


def hotpatch(vuln_type, vuln_id=None):
    """
    Decorator to enable 'hot-patching' of routes.
    Switches between a vulnerable implementation and a secure implementation
    based on the global security_config state.

    Also injects X-Chimera-* educational headers into the response.
    """

    def decorator(f):
        config_attr = f"{vuln_type}_protection"

        if inspect.iscoroutinefunction(f):

            @wraps(f)
            async def async_decorated_function(*args, **kwargs):
                is_secure = getattr(security_config, config_attr, False)
                starlette_request = _get_starlette_request(args, kwargs)
                result = await f(*args, is_secure=is_secure, **kwargs)

                if starlette_request is not None:
                    response = _ensure_starlette_response(result)
                    return _finalize_response(
                        response,
                        starlette_request.url.path,
                        starlette_request.headers,
                        config_attr,
                        vuln_id,
                        is_secure,
                    )

                if make_response is not None and flask_request is not None:
                    response = make_response(result)
                    return _finalize_response(
                        response,
                        flask_request.path,
                        flask_request.headers,
                        config_attr,
                        vuln_id,
                        is_secure,
                    )

                return result

            return async_decorated_function

        @wraps(f)
        def decorated_function(*args, **kwargs):
            is_secure = getattr(security_config, config_attr, False)
            result = f(*args, is_secure=is_secure, **kwargs)

            starlette_request = _get_starlette_request(args, kwargs)
            if starlette_request is not None:
                response = _ensure_starlette_response(result)
                return _finalize_response(
                    response,
                    starlette_request.url.path,
                    starlette_request.headers,
                    config_attr,
                    vuln_id,
                    is_secure,
                )

            if make_response is None or flask_request is None:
                return result

            response = make_response(result)
            return _finalize_response(
                response,
                flask_request.path,
                flask_request.headers,
                config_attr,
                vuln_id,
                is_secure,
            )

        return decorated_function

    return decorator
