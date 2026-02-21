"""
Gunicorn configuration for  WAF Demo API
Optimized for async workloads with JSON structured logging
"""
import os
import json
import logging
from datetime import datetime

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8880')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', '4'))
worker_class = 'gevent'
worker_connections = 1000  # Each worker can handle 1000 concurrent connections
timeout = 30
keepalive = 2

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Logging
accesslog = '-'  # stdout
errorlog = '-'   # stderr
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Server mechanics
daemon = False
pidfile = None
umask = 0o077
tmp_upload_dir = None

# Server hooks
def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def pre_fork(server, worker):
    """Called just prior to forking a worker."""
    pass

def pre_exec(server):
    """Called just prior to forking the master process."""
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info(f"Server is ready. Spawning {workers} workers")

def worker_int(worker):
    """Called when worker receives INT or QUIT signal."""
    worker.log.info(f"Worker received INT or QUIT signal (pid: {worker.pid})")

def worker_abort(worker):
    """Called when worker receives SIGABRT signal."""
    worker.log.info(f"Worker received SIGABRT signal (pid: {worker.pid})")


# Custom JSON access log formatter
class JSONAccessLogFormatter(logging.Formatter):
    """Format access logs as JSON for structured logging in Loki"""

    def format(self, record):
        # Parse Gunicorn's access log
        parts = record.getMessage().split('"')

        if len(parts) >= 3:
            # Extract request line
            request_parts = parts[1].split() if len(parts) > 1 else ['', '', '']
            method = request_parts[0] if len(request_parts) > 0 else ''
            path = request_parts[1] if len(request_parts) > 1 else ''

            # Extract status and size from the part after request
            after_request = parts[2].strip().split() if len(parts) > 2 else ['', '']
            status = after_request[0] if len(after_request) > 0 else ''

            # Extract user agent
            user_agent = parts[3] if len(parts) > 3 else ''

            # Extract latency (microseconds at end)
            latency_us = parts[-1].strip().split()[-1] if len(parts) > 4 else '0'
            try:
                latency_ms = float(latency_us) / 1000
            except:
                latency_ms = 0

            # Build JSON log entry
            log_entry = {
                'ts': datetime.utcnow().isoformat() + 'Z',
                'level': 'info',
                'logger': 'gunicorn.access',
                'method': method,
                'path': path,
                'status': int(status) if status.isdigit() else 0,
                'latency_ms': round(latency_ms, 2),
                'user_agent': user_agent,
                'message': f'{method} {path} {status}'
            }

            return json.dumps(log_entry)

        # Fallback for malformed logs
        return json.dumps({
            'ts': datetime.utcnow().isoformat() + 'Z',
            'level': 'info',
            'logger': 'gunicorn.access',
            'message': record.getMessage()
        })


# Configure JSON logging
def on_starting(server):
    """Configure JSON logging when Gunicorn starts"""
    # Get access log handler
    for handler in server.log.access_log.handlers:
        handler.setFormatter(JSONAccessLogFormatter())

    # Configure error log for JSON
    error_formatter = logging.Formatter(
        '{"ts":"%(asctime)s","level":"%(levelname)s","logger":"gunicorn.error","message":"%(message)s"}',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    for handler in server.log.error_log.handlers:
        handler.setFormatter(error_formatter)
