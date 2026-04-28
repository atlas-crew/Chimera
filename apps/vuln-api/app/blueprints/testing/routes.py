"""
Routes for testing error conditions and WAF responses.

WARNING: This is a DEMO ENVIRONMENT with INTENTIONAL vulnerabilities.
These endpoints intentionally trigger errors for testing purposes.
NEVER use this code in production.
"""

import asyncio
import os
import random
from typing import Any, Dict, Tuple

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from . import testing_router
from app.config import app_config


def _is_json_content_type(content_type: str | None) -> bool:
    if not content_type:
        return False
    media_type = content_type.split(";", 1)[0].strip().lower()
    return media_type == "application/json" or (
        media_type.startswith("application/") and media_type.endswith("+json")
    )


@testing_router.route('/api/test/error/<error_type>', methods=['GET', 'POST'])
async def trigger_error(request: Request, error_type: str) -> Tuple[Dict[str, Any], int]:
    """
    Trigger specific error conditions for WAF testing.

    Supported error types:
        - timeout: Simulate slow operation (delay via ?delay=N)
        - memory: Attempt to allocate large memory
        - cpu: CPU-intensive operation
        - exception: Raise generic exception
        - sql: Simulate SQL injection vulnerability
        - file: Simulate file system access
        - random: Random error from the list
        - divide_zero: Division by zero
        - null_ref: Null reference error
        - type_error: Type mismatch error
        - key_error: Missing dictionary key
        - index_error: List index out of bounds

    Query Parameters:
        delay: For 'timeout', delay in seconds (default: 5)
        iterations: For 'cpu', number of iterations (default: 1000000)
        size: For 'memory', size in MB (default: 100)
        message: Custom error message

    Args:
        error_type: Type of error to trigger

    Returns:
        JSON response (usually an error)
    """
    custom_message = request.query_params.get('message', 'Triggered by test endpoint')

    if error_type == 'timeout':
        delay = int(request.query_params.get('delay', 5))
        # Use asyncio.sleep so we don't block the Starlette event loop.
        # The WSGI compat shim drives this through async_to_sync, which
        # spins up its own loop, so the WSGI path also pauses correctly.
        await asyncio.sleep(delay)
        return JSONResponse({
            "status": "completed",
            "error_type": "timeout",
            "message": f"Operation completed after {delay} seconds",
            "demo_warning": "THIS IS A DEMO - Intentionally slow for testing"
        }, status_code=200)

    elif error_type == 'memory':
        size_mb = int(request.query_params.get('size', 100))
        try:
            # Attempt to allocate large memory block
            big_list = [0] * (size_mb * 1024 * 1024 // 8)  # Each int is ~8 bytes
            return JSONResponse({
                "status": "completed",
                "error_type": "memory",
                "message": f"Allocated ~{size_mb}MB of memory",
                "list_size": len(big_list),
                "demo_warning": "THIS IS A DEMO - Intentionally wasteful for testing"
            }, status_code=200)
        except MemoryError as e:
            raise MemoryError(f"Failed to allocate {size_mb}MB: {custom_message}") from e

    elif error_type == 'cpu':
        iterations = int(request.query_params.get('iterations', 1000000))
        result = 0
        for i in range(iterations):
            result += i * i
        return JSONResponse({
            "status": "completed",
            "error_type": "cpu",
            "message": f"Completed {iterations} iterations",
            "result": result,
            "demo_warning": "THIS IS A DEMO - Intentionally CPU-intensive for testing"
        }, status_code=200)

    elif error_type == 'exception':
        raise Exception(f"Generic exception triggered: {custom_message}")

    elif error_type == 'sql':
        # Simulate SQL injection vulnerability response
        username = request.query_params.get('username', 'admin')
        password = request.query_params.get('password', 'password123')

        # INTENTIONALLY VULNERABLE - Shows what raw SQL would look like
        fake_query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"

        raise Exception(
            f"SQL Injection Test - Query attempted: {fake_query}. "
            f"Custom message: {custom_message}"
        )

    elif error_type == 'file':
        # Simulate file system access vulnerability
        filepath = request.query_params.get('path', '/etc/passwd')

        # INTENTIONALLY VULNERABLE - Shows what file access would look like
        # (we don't actually read the file, just simulate the error)
        if os.path.exists(filepath):
            raise Exception(
                f"File System Access Test - Attempted to read: {filepath}. "
                f"File exists! Custom message: {custom_message}"
            )
        else:
            raise FileNotFoundError(
                f"File System Access Test - Attempted to read: {filepath}. "
                f"File not found. Custom message: {custom_message}"
            )

    elif error_type == 'divide_zero':
        # Trigger division by zero
        denominator = int(request.query_params.get('denominator', 0))
        result = 42 / denominator
        return JSONResponse({"result": result}, status_code=200)

    elif error_type == 'null_ref':
        # Trigger AttributeError (null reference)
        obj = None
        return JSONResponse({"value": obj.some_attribute}, status_code=200)

    elif error_type == 'type_error':
        # Trigger TypeError
        result = "string" + 42
        return JSONResponse({"result": result}, status_code=200)

    elif error_type == 'key_error':
        # Trigger KeyError
        data = {"existing_key": "value"}
        key = request.query_params.get('key', 'nonexistent_key')
        return JSONResponse({"value": data[key]}, status_code=200)

    elif error_type == 'index_error':
        # Trigger IndexError
        data = [1, 2, 3]
        index = int(request.query_params.get('index', 999))
        return JSONResponse({"value": data[index]}, status_code=200)

    elif error_type == 'random':
        # Pick a random error type
        error_types = [
            'exception', 'divide_zero', 'null_ref', 'type_error',
            'key_error', 'index_error', 'sql', 'file'
        ]
        chosen_type = random.choice(error_types)
        # Recursive call to trigger the chosen error
        return await trigger_error(request, chosen_type)

    else:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown error type: {error_type}. "
                f"Supported types: timeout, memory, cpu, exception, sql, file, "
                f"random, divide_zero, null_ref, type_error, key_error, index_error"
            ),
        )


