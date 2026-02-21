"""
Input validation utilities for the demo application.

Provides validation functions with optional bypass capabilities for
intentionally vulnerable WAF testing endpoints.
"""

import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from functools import wraps
from flask import request, jsonify


# Validation patterns
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_PATTERN = re.compile(r'^\+?1?\d{10,15}$')
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
SQL_INJECTION_PATTERN = re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE)\b|--|;|\/\*|\*\/|'|\")", re.IGNORECASE)
XSS_PATTERN = re.compile(r'(<script|javascript:|onerror=|onload=|<iframe)', re.IGNORECASE)
PATH_TRAVERSAL_PATTERN = re.compile(r'\.\.|\/etc\/|\/root\/|\\\\|%2e%2e', re.IGNORECASE)
COMMAND_INJECTION_PATTERN = re.compile(r'[;&|`$(){}[\]<>]')


class ValidationError(Exception):
    """
    Custom exception for validation errors.

    Attributes:
        field: The field that failed validation
        message: Human-readable error message
        code: Error code for programmatic handling
    """

    def __init__(self, field: str, message: str, code: str = "VALIDATION_ERROR"):
        self.field = field
        self.message = message
        self.code = code
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON responses."""
        return {
            'field': self.field,
            'message': self.message,
            'code': self.code
        }


def validate_email(
    email: str,
    required: bool = True,
    bypass: bool = False
) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate
        required: If True, empty values are invalid
        bypass: If True, skip validation (for vulnerable endpoints)

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    if bypass:
        return True

    if not email:
        if required:
            raise ValidationError('email', 'Email is required', 'REQUIRED_FIELD')
        return True

    if not EMAIL_PATTERN.match(email):
        raise ValidationError('email', 'Invalid email format', 'INVALID_FORMAT')

    return True


def validate_string(
    value: str,
    field_name: str,
    min_length: int = 0,
    max_length: int = 1000,
    pattern: Optional[re.Pattern] = None,
    required: bool = True,
    bypass: bool = False
) -> bool:
    """
    Validate string field with configurable constraints.

    Args:
        value: String to validate
        field_name: Name of the field (for error messages)
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        pattern: Optional regex pattern to match
        required: If True, empty values are invalid
        bypass: If True, skip validation

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    if bypass:
        return True

    if not value:
        if required:
            raise ValidationError(field_name, f'{field_name} is required', 'REQUIRED_FIELD')
        return True

    if not isinstance(value, str):
        raise ValidationError(field_name, f'{field_name} must be a string', 'INVALID_TYPE')

    if len(value) < min_length:
        raise ValidationError(
            field_name,
            f'{field_name} must be at least {min_length} characters',
            'TOO_SHORT'
        )

    if len(value) > max_length:
        raise ValidationError(
            field_name,
            f'{field_name} must not exceed {max_length} characters',
            'TOO_LONG'
        )

    if pattern and not pattern.match(value):
        raise ValidationError(
            field_name,
            f'{field_name} format is invalid',
            'INVALID_FORMAT'
        )

    return True


