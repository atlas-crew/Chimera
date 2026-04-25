"""
Framework-agnostic application configuration.

Replaces current_app.config / current_app.secret_key usage so that
route handlers, services, and utilities work identically under Flask
and Starlette.
"""

import logging
import os

logger = logging.getLogger('chimera')


class AppConfig:
    """Central configuration object populated once at startup."""

    def __init__(self, overrides: dict | None = None):
        overrides = overrides or {}

        self.secret_key: str = overrides.get(
            'SECRET_KEY',
            'chimera-demo-key-not-for-production',
        )
        self.debug: bool = overrides.get(
            'DEBUG',
            os.environ.get('FLASK_ENV', '').lower() == 'development'
            or os.environ.get('DEBUG', '').lower() in ('1', 'true', 'yes'),
        )
        self.testing: bool = overrides.get('TESTING', False)
        self.demo_mode: str = os.environ.get('DEMO_MODE', 'full').lower()

        # Apparatus integration
        self.apparatus_enabled: bool = _bool_env('APPARATUS_ENABLED')
        self.apparatus_base_url: str = os.environ.get('APPARATUS_BASE_URL', '').strip().rstrip('/')
        self.apparatus_timeout_ms: int = _int_env('APPARATUS_TIMEOUT_MS', 5000)

        # Throughput mode
        self.throughput_mode: bool = _bool_env('DEMO_THROUGHPUT_MODE')
        self.throughput_payload_bytes: int = _int_env('DEMO_THROUGHPUT_PAYLOAD_BYTES', 2 * 1024)
        self.throughput_max_bytes: int = _int_env('DEMO_THROUGHPUT_MAX_BYTES', 1024 * 1024)

        # Database
        self.use_database: bool = _bool_env('USE_DATABASE')

    # --- dict-like access for backward compatibility with Flask config ---

    def get(self, key: str, default=None):
        """Support config.get('KEY', default) pattern."""
        # Map Flask config keys to our attributes
        attr = _CONFIG_KEY_MAP.get(key)
        if attr is not None:
            return getattr(self, attr)
        return default

    def items(self):
        """Support config.items() for the leak_config endpoint."""
        return {k: getattr(self, k) for k in vars(self) if not k.startswith('_')}.items()

    def __getitem__(self, key: str):
        attr = _CONFIG_KEY_MAP.get(key)
        if attr is not None:
            return getattr(self, attr)
        raise KeyError(key)

    def __contains__(self, key: str):
        return key in _CONFIG_KEY_MAP


# Map from Flask-style config keys to our attribute names
_CONFIG_KEY_MAP = {
    'SECRET_KEY': 'secret_key',
    'DEBUG': 'debug',
    'TESTING': 'testing',
    'DEMO_MODE': 'demo_mode',
    'APPARATUS_ENABLED': 'apparatus_enabled',
    'APPARATUS_BASE_URL': 'apparatus_base_url',
    'APPARATUS_TIMEOUT_MS': 'apparatus_timeout_ms',
    'DEMO_THROUGHPUT_MODE': 'throughput_mode',
    'DEMO_THROUGHPUT_PAYLOAD_BYTES': 'throughput_payload_bytes',
    'DEMO_THROUGHPUT_MAX_BYTES': 'throughput_max_bytes',
    'USE_DATABASE': 'use_database',
}


def _bool_env(key: str) -> bool:
    return os.environ.get(key, '').lower() in ('true', '1', 'yes')


def _int_env(key: str, default: int = 0) -> int:
    try:
        return int(os.environ.get(key, ''))
    except (TypeError, ValueError):
        return default


# Module-level singleton — initialized at import time.
# Override values by calling init_config() before the app starts handling
# requests (e.g. in create_app).
app_config = AppConfig()


def init_config(overrides: dict | None = None) -> AppConfig:
    """Re-initialize the global config singleton with optional overrides.

    Mutates the existing `app_config` instance in place so that modules that
    did `from app.config import app_config` continue to see the updated
    values — otherwise those modules would hold a reference to the pre-init
    instance and silently diverge from callers that re-import.
    """
    fresh = AppConfig(overrides)
    app_config.__dict__.update(fresh.__dict__)
    return app_config
