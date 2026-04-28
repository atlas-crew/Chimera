"""
Unit tests for monitoring and observability utilities.

Tests cover:
- Structured logging
- Audit event logging
- Metrics collection
"""

import pytest
import json
import logging
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from app.utils.monitoring import (
    StructuredFormatter,
    setup_logging,
    logger,
    log_audit_event,
    log_security_event,
    MetricsCollector,
    metrics,
    log_exception
)


class TestStructuredFormatter:
    """Test structured logging formatter."""

    def test_structured_formatter_basic(self):
        """Test basic structured log formatting."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data['level'] == 'INFO'
        assert log_data['message'] == 'Test message'
        assert 'timestamp' in log_data

    def test_structured_formatter_with_exception(self):
        """Test structured formatter includes exception info."""
        formatter = StructuredFormatter()

        try:
            raise ValueError('Test error')
        except ValueError:
            import sys
            exc_info = sys.exc_info()

            record = logging.LogRecord(
                name='test',
                level=logging.ERROR,
                pathname='test.py',
                lineno=1,
                msg='Error occurred',
                args=(),
                exc_info=exc_info
            )

            formatted = formatter.format(record)
            log_data = json.loads(formatted)

            assert 'exception' in log_data
            assert 'ValueError' in log_data['exception']

class TestSetupLogging:
    """Test logging setup function."""

    def test_setup_logging_creates_logger(self):
        """Test setup creates logger with correct configuration."""
        test_logger = setup_logging('test_app', log_level='DEBUG')

        assert test_logger.name == 'test_app'
        assert test_logger.level == logging.DEBUG

    def test_setup_logging_structured_formatter(self):
        """Test setup uses structured formatter."""
        test_logger = setup_logging('test_app', structured=True)

        assert len(test_logger.handlers) > 0
        handler = test_logger.handlers[0]
        assert isinstance(handler.formatter, StructuredFormatter)

    def test_setup_logging_plain_formatter(self):
        """Test setup uses plain formatter when structured=False."""
        test_logger = setup_logging('test_app', structured=False)

        handler = test_logger.handlers[0]
        assert not isinstance(handler.formatter, StructuredFormatter)


class TestAuditLogging:
    """Test audit event logging."""

    @patch('app.utils.monitoring.logger')
    def test_log_audit_event_basic(self, mock_logger):
        """Test basic audit event logging."""
        log_audit_event(
            event_type='data_access',
            user_id='user_123',
            resource='medical_record',
            resource_id='MED-001',
            action='read'
        )

        assert mock_logger.log.called
        call_args = mock_logger.log.call_args

        # Check log level and message
        assert call_args[0][0] == logging.INFO

    @patch('app.utils.monitoring.logger')
    def test_log_audit_event_with_details(self, mock_logger):
        """Test audit logging with additional details."""
        details = {'reason': 'patient_request', 'ip': '192.168.1.1'}

        log_audit_event(
            event_type='admin_action',
            user_id='admin_1',
            action='delete',
            details=details
        )

        # Check details were included
        call_args = mock_logger.log.call_args
        assert 'details' in str(call_args)

    @patch('app.utils.monitoring.logger')
    def test_log_audit_event_severity_levels(self, mock_logger):
        """Test audit logging with different severity levels."""
        for severity in ['INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            mock_logger.reset_mock()

            log_audit_event(
                event_type='test',
                severity=severity
            )

            assert mock_logger.log.called


class TestSecurityLogging:
    """Test security event logging."""

    @patch('app.utils.monitoring.logger')
    def test_log_security_event_basic(self, mock_logger):
        """Test basic security event logging."""
        log_security_event(
            event_type='failed_auth',
            description='Invalid credentials',
            severity='WARNING'
        )

        assert mock_logger.log.called

    @patch('app.utils.monitoring.logger')
    def test_log_security_event_with_details(self, mock_logger):
        """Test security logging with details."""
        details = {'username': 'admin', 'attempts': 5, 'ip': '10.0.0.1'}

        log_security_event(
            event_type='brute_force',
            description='Multiple failed attempts',
            details=details,
            severity='ERROR'
        )

        call_args = mock_logger.log.call_args
        assert 'details' in str(call_args)


class TestMetricsCollector:
    """Test metrics collection functionality."""

    def test_metrics_collector_init(self):
        """Test metrics collector initialization."""
        collector = MetricsCollector()

        assert isinstance(collector._counters, dict)
        assert isinstance(collector._gauges, dict)
        assert isinstance(collector._histograms, dict)

    def test_increment_counter(self):
        """Test incrementing counter metric."""
        collector = MetricsCollector()

        collector.increment_counter('requests', 1)
        collector.increment_counter('requests', 1)

        metrics_data = collector.get_metrics()
        assert metrics_data['counters']['requests'] == 2

    def test_increment_counter_with_tags(self):
        """Test counter with tags."""
        collector = MetricsCollector()

        collector.increment_counter('requests', 1, tags={'method': 'GET'})
        collector.increment_counter('requests', 1, tags={'method': 'POST'})

        metrics_data = collector.get_metrics()
        assert 'requests:method=GET' in metrics_data['counters']
        assert 'requests:method=POST' in metrics_data['counters']

    def test_set_gauge(self):
        """Test setting gauge metric."""
        collector = MetricsCollector()

        collector.set_gauge('memory_usage', 75.5)

        metrics_data = collector.get_metrics()
        assert metrics_data['gauges']['memory_usage'] == 75.5

    def test_set_gauge_overwrites(self):
        """Test gauge value is overwritten."""
        collector = MetricsCollector()

        collector.set_gauge('temp', 20.0)
        collector.set_gauge('temp', 25.0)

        metrics_data = collector.get_metrics()
        assert metrics_data['gauges']['temp'] == 25.0

    def test_record_histogram(self):
        """Test recording histogram values."""
        collector = MetricsCollector()

        collector.record_histogram('response_time', 100)
        collector.record_histogram('response_time', 150)
        collector.record_histogram('response_time', 200)

        metrics_data = collector.get_metrics()
        histogram = metrics_data['histograms']['response_time']

        assert histogram['count'] == 3
        assert histogram['min'] == 100
        assert histogram['max'] == 200
        assert histogram['avg'] == 150

    def test_get_metrics_all_types(self):
        """Test get_metrics returns all metric types."""
        collector = MetricsCollector()

        collector.increment_counter('counter_metric', 5)
        collector.set_gauge('gauge_metric', 42.0)
        collector.record_histogram('histogram_metric', 10)

        metrics_data = collector.get_metrics()

        assert 'counters' in metrics_data
        assert 'gauges' in metrics_data
        assert 'histograms' in metrics_data

    def test_reset_metrics(self):
        """Test resetting all metrics."""
        collector = MetricsCollector()

        collector.increment_counter('counter', 10)
        collector.set_gauge('gauge', 50.0)
        collector.record_histogram('histogram', 100)

        collector.reset()

        metrics_data = collector.get_metrics()
        assert len(metrics_data['counters']) == 0
        assert len(metrics_data['gauges']) == 0
        assert len(metrics_data['histograms']) == 0

    def test_metrics_build_key_with_tags(self):
        """Test metric key building with tags."""
        key = MetricsCollector._build_key('metric', {'tag1': 'val1', 'tag2': 'val2'})

        assert key == 'metric:tag1=val1,tag2=val2'

    def test_metrics_build_key_without_tags(self):
        """Test metric key building without tags."""
        key = MetricsCollector._build_key('metric', None)

        assert key == 'metric'


class TestLogException:
    """Test exception logging function."""

    @patch('app.utils.monitoring.logger')
    def test_log_exception_basic(self, mock_logger):
        """Test basic exception logging."""
        try:
            raise ValueError('Test error')
        except ValueError as e:
            log_exception(e)

        assert mock_logger.error.called

    @patch('app.utils.monitoring.logger')
    def test_log_exception_with_context(self, mock_logger):
        """Test exception logging with context."""
        context = {'user_id': 'user_123', 'action': 'test'}

        try:
            raise RuntimeError('Test error')
        except RuntimeError as e:
            log_exception(e, context=context)

        call_args = mock_logger.error.call_args
        assert 'context' in str(call_args)

    @patch('app.utils.monitoring.logger')
    def test_log_exception_http_exception(self, mock_logger):
        """Test logging HTTP exceptions."""
        from werkzeug.exceptions import NotFound

        try:
            raise NotFound('Resource not found')
        except NotFound as e:
            log_exception(e)

        # HTTP exceptions should be logged as warning
        assert mock_logger.warning.called


class TestGlobalMetricsInstance:
    """Test global metrics collector instance."""

    def test_global_metrics_instance_exists(self):
        """Test global metrics instance is available."""
        assert metrics is not None
        assert isinstance(metrics, MetricsCollector)

    def test_global_metrics_can_record(self):
        """Test global metrics instance can record metrics."""
        metrics.reset()

        metrics.increment_counter('test_counter', 1)
        data = metrics.get_metrics()

        assert 'test_counter' in data['counters']