def validate_integer(
    value: Any,
    field_name: str,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    required: bool = True,
    bypass: bool = False
) -> bool:
    """
    Validate integer field with range constraints.

    Args:
        value: Value to validate
        field_name: Name of the field
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        required: If True, None is invalid
        bypass: If True, skip validation

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    if bypass:
        return True

    if value is None:
        if required:
            raise ValidationError(field_name, f'{field_name} is required', 'REQUIRED_FIELD')
        return True

    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(field_name, f'{field_name} must be an integer', 'INVALID_TYPE')

    if min_value is not None and int_value < min_value:
        raise ValidationError(
            field_name,
            f'{field_name} must be at least {min_value}',
            'OUT_OF_RANGE'
        )

    if max_value is not None and int_value > max_value:
        raise ValidationError(
            field_name,
            f'{field_name} must not exceed {max_value}',
            'OUT_OF_RANGE'
        )

    return True


def validate_float(
    value: Any,
    field_name: str,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    required: bool = True,
    bypass: bool = False
) -> bool:
    """
    Validate float field with range constraints.

    Args:
        value: Value to validate
        field_name: Name of the field
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        required: If True, None is invalid
        bypass: If True, skip validation

    Returns:
        True if valid

    Raises:
        ValidationError: If validation fails
    """
    if bypass:
        return True

    if value is None:
        if required:
            raise ValidationError(field_name, f'{field_name} is required', 'REQUIRED_FIELD')
        return True

    try:
        float_value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(field_name, f'{field_name} must be a number', 'INVALID_TYPE')

    if min_value is not None and float_value < min_value:
        raise ValidationError(
            field_name,
            f'{field_name} must be at least {min_value}',
            'OUT_OF_RANGE'
        )

    if max_value is not None and float_value > max_value:
        raise ValidationError(
            field_name,
            f'{field_name} must not exceed {max_value}',
            'OUT_OF_RANGE'
        )

    return True


def check_sql_injection(
    value: str,
    field_name: str,
    bypass: bool = False
) -> bool:
    """
    Check for SQL injection patterns.

    Args:
        value: String to check
        field_name: Name of the field
        bypass: If True, skip check (for vulnerable endpoints)

    Returns:
        True if safe

    Raises:
        ValidationError: If SQL injection pattern detected
    """
    if bypass or not value:
        return True

    if SQL_INJECTION_PATTERN.search(value):
        raise ValidationError(
            field_name,
            f'{field_name} contains potentially dangerous content',
            'SECURITY_VIOLATION'
        )

    return True


def check_xss(
    value: str,
    field_name: str,
    bypass: bool = False
) -> bool:
    """
    Check for XSS (Cross-Site Scripting) patterns.

    Args:
        value: String to check
        field_name: Name of the field
        bypass: If True, skip check

    Returns:
        True if safe

    Raises:
        ValidationError: If XSS pattern detected
    """
    if bypass or not value:
        return True

    if XSS_PATTERN.search(value):
        raise ValidationError(
            field_name,
            f'{field_name} contains potentially dangerous content',
            'SECURITY_VIOLATION'
        )

    return True


def check_path_traversal(
    value: str,
    field_name: str,
    bypass: bool = False
) -> bool:
    """
    Check for path traversal patterns.

    Args:
        value: String to check
        field_name: Name of the field
        bypass: If True, skip check

    Returns:
        True if safe

    Raises:
        ValidationError: If path traversal pattern detected
    """
    if bypass or not value:
        return True

    if PATH_TRAVERSAL_PATTERN.search(value):
        raise ValidationError(
            field_name,
            f'{field_name} contains invalid path characters',
            'SECURITY_VIOLATION'
        )

    return True


def check_command_injection(
    value: str,
    field_name: str,
    bypass: bool = False
) -> bool:
    """
    Check for command injection patterns.

    Args:
        value: String to check
        field_name: Name of the field
        bypass: If True, skip check

    Returns:
        True if safe

    Raises:
        ValidationError: If command injection pattern detected
    """
    if bypass or not value:
        return True

    if COMMAND_INJECTION_PATTERN.search(value):
        raise ValidationError(
            field_name,
            f'{field_name} contains invalid characters',
            'SECURITY_VIOLATION'
        )

    return True


def sanitize_input(
    data: Dict[str, Any],
    allowed_fields: List[str],
    bypass: bool = False
) -> Dict[str, Any]:
    """
    Sanitize input dictionary by removing unexpected fields.

    Args:
        data: Input dictionary
        allowed_fields: List of allowed field names
        bypass: If True, allow all fields

    Returns:
        Sanitized dictionary with only allowed fields
    """
    if bypass:
        return data

    return {k: v for k, v in data.items() if k in allowed_fields}


def validate_required_fields(
    data: Dict[str, Any],
    required_fields: List[str],
    bypass: bool = False
) -> bool:
    """
    Validate that all required fields are present.

    Args:
        data: Input dictionary
        required_fields: List of required field names
        bypass: If True, skip validation

    Returns:
        True if all required fields present

    Raises:
        ValidationError: If any required field is missing
    """
    if bypass:
        return True

    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            raise ValidationError(field, f'{field} is required', 'REQUIRED_FIELD')

    return True


def validate_json_request(
    required_fields: Optional[List[str]] = None,
    bypass_validation: bool = False
):
    """
    Decorator to validate JSON request data.

    Args:
        required_fields: List of required field names
        bypass_validation: If True, skip validation

    Returns:
        Decorated function

    Example:
        @app.route('/api/user', methods=['POST'])
        @validate_json_request(required_fields=['email', 'name'])
        def create_user():
            data = request.get_json()
            # data is guaranteed to have email and name fields
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not bypass_validation:
                if not request.is_json:
                    return jsonify({
                        'error': 'Content-Type must be application/json',
                        'code': 'INVALID_CONTENT_TYPE'
                    }), 400

                data = request.get_json()
                if data is None:
                    return jsonify({
                        'error': 'Request body must be valid JSON',
                        'code': 'INVALID_JSON'
                    }), 400

                if required_fields:
                    try:
                        validate_required_fields(data, required_fields)
                    except ValidationError as e:
                        return jsonify({'error': e.to_dict()}), 400

            return f(*args, **kwargs)
        return wrapper
    return decorator


def validate_query_params(
    params: Dict[str, Any],
    schema: Dict[str, Dict[str, Any]],
    bypass: bool = False
) -> Dict[str, Any]:
    """
    Validate and convert query parameters according to schema.

    Args:
        params: Raw query parameters
        schema: Schema defining expected parameters
        bypass: If True, skip validation

    Returns:
        Validated and converted parameters

    Example:
        schema = {
            'page': {'type': 'int', 'default': 1, 'min': 1},
            'limit': {'type': 'int', 'default': 10, 'min': 1, 'max': 100}
        }
        validated = validate_query_params(request.args, schema)
    """
    if bypass:
        return params

    result = {}
    for key, rules in schema.items():
        value = params.get(key, rules.get('default'))

        if value is None and rules.get('required', False):
            raise ValidationError(key, f'{key} is required', 'REQUIRED_FIELD')

        if value is not None:
            param_type = rules.get('type', 'str')

            if param_type == 'int':
                validate_integer(
                    value,
                    key,
                    min_value=rules.get('min'),
                    max_value=rules.get('max'),
                    required=rules.get('required', False)
                )
                result[key] = int(value)
            elif param_type == 'float':
                validate_float(
                    value,
                    key,
                    min_value=rules.get('min'),
                    max_value=rules.get('max'),
                    required=rules.get('required', False)
                )
                result[key] = float(value)
            elif param_type == 'bool':
                result[key] = value.lower() in ('true', '1', 'yes')
            else:
                result[key] = value

    return result
