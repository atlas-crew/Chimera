"""
Standardized response helpers for consistent API responses.

Provides utility functions for building JSON responses with standard
structures for success, error, and data payloads.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from flask import jsonify, Response
from werkzeug.http import HTTP_STATUS_CODES


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> tuple[Response, int]:
    """
    Build a standardized success response.

    Args:
        data: Response payload data
        message: Optional success message
        status_code: HTTP status code (default 200)
        headers: Optional additional headers
        metadata: Optional metadata (pagination, timestamps, etc.)

    Returns:
        Tuple of (Response, status_code)

    Example:
        return success_response(
            data={'user_id': '123'},
            message='User created successfully',
            status_code=201
        )
    """
    response_body = {
        'success': True,
        'timestamp': datetime.now().isoformat()
    }

    if message:
        response_body['message'] = message

    if data is not None:
        response_body['data'] = data

    if metadata:
        response_body['metadata'] = metadata

    response = jsonify(response_body)

    if headers:
        for key, value in headers.items():
            response.headers[key] = value

    return response, status_code


def error_response(
    message: str,
    code: str = 'ERROR',
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> tuple[Response, int]:
    """
    Build a standardized error response.

    Args:
        message: Error message
        code: Error code for programmatic handling
        status_code: HTTP status code (default 400)
        details: Optional additional error details
        headers: Optional additional headers

    Returns:
        Tuple of (Response, status_code)

    Example:
        return error_response(
            message='Invalid email format',
            code='VALIDATION_ERROR',
            status_code=400,
            details={'field': 'email'}
        )
    """
    response_body = {
        'success': False,
        'error': {
            'message': message,
            'code': code,
            'timestamp': datetime.now().isoformat()
        }
    }

    if details:
        response_body['error']['details'] = details

    # Add HTTP status text for context
    if status_code in HTTP_STATUS_CODES:
        response_body['error']['status'] = HTTP_STATUS_CODES[status_code]

    response = jsonify(response_body)

    if headers:
        for key, value in headers.items():
            response.headers[key] = value

    return response, status_code


def validation_error_response(
    errors: Union[Dict[str, str], List[Dict[str, str]]],
    message: str = 'Validation failed',
    status_code: int = 400
) -> tuple[Response, int]:
    """
    Build a response for validation errors.

    Args:
        errors: Validation errors (field-level or list of errors)
        message: Overall error message
        status_code: HTTP status code (default 400)

    Returns:
        Tuple of (Response, status_code)

    Example:
        return validation_error_response(
            errors={'email': 'Invalid format', 'password': 'Too short'},
            message='Input validation failed'
        )
    """
    return error_response(
        message=message,
        code='VALIDATION_ERROR',
        status_code=status_code,
        details={'validation_errors': errors}
    )


def not_found_response(
    resource: str = 'Resource',
    resource_id: Optional[str] = None
) -> tuple[Response, int]:
    """
    Build a 404 Not Found response.

    Args:
        resource: Type of resource not found
        resource_id: Optional ID of the resource

    Returns:
        Tuple of (Response, 404)

    Example:
        return not_found_response('User', user_id='123')
    """
    if resource_id:
        message = f"{resource} with ID '{resource_id}' not found"
    else:
        message = f"{resource} not found"

    return error_response(
        message=message,
        code='NOT_FOUND',
        status_code=404
    )


def unauthorized_response(
    message: str = 'Authentication required',
    code: str = 'UNAUTHORIZED'
) -> tuple[Response, int]:
    """
    Build a 401 Unauthorized response.

    Args:
        message: Error message
        code: Error code

    Returns:
        Tuple of (Response, 401)
    """
    return error_response(
        message=message,
        code=code,
        status_code=401,
        headers={'WWW-Authenticate': 'Bearer'}
    )


def forbidden_response(
    message: str = 'Access denied',
    code: str = 'FORBIDDEN'
) -> tuple[Response, int]:
    """
    Build a 403 Forbidden response.

    Args:
        message: Error message
        code: Error code

    Returns:
        Tuple of (Response, 403)
    """
    return error_response(
        message=message,
        code=code,
        status_code=403
    )


def conflict_response(
    message: str,
    resource: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> tuple[Response, int]:
    """
    Build a 409 Conflict response.

    Args:
        message: Error message
        resource: Type of resource in conflict
        details: Optional additional details

    Returns:
        Tuple of (Response, 409)

    Example:
        return conflict_response(
            message='Email already registered',
            resource='User',
            details={'email': 'user@example.com'}
        )
    """
    error_details = details or {}
    if resource:
        error_details['resource'] = resource

    return error_response(
        message=message,
        code='CONFLICT',
        status_code=409,
        details=error_details
    )


def too_many_requests_response(
    message: str = 'Rate limit exceeded',
    retry_after: Optional[int] = None
) -> tuple[Response, int]:
    """
    Build a 429 Too Many Requests response.

    Args:
        message: Error message
        retry_after: Optional seconds until rate limit resets

    Returns:
        Tuple of (Response, 429)
    """
    headers = {}
    if retry_after:
        headers['Retry-After'] = str(retry_after)

    return error_response(
        message=message,
        code='RATE_LIMIT_EXCEEDED',
        status_code=429,
        headers=headers,
        details={'retry_after': retry_after} if retry_after else None
    )


def internal_server_error_response(
    message: str = 'Internal server error',
    error_id: Optional[str] = None,
    include_details: bool = False,
    details: Optional[Dict[str, Any]] = None
) -> tuple[Response, int]:
    """
    Build a 500 Internal Server Error response.

    Args:
        message: Error message (should be generic for security)
        error_id: Optional error tracking ID
        include_details: If True, include error details (dev mode only)
        details: Optional error details

    Returns:
        Tuple of (Response, 500)

    Example:
        return internal_server_error_response(
            error_id='ERR-2024-001',
            include_details=app.debug,
            details={'exception': str(e)}
        )
    """
    error_details = {}
    if error_id:
        error_details['error_id'] = error_id
        message = f"{message}. Reference ID: {error_id}"

    if include_details and details:
        error_details.update(details)

    return error_response(
        message=message,
        code='INTERNAL_ERROR',
        status_code=500,
        details=error_details if error_details else None
    )


def created_response(
    data: Any,
    resource_url: Optional[str] = None,
    message: Optional[str] = None
) -> tuple[Response, int]:
    """
    Build a 201 Created response.

    Args:
        data: Created resource data
        resource_url: Optional URL of the created resource
        message: Optional success message

    Returns:
        Tuple of (Response, 201)

    Example:
        return created_response(
            data={'user_id': '123', 'email': 'user@example.com'},
            resource_url='/api/users/123',
            message='User created successfully'
        )
    """
    headers = {}
    if resource_url:
        headers['Location'] = resource_url

    return success_response(
        data=data,
        message=message,
        status_code=201,
        headers=headers
    )


def accepted_response(
    message: str = 'Request accepted for processing',
    job_id: Optional[str] = None,
    status_url: Optional[str] = None
) -> tuple[Response, int]:
    """
    Build a 202 Accepted response for async operations.

    Args:
        message: Success message
        job_id: Optional job/task ID for tracking
        status_url: Optional URL to check operation status

    Returns:
        Tuple of (Response, 202)

    Example:
        return accepted_response(
            message='Export job started',
            job_id='job-123',
            status_url='/api/jobs/job-123'
        )
    """
    data = {}
    if job_id:
        data['job_id'] = job_id
    if status_url:
        data['status_url'] = status_url

    headers = {}
    if status_url:
        headers['Location'] = status_url

    return success_response(
        data=data if data else None,
        message=message,
        status_code=202,
        headers=headers
    )


def no_content_response() -> tuple[Response, int]:
    """
    Build a 204 No Content response.

    Returns:
        Tuple of (Response, 204)

    Example:
        # For successful DELETE operations
        return no_content_response()
    """
    return jsonify({}), 204


def paginated_response(
    items: List[Any],
    page: int,
    per_page: int,
    total_items: int,
    message: Optional[str] = None
) -> tuple[Response, int]:
    """
    Build a paginated response with metadata.

    Args:
        items: List of items for current page
        page: Current page number (1-indexed)
        per_page: Items per page
        total_items: Total number of items across all pages
        message: Optional success message

    Returns:
        Tuple of (Response, 200)

    Example:
        return paginated_response(
            items=users,
            page=2,
            per_page=10,
            total_items=45
        )
    """
    total_pages = (total_items + per_page - 1) // per_page  # Ceiling division

    metadata = {
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }

    return success_response(
        data=items,
        message=message,
        metadata=metadata
    )


def build_api_envelope(
    data: Any,
    success: bool = True,
    message: Optional[str] = None,
    errors: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Build a complete API response envelope (not jsonified).

    Useful when you need to manipulate the response dict before returning.

    Args:
        data: Response data
        success: Whether operation succeeded
        message: Optional message
        errors: Optional list of error messages
        warnings: Optional list of warning messages

    Returns:
        Response dictionary

    Example:
        envelope = build_api_envelope(
            data={'user': user_data},
            success=True,
            warnings=['Email verification pending']
        )
        return jsonify(envelope), 200
    """
    response = {
        'success': success,
        'timestamp': datetime.now().isoformat()
    }

    if message:
        response['message'] = message

    if data is not None:
        response['data'] = data

    if errors:
        response['errors'] = errors

    if warnings:
        response['warnings'] = warnings

    return response
