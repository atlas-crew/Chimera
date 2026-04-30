"""
Utility functions for the demo application.
"""

from .demo_data import (
    init_demo_data,
    reset_demo_data,
    get_demo_user,
    get_demo_customer,
    seed_additional_users,
    seed_additional_products,
    seed_transactions,
    get_seed_statistics,
    create_predictable_test_data,
    export_demo_data,
    import_demo_data
)
from .templates import DEMO_PAGE_TEMPLATE
# validators.py and responses.py were Flask-only helpers, deleted in
# task-16.8 once no migrated routes referenced them. The corresponding
# `__all__` entries below have also been removed.
from .auth_helpers import (
    TokenError,
    generate_token,
    verify_token,
    generate_refresh_token,
    generate_api_key,
    hash_password,
    verify_password,
    extract_bearer_token,
    create_session,
    validate_session,
    invalidate_session,
    check_rate_limit,
    generate_mfa_secret,
    verify_totp_code
)
from .monitoring import (
    setup_logging,
    logger,
    log_audit_event,
    log_security_event,
    log_exception,
    metrics,
    MetricsCollector,
)

__all__ = [
    # Demo data
    'init_demo_data',
    'reset_demo_data',
    'get_demo_user',
    'get_demo_customer',
    'seed_additional_users',
    'seed_additional_products',
    'seed_transactions',
    'get_seed_statistics',
    'create_predictable_test_data',
    'export_demo_data',
    'import_demo_data',
    # Templates
    'DEMO_PAGE_TEMPLATE',
    # Auth helpers
    'TokenError',
    'generate_token',
    'verify_token',
    'generate_refresh_token',
    'generate_api_key',
    'hash_password',
    'verify_password',
    'extract_bearer_token',
    'create_session',
    'validate_session',
    'invalidate_session',
    'check_rate_limit',
    'generate_mfa_secret',
    'verify_totp_code',
    # Monitoring
    'setup_logging',
    'logger',
    'log_audit_event',
    'log_security_event',
    'log_exception',
    'metrics',
    'MetricsCollector',
]
