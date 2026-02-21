"""
Monitoring and observability utilities.

Provides structured logging, request tracing, metrics collection,
and audit event logging for the demo application.
"""

import logging
import time
import json
from datetime import datetime
from typing import Any, Dict, Optional, Callable
from functools import wraps
from flask import request, g, has_request_context
from werkzeug.exceptions import HTTPException


# Configure structured logging
class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in structured JSON format.

    This makes logs easier to parse and analyze with log aggregation tools.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add request context if available
        if has_request_context():
            log_data['request'] = {
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr
            }

            # Add request ID if set
            if hasattr(g, 'request_id'):
                log_data['request_id'] = g.request_id

        # Add any extra fields from record
        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        return json.dumps(log_data)


def setup_logging(
    app_name: str = 'api-demo',
    log_level: str = 'INFO',
    structured: bool = True
) -> logging.Logger:
    """
    Setup application logging with structured output.

    Args:
        app_name: Application name for logger
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: If True, use structured JSON logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler()

    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Global logger instance
logger = setup_logging()


def log_request(
    include_headers: bool = False,
    include_body: bool = False,
    max_body_size: int = 1024
):
    """
    Decorator to log HTTP requests and responses.

    Args:
        include_headers: If True, log request headers
        include_body: If True, log request body
        max_body_size: Maximum body size to log (bytes)

    Returns:
        Decorated function

    Example:
        @app.route('/api/users')
        @log_request(include_body=True)
        def list_users():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Log request
            log_data = {
                'event': 'request_started',
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.user_agent.string if request.user_agent else None
            }

            if include_headers:
                log_data['headers'] = dict(request.headers)

            if include_body and request.data:
                body_size = len(request.data)
                if body_size <= max_body_size:
                    try:
                        if request.is_json:
                            log_data['body'] = request.get_json()
                        else:
                            log_data['body'] = request.data.decode('utf-8', errors='ignore')
                    except Exception:
                        log_data['body'] = '<unable to decode>'
                else:
                    log_data['body'] = f'<body too large: {body_size} bytes>'

            logger.info('Request', extra=log_data)

            # Execute endpoint
            try:
                response = f(*args, **kwargs)
                duration = time.time() - start_time

                # Log response
                status_code = 200
                if isinstance(response, tuple):
                    status_code = response[1] if len(response) > 1 else 200

                logger.info('Request completed', extra={
                    'event': 'request_completed',
                    'method': request.method,
                    'path': request.path,
                    'status_code': status_code,
                    'duration_ms': round(duration * 1000, 2)
                })

                return response

            except Exception as e:
                duration = time.time() - start_time

                # Log error
                logger.error('Request failed', extra={
                    'event': 'request_failed',
                    'method': request.method,
                    'path': request.path,
                    'error': str(e),
                    'duration_ms': round(duration * 1000, 2)
                }, exc_info=True)

                raise

        return wrapper
    return decorator


