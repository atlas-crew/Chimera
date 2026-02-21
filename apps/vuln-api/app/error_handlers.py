"""
Intentionally verbose error handlers for WAF testing/honeypot demonstration.

WARNING: This is a DEMO ENVIRONMENT with INTENTIONAL vulnerabilities.
These error handlers LEAK information on purpose for testing WAF protection.
NEVER use this code in production.
"""

import traceback
import sys
from datetime import datetime
from typing import Dict, Any, Tuple

from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException


class DemoErrorHandler:
    """
    Intentionally insecure error handler that leaks maximum information.

    This class is designed for WAF testing and honeypot scenarios where
    verbose error responses are needed to test security controls.
    """

    def __init__(self, app: Flask) -> None:
        """
        Initialize error handlers with the Flask app.

        Args:
            app: Flask application instance
        """
        self.app = app
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register all error handlers with the Flask app."""
        # HTTP error codes
        self.app.register_error_handler(400, self.handle_bad_request)
        self.app.register_error_handler(401, self.handle_unauthorized)
        self.app.register_error_handler(403, self.handle_forbidden)
        self.app.register_error_handler(404, self.handle_not_found)
        self.app.register_error_handler(500, self.handle_internal_error)

        # Generic exception handler (catches all unhandled exceptions)
        self.app.register_error_handler(Exception, self.handle_generic_exception)

    def _build_error_response(
        self,
        error_type: str,
        status_code: int,
        message: str,
        exception: Exception = None,
        include_trace: bool = True
    ) -> Tuple[Dict[str, Any], int]:
        """
        Build verbose error response with maximum information leakage.

        Args:
            error_type: Type of error (e.g., "BadRequest", "InternalError")
            status_code: HTTP status code
            message: Error message
            exception: Optional exception object
            include_trace: Whether to include stack trace

        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {
            "error": error_type,
            "status_code": status_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "demo_warning": "THIS IS A DEMO ENVIRONMENT - INTENTIONALLY INSECURE FOR TESTING",
            "path": request.path,
            "method": request.method,
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", "Unknown"),
            "request_id": request.environ.get("REQUEST_ID", "N/A"),
        }

        # Leak all request data
        response["leaked_data"] = {
            "headers": dict(request.headers),
            "args": dict(request.args),
            "form": dict(request.form) if request.form else None,
            "cookies": dict(request.cookies),
            "content_type": request.content_type,
            "content_length": request.content_length,
        }

        # Try to include JSON body if present
        try:
            if request.is_json:
                response["leaked_data"]["json_body"] = request.get_json(force=True)
        except Exception as e:
            response["leaked_data"]["json_parse_error"] = str(e)

        # Try to include raw body
        try:
            if request.data:
                response["leaked_data"]["raw_body"] = request.data.decode("utf-8", errors="replace")
        except Exception as e:
            response["leaked_data"]["raw_body_error"] = str(e)

        # Leak environment information
        response["environment"] = {
            "python_version": sys.version,
            "flask_debug": self.app.debug,
            "flask_env": self.app.config.get("ENV", "unknown"),
        }

        # Include exception details if available
        if exception:
            response["exception_details"] = {
                "type": type(exception).__name__,
                "message": str(exception),
                "args": exception.args,
            }

            # Include stack trace for maximum information leakage
            if include_trace:
                response["stack_trace"] = traceback.format_exception(
                    type(exception),
                    exception,
                    exception.__traceback__
                )

                # Also include local variables from each frame
                tb = exception.__traceback__
                frames = []
                while tb is not None:
                    frame = tb.tb_frame
                    frames.append({
                        "filename": frame.f_code.co_filename,
                        "function": frame.f_code.co_name,
                        "line_number": tb.tb_lineno,
                        "local_vars": {k: repr(v) for k, v in frame.f_locals.items()},
                    })
                    tb = tb.tb_next
                response["stack_frames"] = frames

        return response, status_code

    def handle_bad_request(self, error: HTTPException) -> Tuple[Dict[str, Any], int]:
        """
        Handle 400 Bad Request errors with verbose output.

        Args:
            error: HTTPException instance

        Returns:
            JSON response with leaked information
        """
        return self._build_error_response(
            error_type="BadRequest",
            status_code=400,
            message=f"Invalid request: {error.description}",
            exception=error
        )

    def handle_unauthorized(self, error: HTTPException) -> Tuple[Dict[str, Any], int]:
        """
        Handle 401 Unauthorized errors with leaked auth information.

        Args:
            error: HTTPException instance

        Returns:
            JSON response with leaked authentication details
        """
        response, code = self._build_error_response(
            error_type="Unauthorized",
            status_code=401,
            message="Authentication required or invalid credentials",
            exception=error
        )

        # Leak authentication attempts (INTENTIONALLY INSECURE)
        response["auth_debug"] = {
            "authorization_header": request.headers.get("Authorization", "Not provided"),
            "basic_auth_username": request.authorization.username if request.authorization else None,
            "session_data": dict(request.cookies),
        }

        return response, code

    def handle_forbidden(self, error: HTTPException) -> Tuple[Dict[str, Any], int]:
        """
        Handle 403 Forbidden errors with leaked permission information.

        Args:
            error: HTTPException instance

        Returns:
            JSON response with leaked permission details
        """
        response, code = self._build_error_response(
            error_type="Forbidden",
            status_code=403,
            message="Access denied - insufficient permissions",
            exception=error
        )

        # Leak permission information (INTENTIONALLY INSECURE)
        response["permission_debug"] = {
            "required_permissions": "Not implemented in demo",
            "user_permissions": "Not implemented in demo",
            "resource_owner": "Not implemented in demo",
        }

        return response, code

    def handle_not_found(self, error: HTTPException) -> Tuple[Dict[str, Any], int]:
        """
        Handle 404 Not Found errors with leaked path information.

        Args:
            error: HTTPException instance

        Returns:
            JSON response with leaked routing details
        """
        response, code = self._build_error_response(
            error_type="NotFound",
            status_code=404,
            message=f"Resource not found: {request.path}",
            exception=error
        )

        # Leak routing information (INTENTIONALLY INSECURE)
        response["routing_debug"] = {
            "requested_path": request.path,
            "available_endpoints": [str(rule) for rule in self.app.url_map.iter_rules()],
            "blueprint": request.blueprint,
            "endpoint": request.endpoint,
        }

        return response, code

    def handle_internal_error(self, error: Exception) -> Tuple[Dict[str, Any], int]:
        """
        Handle 500 Internal Server Error with maximum debug information.

        Args:
            error: Exception instance

        Returns:
            JSON response with full stack trace and system state
        """
        response, code = self._build_error_response(
            error_type="InternalServerError",
            status_code=500,
            message="Internal server error - see debug details below",
            exception=error,
            include_trace=True
        )

        # Leak additional system state (INTENTIONALLY INSECURE)
        response["system_debug"] = {
            "config_keys": list(self.app.config.keys()),
            "registered_blueprints": list(self.app.blueprints.keys()),
            "extensions": list(self.app.extensions.keys()) if hasattr(self.app, 'extensions') else [],
        }

        return response, code

    def handle_generic_exception(self, error: Exception) -> Tuple[Dict[str, Any], int]:
        """
        Catch-all handler for any unhandled exception.

        Args:
            error: Exception instance

        Returns:
            JSON response with comprehensive error details
        """
        # If it's an HTTPException, let specific handlers deal with it
        if isinstance(error, HTTPException):
            return error

        # Otherwise, treat as 500 with full debugging
        response, code = self._build_error_response(
            error_type=type(error).__name__,
            status_code=500,
            message=f"Unhandled exception: {str(error)}",
            exception=error,
            include_trace=True
        )

        # Add extra debugging for unexpected errors
        response["debugging_hint"] = (
            "This is an unhandled exception. In production, this would be logged "
            "and a generic error shown. This demo intentionally exposes all details."
        )

        return response, code


def register_error_handlers(app: Flask) -> None:
    """
    Convenience function to register all demo error handlers.

    Args:
        app: Flask application instance
    """
    DemoErrorHandler(app)