@testing_router.route('/api/test/status/<int:code>', methods=['GET', 'POST'])
async def return_status_code(request: Request, code: int) -> Tuple[Dict[str, Any], int]:
    """
    Return a specific HTTP status code for testing.

    This endpoint allows testing WAF responses to different HTTP status codes.
    Supports custom messages via query parameter.

    Query Parameters:
        message: Custom message to include in response
        abort: If 'true', use abort() instead of returning response

    Args:
        code: HTTP status code to return (100-599)

    Returns:
        JSON response with the specified status code
    """
    if code < 100 or code > 599:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status code: {code}. Must be between 100 and 599.",
        )

    custom_message = request.query_params.get('message', f'Testing HTTP {code} response')
    use_abort = request.query_params.get('abort', 'false').lower() == 'true'

    # If client wants to use abort (which triggers error handlers)
    if use_abort and code >= 400:
        raise HTTPException(status_code=code, detail=custom_message)

    # Build response with leaked information
    response_data = {
        "status_code": code,
        "message": custom_message,
        "demo_warning": "THIS IS A DEMO - Intentionally returns arbitrary status codes",
        "request_details": {
            "path": request.url.path,
            "method": request.method,
            "remote_addr": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent", "Unknown"),
        }
    }

    # Add status-specific information
    if 200 <= code < 300:
        response_data["category"] = "Success"
    elif 300 <= code < 400:
        response_data["category"] = "Redirection"
    elif 400 <= code < 500:
        response_data["category"] = "Client Error"
    elif 500 <= code < 600:
        response_data["category"] = "Server Error"
    else:
        response_data["category"] = "Informational"

    return JSONResponse(response_data, status_code=code)


@testing_router.route('/api/test/chain/<int:depth>', methods=['GET'])
async def error_chain(request: Request, depth: int) -> Dict[str, Any]:
    """
    Create a chain of nested function calls that eventually error.

    This tests stack trace depth and recursion limits.

    Args:
        depth: Number of recursive calls before erroring

    Returns:
        JSON response (or raises exception)
    """
    if depth <= 0:
        raise Exception("Reached maximum depth - triggering error in call chain")

    if depth == 1:
        # Last level - trigger the error
        return await error_chain(request, 0)
    else:
        # Recursive call with decreasing depth
        result = await error_chain(request, depth - 1)
        return result


@testing_router.route('/api/test/leak/config', methods=['GET'])
async def leak_config(request: Request) -> Dict[str, Any]:
    """
    Intentionally leak application configuration.

    WARNING: INTENTIONALLY INSECURE FOR DEMO PURPOSES.

    Returns:
        JSON response with application configuration
    """
    # Leak all configuration via the framework-agnostic app_config singleton.
    # current_app.config is Flask-only and not available under Starlette, so
    # we surface the same vulnerability surface (secret_key, debug, testing,
    # full config dump) through app_config to keep the AC behavior intact.
    config_dict = {key: repr(value) for key, value in app_config.items()}

    # Best-effort leak of Flask-specific internals when reachable through the
    # WSGI compat shim. Under native Starlette there's no current_app, so
    # these stay empty (as advertised). Both errors are swallowed so the
    # endpoint stays a stable demo target regardless of framework path.
    blueprints: list = []
    url_rules: list = []
    try:
        from flask import current_app as _ca

        blueprints = list(_ca.blueprints.keys())
        url_rules = [str(rule) for rule in _ca.url_map.iter_rules()]
    except (ImportError, RuntimeError):
        pass

    return JSONResponse({
        "demo_warning": "THIS IS A DEMO - Intentionally leaking configuration",
        "config": config_dict,
        "secret_key": app_config.secret_key,
        "debug": app_config.debug,
        "testing": app_config.testing,
        "blueprints": blueprints,
        "url_map": url_rules,
    }, status_code=200)