def track_performance(operation_name: Optional[str] = None):
    """
    Decorator to track performance metrics for operations.

    Args:
        operation_name: Name of the operation (defaults to function name)

    Returns:
        Decorated function

    Example:
        @track_performance('database_query')
        def get_users():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f.__name__
            start_time = time.time()

            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time

                logger.info('Performance metric', extra={
                    'event': 'performance_metric',
                    'operation': op_name,
                    'duration_ms': round(duration * 1000, 2),
                    'success': True
                })

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger.error('Performance metric', extra={
                    'event': 'performance_metric',
                    'operation': op_name,
                    'duration_ms': round(duration * 1000, 2),
                    'success': False,
                    'error': str(e)
                })

                raise

        return wrapper
    return decorator


def log_audit_event(
    event_type: str,
    user_id: Optional[str] = None,
    resource: Optional[str] = None,
    resource_id: Optional[str] = None,
    action: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    severity: str = 'INFO'
):
    """
    Log an audit event for security and compliance tracking.

    Args:
        event_type: Type of audit event (e.g., 'auth', 'data_access', 'admin')
        user_id: ID of user performing action
        resource: Type of resource affected
        resource_id: ID of specific resource
        action: Action performed (e.g., 'create', 'read', 'update', 'delete')
        details: Additional event details
        severity: Event severity (INFO, WARNING, ERROR, CRITICAL)

    Example:
        log_audit_event(
            event_type='data_access',
            user_id='user_123',
            resource='medical_record',
            resource_id='MED-001',
            action='read',
            details={'reason': 'patient_request'}
        )
    """
    audit_data = {
        'event': 'audit_event',
        'event_type': event_type,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'user_id': user_id,
        'resource': resource,
        'resource_id': resource_id,
        'action': action
    }

    if details:
        audit_data['details'] = details

    # Add request context if available
    if has_request_context():
        audit_data['request'] = {
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr,
            'user_agent': request.user_agent.string if request.user_agent else None
        }

        if hasattr(g, 'request_id'):
            audit_data['request_id'] = g.request_id

    # Log at appropriate level
    log_level = getattr(logging, severity.upper(), logging.INFO)
    logger.log(log_level, f"Audit: {event_type}", extra=audit_data)


def log_security_event(
    event_type: str,
    severity: str = 'WARNING',
    description: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """
    Log a security-related event.

    Args:
        event_type: Type of security event (e.g., 'failed_auth', 'rate_limit', 'suspicious_activity')
        severity: Event severity (WARNING, ERROR, CRITICAL)
        description: Human-readable description
        details: Additional event details

    Example:
        log_security_event(
            event_type='failed_auth',
            severity='WARNING',
            description='Multiple failed login attempts',
            details={'username': 'admin', 'attempts': 5}
        )
    """
    security_data = {
        'event': 'security_event',
        'event_type': event_type,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'description': description
    }

    if details:
        security_data['details'] = details

    # Add request context
    if has_request_context():
        security_data['request'] = {
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr,
            'headers': {
                'user_agent': request.user_agent.string if request.user_agent else None,
                'referer': request.referrer
            }
        }

    log_level = getattr(logging, severity.upper(), logging.WARNING)
    logger.log(log_level, f"Security: {event_type}", extra=security_data)


class MetricsCollector:
    """
    Simple metrics collector for tracking application metrics.

    In production, this would integrate with Prometheus, StatsD, etc.
    """

    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = {}

    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Amount to increment
            tags: Optional metric tags
        """
        key = self._build_key(name, tags)
        self._counters[key] = self._counters.get(key, 0) + value

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Set a gauge metric.

        Args:
            name: Metric name
            value: Metric value
            tags: Optional metric tags
        """
        key = self._build_key(name, tags)
        self._gauges[key] = value

    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a histogram value.

        Args:
            name: Metric name
            value: Value to record
            tags: Optional metric tags
        """
        key = self._build_key(name, tags)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot.

        Returns:
            Dictionary of all metrics
        """
        return {
            'counters': dict(self._counters),
            'gauges': dict(self._gauges),
            'histograms': {
                k: {
                    'count': len(v),
                    'min': min(v) if v else 0,
                    'max': max(v) if v else 0,
                    'avg': sum(v) / len(v) if v else 0
                }
                for k, v in self._histograms.items()
            }
        }

    def reset(self):
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()

    @staticmethod
    def _build_key(name: str, tags: Optional[Dict[str, str]]) -> str:
        """Build metric key with tags."""
        if not tags:
            return name
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}:{tag_str}"


# Global metrics collector instance
metrics = MetricsCollector()


def generate_request_id() -> str:
    """
    Generate a unique request ID for tracing.

    Returns:
        Request ID string
    """
    import uuid
    return str(uuid.uuid4())


def request_id_middleware(app):
    """
    Middleware to add request IDs to all requests.

    Args:
        app: Flask application instance

    Example:
        from app.utils.monitoring import request_id_middleware
        request_id_middleware(app)
    """
    @app.before_request
    def before_request():
        """Generate and store request ID."""
        g.request_id = request.headers.get('X-Request-ID', generate_request_id())

    @app.after_request
    def after_request(response):
        """Add request ID to response headers."""
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        return response


def log_exception(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None
):
    """
    Log an exception with context.

    Args:
        exception: Exception to log
        context: Additional context information
    """
    error_data = {
        'event': 'exception',
        'exception_type': type(exception).__name__,
        'exception_message': str(exception)
    }

    if context:
        error_data['context'] = context

    if isinstance(exception, HTTPException):
        error_data['status_code'] = exception.code
        logger.warning('HTTP exception', extra=error_data)
    else:
        logger.error('Exception occurred', extra=error_data, exc_info=True)
