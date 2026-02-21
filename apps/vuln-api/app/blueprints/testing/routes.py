"""
Routes for testing error conditions and WAF responses.

WARNING: This is a DEMO ENVIRONMENT with INTENTIONAL vulnerabilities.
These endpoints intentionally trigger errors for testing purposes.
NEVER use this code in production.
"""

import time
import random
import os
from typing import Dict, Any, Tuple

from flask import request, jsonify, abort
from werkzeug.exceptions import HTTPException

from . import testing_bp


@testing_bp.route('/error/<error_type>', methods=['GET', 'POST'])
def trigger_error(error_type: str) -> Tuple[Dict[str, Any], int]:
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
    custom_message = request.args.get('message', 'Triggered by test endpoint')

    if error_type == 'timeout':
        delay = int(request.args.get('delay', 5))
        time.sleep(delay)
        return jsonify({
            "status": "completed",
            "error_type": "timeout",
            "message": f"Operation completed after {delay} seconds",
            "demo_warning": "THIS IS A DEMO - Intentionally slow for testing"
        }), 200

    elif error_type == 'memory':
        size_mb = int(request.args.get('size', 100))
        try:
            # Attempt to allocate large memory block
            big_list = [0] * (size_mb * 1024 * 1024 // 8)  # Each int is ~8 bytes
            return jsonify({
                "status": "completed",
                "error_type": "memory",
                "message": f"Allocated ~{size_mb}MB of memory",
                "list_size": len(big_list),
                "demo_warning": "THIS IS A DEMO - Intentionally wasteful for testing"
            }), 200
        except MemoryError as e:
            raise MemoryError(f"Failed to allocate {size_mb}MB: {custom_message}") from e

    elif error_type == 'cpu':
        iterations = int(request.args.get('iterations', 1000000))
        result = 0
        for i in range(iterations):
            result += i * i
        return jsonify({
            "status": "completed",
            "error_type": "cpu",
            "message": f"Completed {iterations} iterations",
            "result": result,
            "demo_warning": "THIS IS A DEMO - Intentionally CPU-intensive for testing"
        }), 200

    elif error_type == 'exception':
        raise Exception(f"Generic exception triggered: {custom_message}")

    elif error_type == 'sql':
        # Simulate SQL injection vulnerability response
        username = request.args.get('username', 'admin')
        password = request.args.get('password', 'password123')

        # INTENTIONALLY VULNERABLE - Shows what raw SQL would look like
        fake_query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"

        raise Exception(
            f"SQL Injection Test - Query attempted: {fake_query}. "
            f"Custom message: {custom_message}"
        )

    elif error_type == 'file':
        # Simulate file system access vulnerability
        filepath = request.args.get('path', '/etc/passwd')

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
        denominator = int(request.args.get('denominator', 0))
        result = 42 / denominator
        return jsonify({"result": result}), 200

    elif error_type == 'null_ref':
        # Trigger AttributeError (null reference)
        obj = None
        return jsonify({"value": obj.some_attribute}), 200

    elif error_type == 'type_error':
        # Trigger TypeError
        result = "string" + 42
        return jsonify({"result": result}), 200

    elif error_type == 'key_error':
        # Trigger KeyError
        data = {"existing_key": "value"}
        key = request.args.get('key', 'nonexistent_key')
        return jsonify({"value": data[key]}), 200

    elif error_type == 'index_error':
        # Trigger IndexError
        data = [1, 2, 3]
        index = int(request.args.get('index', 999))
        return jsonify({"value": data[index]}), 200

    elif error_type == 'random':
        # Pick a random error type
        error_types = [
            'exception', 'divide_zero', 'null_ref', 'type_error',
            'key_error', 'index_error', 'sql', 'file'
        ]
        chosen_type = random.choice(error_types)
        # Recursive call to trigger the chosen error
        return trigger_error(chosen_type)

    else:
        abort(400, description=f"Unknown error type: {error_type}. "
                              f"Supported types: timeout, memory, cpu, exception, sql, file, "
                              f"random, divide_zero, null_ref, type_error, key_error, index_error")


@testing_bp.route('/status/<int:code>', methods=['GET', 'POST'])
def return_status_code(code: int) -> Tuple[Dict[str, Any], int]:
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
        abort(400, description=f"Invalid status code: {code}. Must be between 100 and 599.")

    custom_message = request.args.get('message', f'Testing HTTP {code} response')
    use_abort = request.args.get('abort', 'false').lower() == 'true'

    # If client wants to use abort (which triggers error handlers)
    if use_abort and code >= 400:
        abort(code, description=custom_message)

    # Build response with leaked information
    response_data = {
        "status_code": code,
        "message": custom_message,
        "demo_warning": "THIS IS A DEMO - Intentionally returns arbitrary status codes",
        "request_details": {
            "path": request.path,
            "method": request.method,
            "remote_addr": request.remote_addr,
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

    return jsonify(response_data), code


@testing_bp.route('/chain/<int:depth>', methods=['GET'])
def error_chain(depth: int) -> Dict[str, Any]:
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
        return error_chain(0)
    else:
        # Recursive call with decreasing depth
        result = error_chain(depth - 1)
        return result


@testing_bp.route('/leak/config', methods=['GET'])
def leak_config() -> Dict[str, Any]:
    """
    Intentionally leak Flask application configuration.

    WARNING: INTENTIONALLY INSECURE FOR DEMO PURPOSES.

    Returns:
        JSON response with application configuration
    """
    from flask import current_app

    # Leak all configuration (INTENTIONALLY INSECURE)
    config_dict = {key: repr(value) for key, value in current_app.config.items()}

    return jsonify({
        "demo_warning": "THIS IS A DEMO - Intentionally leaking configuration",
        "config": config_dict,
        "secret_key": current_app.secret_key,
        "debug": current_app.debug,
        "testing": current_app.testing,
        "blueprints": list(current_app.blueprints.keys()),
        "url_map": [str(rule) for rule in current_app.url_map.iter_rules()],
    }), 200


@testing_bp.route('/leak/env', methods=['GET'])
def leak_environment() -> Dict[str, Any]:
    """
    Intentionally leak environment variables.

    WARNING: INTENTIONALLY INSECURE FOR DEMO PURPOSES.

    Returns:
        JSON response with environment variables
    """
    # Leak environment variables (INTENTIONALLY INSECURE)
    env_dict = dict(os.environ)

    return jsonify({
        "demo_warning": "THIS IS A DEMO - Intentionally leaking environment variables",
        "environment": env_dict,
        "path": os.environ.get('PATH', 'Not set'),
        "python_path": os.environ.get('PYTHONPATH', 'Not set'),
        "user": os.environ.get('USER', 'Not set'),
        "home": os.environ.get('HOME', 'Not set'),
    }), 200


@testing_bp.route('/leak/headers', methods=['GET', 'POST'])
def leak_headers() -> Dict[str, Any]:
    """
    Echo back all request headers and data.

    Useful for testing header injection and data leakage scenarios.

    Returns:
        JSON response with all request details
    """
    response = {
        "demo_warning": "THIS IS A DEMO - Intentionally echoing all request data",
        "headers": dict(request.headers),
        "method": request.method,
        "path": request.path,
        "query_string": request.query_string.decode('utf-8'),
        "args": dict(request.args),
        "form": dict(request.form) if request.form else None,
        "cookies": dict(request.cookies),
        "remote_addr": request.remote_addr,
        "user_agent": request.headers.get("User-Agent", "Unknown"),
    }

    # Try to include JSON body
    try:
        if request.is_json:
            response["json_body"] = request.get_json(force=True)
    except Exception as e:
        response["json_parse_error"] = str(e)

    # Try to include raw body
    try:
        if request.data:
            response["raw_body"] = request.data.decode("utf-8", errors="replace")
    except Exception as e:
        response["raw_body_error"] = str(e)

    return jsonify(response), 200


@testing_bp.route('/health', methods=['GET'])
def health_check() -> Dict[str, Any]:
    """
    Simple health check endpoint.

    Returns:
        JSON response indicating service is running
    """
    return jsonify({
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
    }), 200
