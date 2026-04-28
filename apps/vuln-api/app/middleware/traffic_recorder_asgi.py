"""
Starlette/ASGI counterpart to app.middleware.traffic_recorder.TrafficRecorder.

Writes the same JSON log schema as the Flask version so the recorder blueprint
(app.blueprints.recorder) can read entries written by either side during the
transitional compat-bridge phase. The Flask version stays wired in the WSGI
factory; this middleware records traffic served natively through app.asgi:app
once gunicorn flips to uvicorn at task-16.8 cutover.
"""

import json
import os
import time
from datetime import datetime
from urllib.parse import parse_qs


_SKIP_TOKENS = ('.css', '.js', '.png', '.ico', '/swagger', '/healthz', '/openapi.yaml')


class TrafficRecorderMiddleware:
    """ASGI middleware that records request/response metadata to a JSON log.

    Activates only when RECORD_TRAFFIC=true. Captures request body bytes by
    wrapping the receive callable, and the response status by wrapping send.
    """

    def __init__(self, app):
        self.app = app
        self.log_file = os.environ.get('TRAFFIC_LOG_FILE', 'traffic_log.json')
        self.enabled = os.environ.get('RECORD_TRAFFIC', 'false').lower() == 'true'

        if self.enabled:
            print(f"Traffic recording enabled (ASGI). Logs will be saved to {self.log_file}")
            if not os.path.exists(self.log_file):
                with open(self.log_file, 'w') as f:
                    json.dump([], f)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or not self.enabled:
            await self.app(scope, receive, send)
            return

        path = scope.get('path', '')
        if any(token in path for token in _SKIP_TOKENS):
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        body_chunks: list[bytes] = []

        async def wrapped_receive():
            message = await receive()
            if message['type'] == 'http.request':
                body_chunks.append(message.get('body', b''))
            return message

        status = {'code': 200}

        async def wrapped_send(message):
            if message['type'] == 'http.response.start':
                status['code'] = message['status']
            await send(message)

        await self.app(scope, wrapped_receive, wrapped_send)

        duration = time.time() - start_time

        headers = {
            k.decode('latin-1'): v.decode('latin-1')
            for k, v in scope.get('headers', [])
        }
        query_string = scope.get('query_string', b'').decode('latin-1')
        # Match Flask's dict(request.args) shape: last value wins for repeated keys.
        query_params = {k: v[-1] for k, v in parse_qs(query_string).items()}

        body_json = None
        if 'application/json' in headers.get('content-type', ''):
            body_bytes = b''.join(body_chunks)
            if body_bytes:
                try:
                    body_json = json.loads(body_bytes)
                except (json.JSONDecodeError, ValueError):
                    body_json = None

        entry = {
            'timestamp': datetime.now().isoformat(),
            'method': scope.get('method', ''),
            'path': path,
            'query_params': query_params,
            'headers': headers,
            'status_code': status['code'],
            'duration_ms': round(duration * 1000, 2),
            'body': body_json,
        }

        try:
            with open(self.log_file, 'r+') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
                data.append(entry)
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
        except Exception as e:
            print(f"Failed to log traffic: {e}")
