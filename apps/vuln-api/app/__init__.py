"""
Application factory for the  WAF Demo Site.
"""

import os
from flask import Flask, Response, jsonify, request, send_from_directory

from app.throughput import (
    bool_env,
    int_env,
    throughput_payload_bytes,
    build_payload_cache
)


def create_app(config=None):
    """
    Application factory pattern for creating Flask app instances.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__, static_folder='../static')

    # Basic configuration
    app.secret_key = config.get('SECRET_KEY', 'chimera-demo-key-not-for-production') if config else 'chimera-demo-key-not-for-production'

    # Initialize Swagger (legacy flasgger setup retained for backward compatibility)
    from flasgger import Swagger
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": " Demo API",
            "description": "API Documentation for  WAF TestBed. <br><br><b>Note:</b> This API contains intentional vulnerabilities for educational and testing purposes.",
            "version": "1.0.0"
        },
        "schemes": [
            "http",
            "https"
        ],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\""
            }
        }
    }
    Swagger(app, template=swagger_template)

    # Enable debug mode for demo environment to ensure verbose error responses
    demo_mode = os.environ.get('DEMO_MODE', 'true').lower() == 'true'
    if demo_mode:
        app.config['DEBUG'] = True
        app.config['ENV'] = 'development'
        app.config['DEMO_MODE'] = True

    # Initialize database if USE_DATABASE=true
    use_database = os.environ.get('USE_DATABASE', 'false').lower() == 'true'
    if use_database:
        from app.database import init_database
        db_initialized = init_database(app)
        if db_initialized:
            print("✓ Database mode enabled (SQLite)")
        else:
            print("✗ Database initialization failed")
    else:
        print("✓ In-memory mode (no database)")

    throughput_mode = bool_env('DEMO_THROUGHPUT_MODE')
    if throughput_mode:
        payload_bytes = throughput_payload_bytes()
        payload_cache = build_payload_cache(payload_bytes)
        payload = payload_cache[payload_bytes]
        payload_size = len(payload)
        max_payload_bytes = int_env('DEMO_THROUGHPUT_MAX_BYTES') or (1024 * 1024)
        throughput_only_fast = bool_env('DEMO_THROUGHPUT_ONLY_FAST')
        match_paths = [p.strip() for p in os.environ.get('DEMO_THROUGHPUT_PATHS', '').split(',') if p.strip()]
        exclude_paths = [p.strip() for p in os.environ.get('DEMO_THROUGHPUT_EXCLUDE_PATHS', '').split(',') if p.strip()]

        app.config['DEMO_THROUGHPUT_MODE'] = True
        app.config['DEMO_THROUGHPUT_PAYLOAD'] = payload
        app.config['DEMO_THROUGHPUT_PAYLOAD_BYTES'] = payload_size
        app.config['DEMO_THROUGHPUT_PAYLOAD_CACHE'] = payload_cache
        app.config['DEMO_THROUGHPUT_MAX_BYTES'] = max_payload_bytes
        app.config['DEMO_THROUGHPUT_ONLY_FAST'] = throughput_only_fast
        app.config['DEMO_THROUGHPUT_PATHS'] = match_paths
        app.config['DEMO_THROUGHPUT_EXCLUDE_PATHS'] = exclude_paths

        @app.before_request
        def short_circuit_exports():
            if throughput_only_fast:
                return None
            if request.method not in {'GET', 'POST'}:
                return None
            path = request.path or ''
            if exclude_paths and any(token in path for token in exclude_paths):
                return None
            if match_paths:
                if not any(token in path for token in match_paths):
                    return None
            elif 'export' not in path:
                return None

            response = Response(payload, mimetype='application/json')
            response.headers['X-Demo-Throughput'] = 'true'
            response.headers['X-Demo-Throughput-Bytes'] = str(payload_size)
            return response

    # Register Security Headers (CSP + CORS)
    @app.after_request
    def add_security_headers(response):
        """Set Content-Security-Policy and CORS headers for all responses"""
        # CORS Headers - Intentionally permissive for demo
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'

        if request.path in {'/swagger', '/openapi.yaml'}:
            response.headers['Content-Security-Policy'] = (
                "default-src 'self' https://unpkg.com; "
                "style-src 'self' https://unpkg.com 'unsafe-inline'; "
                "script-src 'self' https://unpkg.com 'unsafe-inline'; "
                "img-src 'self' data: https://unpkg.com; "
                "font-src 'self' https://unpkg.com; "
                "connect-src 'self'"
            )
            return response

        # SPA routes need relaxed CSP for Tailwind/Vite inline styles
        if not request.path.startswith(('/api/', '/apidocs', '/flasgger_static', '/apispec')):
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "script-src 'self'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'"
            )
        else:
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "style-src 'self'; "
                "script-src 'self'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'"
            )
        return response

    # Register error handlers BEFORE blueprints to ensure they catch all errors
    from app.error_handlers import register_error_handlers
    register_error_handlers(app)

    # Import and register blueprints
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.banking import banking_bp
    from app.blueprints.mobile import mobile_bp
    from app.blueprints.healthcare import healthcare_bp
    from app.blueprints.compliance import compliance_bp
    from app.blueprints.ecommerce import ecommerce_bp
    from app.blueprints.checkout import checkout_bp
    from app.blueprints.payments import payments_bp
    from app.blueprints.loyalty import loyalty_bp
    from app.blueprints.insurance import insurance_bp
    from app.blueprints.infrastructure import infrastructure_bp
    from app.blueprints.attack_sim import attack_sim_bp
    from app.blueprints.ics_ot import ics_ot_bp
    from app.blueprints.security_ops import security_ops_bp
    from app.blueprints.integrations import integrations_bp
    from app.blueprints.government import government_bp
    from app.blueprints.saas import saas_bp
    from app.blueprints.telecom import telecom_bp
    from app.blueprints.energy_utilities import energy_utilities_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.testing import testing_bp
    from app.blueprints.throughput import throughput_bp
    from app.blueprints.genai import genai_bp
    from app.blueprints.diagnostics import diagnostics_bp
    from app.blueprints.recorder import recorder_bp
    from app.middleware.traffic_recorder import TrafficRecorder

    # Initialize Traffic Recorder
    TrafficRecorder(app)

    # Register all blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(banking_bp)
    app.register_blueprint(mobile_bp)
    app.register_blueprint(healthcare_bp)
    app.register_blueprint(compliance_bp)
    app.register_blueprint(ecommerce_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(loyalty_bp)
    app.register_blueprint(insurance_bp)
    app.register_blueprint(infrastructure_bp)
    app.register_blueprint(attack_sim_bp)
    app.register_blueprint(ics_ot_bp)
    app.register_blueprint(security_ops_bp)
    app.register_blueprint(integrations_bp)
    app.register_blueprint(government_bp)
    app.register_blueprint(saas_bp)
    app.register_blueprint(telecom_bp)
    app.register_blueprint(energy_utilities_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(testing_bp)
    app.register_blueprint(throughput_bp)
    app.register_blueprint(genai_bp)
    app.register_blueprint(diagnostics_bp)
    app.register_blueprint(recorder_bp)

    # Register database vulnerable endpoints (if database mode enabled)
    if use_database:
        from app.blueprints.database_vulnerable import db_vuln_bp
        app.register_blueprint(db_vuln_bp)
        print("✓ SQL injection test endpoints enabled")

    # Static OpenAPI spec + Swagger UI
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs'))

    @app.get('/openapi.yaml')
    def openapi_spec():
        return send_from_directory(docs_dir, 'openapi.yaml')

    @app.get('/swagger')
    def swagger_ui():
        html = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title> TestBed Swagger UI</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    <style>
      body { margin: 0; background: #0f172a; }
      #swagger-ui { padding: 12px 24px; }
    </style>
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.onload = function () {
        SwaggerUIBundle({
          url: '/openapi.yaml',
          dom_id: '#swagger-ui',
          deepLinking: true,
          presets: [SwaggerUIBundle.presets.apis],
          layout: 'BaseLayout'
        });
      };
    </script>
  </body>
</html>
"""
        return Response(html, mimetype='text/html')

    # Initialize demo data
    with app.app_context():
        from app.utils import init_demo_data
        init_demo_data()

    # --- SPA serving: bundle the React frontend into Flask ---
    web_dist_dir = os.path.join(os.path.dirname(__file__), 'web_dist')
    spa_index = os.path.join(web_dist_dir, 'index.html')
    _API_PREFIXES = ('api/', 'apidocs', 'flasgger_static', 'apispec')

    if os.path.isfile(spa_index):
        print("✓ SPA mode — serving web portal from app/web_dist/")

        # Replace the main blueprint's / handler instead of adding a
        # duplicate URL rule (blueprint routes match before app routes).
        def _serve_spa_index():
            return send_from_directory(web_dist_dir, 'index.html')

        app.view_functions['main.home'] = _serve_spa_index

        @app.route('/<path:path>')
        def spa_catch_all(path):
            # Let API and Swagger routes return 404 so error handlers work
            if path.startswith(_API_PREFIXES):
                return jsonify({"error": "Not found"}), 404

            # Serve actual static files (JS, CSS, images, etc.)
            static_path = os.path.join(web_dist_dir, path)
            if os.path.isfile(static_path):
                return send_from_directory(web_dist_dir, path)

            # Everything else → index.html (React Router handles it)
            return send_from_directory(web_dist_dir, 'index.html')
    else:
        print("✓ API-only mode — no web_dist/index.html found")

    return app
