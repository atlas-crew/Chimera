import json
import os
import time
from datetime import datetime
from flask import request, g

class TrafficRecorder:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.log_file = os.environ.get('TRAFFIC_LOG_FILE', 'traffic_log.json')
        self.enabled = os.environ.get('RECORD_TRAFFIC', 'false').lower() == 'true'
        
        if self.enabled:
            print(f"Traffic recording enabled. Logs will be saved to {self.log_file}")
            # Ensure log file exists or create empty array
            if not os.path.exists(self.log_file):
                with open(self.log_file, 'w') as f:
                    json.dump([], f)

            app.before_request(self.before_request)
            app.after_request(self.after_request)

    def before_request(self):
        g.start_time = time.time()

    def after_request(self, response):
        if not self.enabled:
            return response

        # Skip recording for static assets, swagger, and health checks
        if any(p in request.path for p in ['.css', '.js', '.png', '.ico', '/swagger', '/healthz', '/openapi.yaml']):
            return response

        duration = time.time() - g.start_time
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.args),
            'headers': dict(request.headers),
            'status_code': response.status_code,
            'duration_ms': round(duration * 1000, 2),
            # Capture body only for small requests to avoid bloat
            'body': request.get_json(silent=True) if request.is_json else None
        }

        try:
            # Append to log file (inefficient for high volume, but fine for demo recording)
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

        return response
