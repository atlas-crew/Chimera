"""
Security module for  WAF Demo API
Provides DEMO_MODE gating for dangerous endpoints
"""

import os
from functools import wraps
from flask import jsonify, request
import logging

logger = logging.getLogger(__name__)

# Get DEMO_MODE from environment (default to strict for safety)
DEMO_MODE = os.getenv('DEMO_MODE', 'strict').lower()

# Validate DEMO_MODE
if DEMO_MODE not in ['strict', 'full']:
    logger.warning(f"Invalid DEMO_MODE '{DEMO_MODE}', defaulting to 'strict'")
    DEMO_MODE = 'strict'

logger.info(f"Application started in DEMO_MODE={DEMO_MODE}")


def require_full_demo(f):
    """
    Decorator to restrict dangerous endpoints to DEMO_MODE=full only.

    Usage:
        @app.route('/api/apt/backdoor')
        @require_full_demo
        def dangerous_endpoint():
            return jsonify({"status": "dangerous"})

    In DEMO_MODE=strict, returns 403 Forbidden.
    In DEMO_MODE=full, allows the request through.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if DEMO_MODE != 'full':
            logger.warning(
                f"Blocked access to {request.path} - requires DEMO_MODE=full "
                f"(current mode: {DEMO_MODE})"
            )
            return jsonify({
                'error': 'Forbidden',
                'message': 'This endpoint requires DEMO_MODE=full',
                'endpoint': request.path,
                'current_mode': DEMO_MODE,
                'documentation': 'See deploy/SECURITY.md for DEMO_MODE configuration'
            }), 403

        # Log access to dangerous endpoint
        logger.warning(
            f"SECURITY: Access to dangerous endpoint {request.path} "
            f"allowed in DEMO_MODE=full from {request.remote_addr}"
        )

        return f(*args, **kwargs)

    return decorated_function


def is_full_mode():
    """Check if application is running in full demo mode"""
    return DEMO_MODE == 'full'


def get_demo_mode():
    """Get current DEMO_MODE setting"""
    return DEMO_MODE


# Endpoint categories that should be restricted
DANGEROUS_ENDPOINT_PATTERNS = [
    # Advanced Persistent Threat simulation
    '/api/apt/',
    '/api/c2/',
    '/api/malware/',

    # Industrial Control Systems
    '/api/ics/',
    '/api/scada/',
    '/api/modbus/',

    # Credential harvesting
    '/api/admin/credentials/',
    '/api/internal/passwords/',
    '/api/secrets/',

    # Data exfiltration
    '/api/exfil/',
    '/api/dump/',
    '/api/export/all',

    # Cloud exploitation
    '/api/cloud/metadata/',
    '/api/aws/credentials/',
    '/api/azure/tokens/',

    # Backdoors and reverse shells
    '/api/backdoor/',
    '/api/shell/',
    '/api/reverse/',

    # Ransomware simulation
    '/api/ransomware/',
    '/api/crypto/',

    # Supply chain attacks
    '/api/vendor/compromise/',
    '/api/supply-chain/',
]


def is_dangerous_endpoint(path):
    """
    Check if an endpoint path is considered dangerous.

    Args:
        path: Request path to check

    Returns:
        True if endpoint matches dangerous patterns, False otherwise
    """
    for pattern in DANGEROUS_ENDPOINT_PATTERNS:
        if path.startswith(pattern):
            return True
    return False


# Security headers middleware
def add_security_headers(response):
    """
    Add security headers to all responses.
    Should be registered with @app.after_request
    """
    # Existing CSP is maintained from app.py

    # Add additional security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Add DEMO_MODE indicator header (for testing/debugging)
    response.headers['X-Demo-Mode'] = DEMO_MODE

    return response