@testing_router.route('/api/test/leak/env', methods=['GET'])
async def leak_environment(request: Request) -> Dict[str, Any]:
    """
    Intentionally leak environment variables.

    WARNING: INTENTIONALLY INSECURE FOR DEMO PURPOSES.

    Returns:
        JSON response with environment variables
    """
    # Leak environment variables (INTENTIONALLY INSECURE)
    env_dict = dict(os.environ)

    return JSONResponse({
        "demo_warning": "THIS IS A DEMO - Intentionally leaking environment variables",
        "environment": env_dict,
        "path": os.environ.get('PATH', 'Not set'),
        "python_path": os.environ.get('PYTHONPATH', 'Not set'),
        "user": os.environ.get('USER', 'Not set'),
        "home": os.environ.get('HOME', 'Not set'),
    }, status_code=200)


@testing_router.route('/api/test/leak/headers', methods=['GET', 'POST'])
async def leak_headers(request: Request) -> Dict[str, Any]:
    """
    Echo back all request headers and data.

    Useful for testing header injection and data leakage scenarios.

    Returns:
        JSON response with all request details
    """
    # Form decoding only makes sense for form-encoded payloads. Eagerly
    # awaiting request.form() on a JSON or empty body would consume the
    # body stream and break the JSON/raw-body branches below, so guard on
    # the content type up front.
    content_type = request.headers.get("content-type", "")
    media_type = content_type.split(";", 1)[0].strip().lower()
    form_data = None
    if media_type in {"application/x-www-form-urlencoded", "multipart/form-data"}:
        try:
            form = await request.form()
            form_data = {k: v for k, v in form.items()} if form else None
        except Exception as e:
            form_data = {"_form_parse_error": str(e)}

    response = {
        "demo_warning": "THIS IS A DEMO - Intentionally echoing all request data",
        "headers": dict(request.headers),
        "method": request.method,
        "path": request.url.path,
        # Starlette exposes the raw query string as a str on request.url.query
        # (Flask's request.query_string is bytes); normalize to a string.
        "query_string": request.url.query,
        "args": dict(request.query_params),
        "form": form_data,
        "cookies": dict(request.cookies),
        "remote_addr": request.client.host if request.client else None,
        "user_agent": request.headers.get("User-Agent", "Unknown"),
    }

    # Try to include JSON body. Starlette has no request.is_json, so we sniff
    # the content type the same way Flask 3 does.
    try:
        if _is_json_content_type(content_type):
            response["json_body"] = await request.json()
    except Exception as e:
        response["json_parse_error"] = str(e)

    # Try to include raw body. Starlette uses awaitable request.body() in
    # place of Flask's request.data property.
    try:
        raw_body = await request.body()
        if raw_body:
            response["raw_body"] = raw_body.decode("utf-8", errors="replace")
    except Exception as e:
        response["raw_body_error"] = str(e)

    return JSONResponse(response, status_code=200)


@testing_router.route('/api/test/health', methods=['GET'])
async def health_check(request: Request) -> Dict[str, Any]:
    """
    Simple health check endpoint.

    Returns:
        JSON response indicating service is running
    """
    return JSONResponse({
        "status": "healthy",
        "service": "api-demo testing endpoints",
        "demo_warning": "THIS IS A DEMO ENVIRONMENT - NOT FOR PRODUCTION USE",
        "available_error_types": [
            "timeout", "memory", "cpu", "exception", "sql", "file",
            "random", "divide_zero", "null_ref", "type_error",
            "key_error", "index_error"
        ],
        "endpoints": {
            "/api/test/error/<type>": "Trigger specific error condition",
            "/api/test/status/<code>": "Return specific HTTP status code",
            "/api/test/chain/<depth>": "Create error call chain",
            "/api/test/leak/config": "Leak application configuration",
            "/api/test/leak/env": "Leak environment variables",
            "/api/test/leak/headers": "Echo all request data",
            "/api/test/health": "Health check endpoint"
        }
    }, status_code=200)
