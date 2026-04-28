"""
Monitoring and observability utilities.

Provides structured logging, request tracing, metrics collection,
and audit event logging for the demo application.
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional


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

        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

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

    status_code = getattr(exception, 'status_code', None) or getattr(exception, 'code', None)
    if status_code is not None:
        error_data['status_code'] = status_code
        logger.warning('HTTP exception', extra=error_data)
    else:
        logger.error('Exception occurred', extra=error_data, exc_info=True)
