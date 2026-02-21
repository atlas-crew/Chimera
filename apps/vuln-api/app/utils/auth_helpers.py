"""
Authentication and authorization helper utilities.

Provides token generation, validation, session management, and API key
handling with support for demo/weak credentials for WAF testing.
"""

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from functools import wraps
from flask import request, g
from app.utils.responses import unauthorized_response, forbidden_response


# Demo secret key - NOT for production use
SECRET_KEY = 'chimera-demo-secret-key-not-secure'
TOKEN_EXPIRY_SECONDS = 3600  # 1 hour
REFRESH_TOKEN_EXPIRY_SECONDS = 86400 * 7  # 7 days
API_KEY_PREFIX = 'tx_'


class TokenError(Exception):
    """Exception raised for token-related errors."""
    pass


def generate_token(
    user_id: str,
    additional_claims: Optional[Dict[str, Any]] = None,
    expiry_seconds: int = TOKEN_EXPIRY_SECONDS,
    weak_signing: bool = False
) -> str:
    """
    Generate a JWT-like token (simplified for demo).

    Args:
        user_id: User identifier
        additional_claims: Optional additional claims to include
        expiry_seconds: Token expiry time in seconds
        weak_signing: If True, use weak signing for vulnerable endpoints

    Returns:
        Signed token string

    Note:
        This is a simplified token implementation for demo purposes.
        Production code should use proper JWT libraries (PyJWT, etc.)
    """
    issued_at = int(time.time())
    expires_at = issued_at + expiry_seconds

    payload = {
        'user_id': user_id,
        'iat': issued_at,
        'exp': expires_at
    }

    if additional_claims:
        payload.update(additional_claims)

    # Simple token format: base64(payload) + '.' + signature
    import base64
    import json

    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip('=')

    if weak_signing:
        # Weak signature for vulnerable endpoint testing
        signature = hashlib.md5(payload_b64.encode()).hexdigest()
    else:
        # HMAC-SHA256 signature
        signature = hmac.new(
            SECRET_KEY.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()

    return f"{payload_b64}.{signature}"


def verify_token(
    token: str,
    weak_signing: bool = False,
    skip_expiry: bool = False
) -> Dict[str, Any]:
    """
    Verify and decode a token.

    Args:
        token: Token string to verify
        weak_signing: If True, expect weak signing
        skip_expiry: If True, don't check expiry (for testing)

    Returns:
        Decoded payload dictionary

    Raises:
        TokenError: If token is invalid or expired
    """
    try:
        import base64
        import json

        # Split token
        parts = token.split('.')
        if len(parts) != 2:
            raise TokenError('Invalid token format')

        payload_b64, signature = parts

        # Verify signature
        if weak_signing:
            expected_sig = hashlib.md5(payload_b64.encode()).hexdigest()
        else:
            expected_sig = hmac.new(
                SECRET_KEY.encode(),
                payload_b64.encode(),
                hashlib.sha256
            ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            raise TokenError('Invalid token signature')

        # Decode payload
        # Add padding back if needed
        padding = 4 - (len(payload_b64) % 4)
        if padding != 4:
            payload_b64 += '=' * padding

        payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode()
        payload = json.loads(payload_json)

        # Check expiry
        if not skip_expiry:
            current_time = int(time.time())
            if payload.get('exp', 0) < current_time:
                raise TokenError('Token has expired')

        return payload

    except (ValueError, KeyError, json.JSONDecodeError) as e:
        raise TokenError(f'Invalid token: {str(e)}')


def generate_refresh_token() -> str:
    """
    Generate a secure random refresh token.

    Returns:
        Random token string
    """
    return secrets.token_urlsafe(32)


def generate_api_key(
    prefix: str = API_KEY_PREFIX,
    length: int = 32
) -> str:
    """
    Generate an API key.

    Args:
        prefix: Prefix for the API key
        length: Length of the random part

    Returns:
        API key string
    """
    random_part = secrets.token_urlsafe(length)
    return f"{prefix}{random_part}"


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash a password with salt.

    Args:
        password: Plain text password
        salt: Optional salt (generated if not provided)

    Returns:
        Tuple of (hashed_password, salt)

    Note:
        This is a simplified implementation. Production code should use
        proper password hashing libraries (bcrypt, argon2, etc.)
    """
    if salt is None:
        salt = secrets.token_hex(16)

    # Use PBKDF2 for password hashing
    import hashlib
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        100000  # iterations
    )

    return hashed.hex(), salt


def verify_password(
    password: str,
    hashed_password: str,
    salt: str,
    weak_hash: bool = False
) -> bool:
    """
    Verify a password against its hash.

    Args:
        password: Plain text password to verify
        hashed_password: Stored hashed password
        salt: Salt used for hashing
        weak_hash: If True, use weak comparison (for vulnerable endpoints)

    Returns:
        True if password matches, False otherwise
    """
    if weak_hash:
        # Weak comparison for vulnerable endpoint testing
        test_hash = hashlib.md5((password + salt).encode()).hexdigest()
        return test_hash == hashed_password

    # Strong comparison
    test_hashed, _ = hash_password(password, salt)
    return hmac.compare_digest(test_hashed, hashed_password)


def extract_bearer_token(authorization_header: Optional[str]) -> Optional[str]:
    """
    Extract bearer token from Authorization header.

    Args:
        authorization_header: Value of Authorization header

    Returns:
        Token string or None if not found/invalid
    """
    if not authorization_header:
        return None

    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None

    return parts[1]


def extract_api_key(
    header_name: str = 'X-API-Key',
    query_param: str = 'api_key',
    allow_query: bool = False
) -> Optional[str]:
    """
    Extract API key from request headers or query parameters.

    Args:
        header_name: Name of the header containing API key
        query_param: Name of query parameter containing API key
        allow_query: If True, allow API key in query parameters

    Returns:
        API key string or None if not found
    """
    # Check header first (preferred method)
    api_key = request.headers.get(header_name)
    if api_key:
        return api_key

    # Check query parameter if allowed
    if allow_query:
        api_key = request.args.get(query_param)
        if api_key:
            return api_key

    return None


def require_auth(
    weak_auth: bool = False,
    allow_api_key: bool = True
):
    """
    Decorator to require authentication for an endpoint.

    Args:
        weak_auth: If True, use weak token validation
        allow_api_key: If True, accept API key authentication

    Returns:
        Decorated function

    Example:
        @app.route('/api/protected')
        @require_auth()
        def protected_endpoint():
            user_id = g.user_id  # Set by decorator
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Try bearer token authentication first
            auth_header = request.headers.get('Authorization')
            token = extract_bearer_token(auth_header)

            if token:
                try:
                    payload = verify_token(token, weak_signing=weak_auth)
                    g.user_id = payload.get('user_id')
                    g.auth_method = 'token'
                    g.token_payload = payload
                    return f(*args, **kwargs)
                except TokenError:
                    return unauthorized_response(message='Invalid or expired token')

            # Try API key authentication if allowed
            if allow_api_key:
                api_key = extract_api_key()
                if api_key:
                    # In production, verify API key against database
                    # For demo, accept keys starting with correct prefix
                    if api_key.startswith(API_KEY_PREFIX):
                        g.api_key = api_key
                        g.auth_method = 'api_key'
                        # Extract user_id from API key or lookup in DB
                        g.user_id = 'api_user'  # Placeholder
                        return f(*args, **kwargs)

            return unauthorized_response()

        return wrapper
    return decorator


def require_role(allowed_roles: list):
    """
    Decorator to require specific roles for an endpoint.

    Must be used after @require_auth decorator.

    Args:
        allowed_roles: List of allowed role names

    Returns:
        Decorated function

    Example:
        @app.route('/api/admin/users')
        @require_auth()
        @require_role(['admin', 'superuser'])
        def admin_endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not hasattr(g, 'token_payload'):
                return forbidden_response(
                    message='Authorization required'
                )

            user_role = g.token_payload.get('role')
            if user_role not in allowed_roles:
                return forbidden_response(
                    message='Insufficient permissions'
                )

            return f(*args, **kwargs)
        return wrapper
    return decorator


def create_session(
    user_id: str,
    session_data: Optional[Dict[str, Any]] = None,
    expiry_minutes: int = 30
) -> str:
    """
    Create a session and return session ID.

    Args:
        user_id: User identifier
        session_data: Optional session data
        expiry_minutes: Session expiry in minutes

    Returns:
        Session ID
    """
    session_id = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(minutes=expiry_minutes)

    # In production, store in Redis or database
    # For demo, this is a placeholder
    session = {
        'session_id': session_id,
        'user_id': user_id,
        'created_at': datetime.now().isoformat(),
        'expires_at': expires_at.isoformat(),
        'data': session_data or {}
    }

    return session_id


def validate_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Validate a session ID and return session data.

    Args:
        session_id: Session identifier

    Returns:
        Session data dictionary or None if invalid/expired
    """
    # In production, lookup in Redis or database
    # For demo, this is a placeholder
    return None


def invalidate_session(session_id: str) -> bool:
    """
    Invalidate a session.

    Args:
        session_id: Session identifier

    Returns:
        True if invalidated, False if session not found
    """
    # In production, remove from Redis or database
    # For demo, this is a placeholder
    return True


def check_rate_limit(
    user_id: str,
    endpoint: str,
    max_requests: int = 100,
    window_seconds: int = 60
) -> Tuple[bool, int]:
    """
    Check if user has exceeded rate limit for endpoint.

    Args:
        user_id: User identifier
        endpoint: Endpoint name
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds

    Returns:
        Tuple of (allowed, remaining_requests)
    """
    # In production, use Redis with sliding window
    # For demo, this is a placeholder that always allows
    return True, max_requests - 1


def generate_mfa_secret() -> str:
    """
    Generate a secret for MFA (TOTP).

    Returns:
        Base32-encoded secret string
    """
    import base64
    random_bytes = secrets.token_bytes(20)
    return base64.b32encode(random_bytes).decode('utf-8')


def verify_totp_code(
    secret: str,
    code: str,
    window: int = 1
) -> bool:
    """
    Verify a TOTP code against secret.

    Args:
        secret: Base32-encoded secret
        code: 6-digit TOTP code
        window: Number of time windows to check (±window)

    Returns:
        True if code is valid, False otherwise

    Note:
        This is a simplified implementation. Production code should use
        proper TOTP libraries (pyotp, etc.)
    """
    import base64
    import struct

    try:
        # Decode secret
        key = base64.b32decode(secret)

        # Get current time window (30 second intervals)
        current_time = int(time.time() // 30)

        # Check code against current and nearby time windows
        for offset in range(-window, window + 1):
            time_window = current_time + offset

            # Generate HOTP
            msg = struct.pack('>Q', time_window)
            digest = hmac.new(key, msg, hashlib.sha1).digest()

            # Dynamic truncation
            offset_bits = digest[-1] & 0x0F
            truncated = struct.unpack('>I', digest[offset_bits:offset_bits + 4])[0]
            truncated &= 0x7FFFFFFF
            expected_code = str(truncated % 1000000).zfill(6)

            if hmac.compare_digest(code, expected_code):
                return True

        return False

    except Exception:
        return False
