"""
Application factory for the  WAF Demo Site.
"""

import os
from flask import Flask, Response, jsonify, request, send_from_directory

from app.config import init_config
from app.throughput import (
    bool_env,
    int_env,
    throughput_payload_bytes,
    build_payload_cache,
)


def create_app(config=None):
    """
    Application factory pattern for creating Flask app instances.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured Flask application instance
    """
    # Initialize framework-agnostic config before anything else
    app_config = init_config(config)

    app = Flask(__name__, static_folder="../static")

    # Basic configuration
    app.secret_key = app_config.secret_key

    # Initialize Swagger (legacy flasgger setup retained for backward compatibility)
    from flasgger import Swagger

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": " Demo API",
            "description": "API Documentation for  WAF TestBed. <br><br><b>Note:</b> This API contains intentional vulnerabilities for educational and testing purposes.",
            "version": "1.0.0",
        },
        "schemes": ["http", "https"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"',
            }
        },
    }
    Swagger(app, template=swagger_template)

    # Enable debug mode for demo environment to ensure verbose error responses
    demo_mode = os.environ.get("DEMO_MODE", "true").lower() == "true"
    if demo_mode:
        app.config["DEBUG"] = True
        app.config["ENV"] = "development"
        app.config["DEMO_MODE"] = True

    # Initialize database if USE_DATABASE=true
    use_database = os.environ.get("USE_DATABASE", "false").lower() == "true"
    if use_database:
        from app.database import init_database

        db_initialized = init_database(app)
        if db_initialized:
            print("✓ Database mode enabled (SQLite)")
        else:
            print("✗ Database initialization failed")
    else:
        print("✓ In-memory mode (no database)")

    throughput_mode = bool_env("DEMO_THROUGHPUT_MODE")
    if throughput_mode:
        payload_bytes = throughput_payload_bytes()
        payload_cache = build_payload_cache(payload_bytes)
        payload = payload_cache[payload_bytes]
        payload_size = len(payload)
        max_payload_bytes = int_env("DEMO_THROUGHPUT_MAX_BYTES") or (1024 * 1024)
        throughput_only_fast = bool_env("DEMO_THROUGHPUT_ONLY_FAST")
        match_paths = [
            p.strip()
            for p in os.environ.get("DEMO_THROUGHPUT_PATHS", "").split(",")
            if p.strip()
        ]
        exclude_paths = [
            p.strip()
            for p in os.environ.get("DEMO_THROUGHPUT_EXCLUDE_PATHS", "").split(",")
            if p.strip()
        ]

        app.config["DEMO_THROUGHPUT_MODE"] = True
        app.config["DEMO_THROUGHPUT_PAYLOAD"] = payload
        app.config["DEMO_THROUGHPUT_PAYLOAD_BYTES"] = payload_size
        app.config["DEMO_THROUGHPUT_PAYLOAD_CACHE"] = payload_cache
        app.config["DEMO_THROUGHPUT_MAX_BYTES"] = max_payload_bytes
        app.config["DEMO_THROUGHPUT_ONLY_FAST"] = throughput_only_fast
        app.config["DEMO_THROUGHPUT_PATHS"] = match_paths
        app.config["DEMO_THROUGHPUT_EXCLUDE_PATHS"] = exclude_paths

        @app.before_request
        def short_circuit_exports():
            if throughput_only_fast:
                return None
            if request.method not in {"GET", "POST"}:
                return None
            path = request.path or ""
            if exclude_paths and any(token in path for token in exclude_paths):
                return None
            if match_paths:
                if not any(token in path for token in match_paths):
                    return None
            elif "export" not in path:
                return None

            response = Response(payload, mimetype="application/json")
            response.headers["X-Demo-Throughput"] = "true"
            response.headers["X-Demo-Throughput-Bytes"] = str(payload_size)
            return response

    apparatus_enabled = bool_env("APPARATUS_ENABLED", default=False)
    apparatus_base_url = os.environ.get(
        "APPARATUS_BASE_URL", "http://127.0.0.1:8090"
    ).strip()
    apparatus_timeout_ms = int_env("APPARATUS_TIMEOUT_MS")
    if apparatus_timeout_ms is None or apparatus_timeout_ms < 1:
        apparatus_timeout_ms = 5000

    app.config["APPARATUS_ENABLED"] = apparatus_enabled
    app.config["APPARATUS_BASE_URL"] = apparatus_base_url
    app.config["APPARATUS_TIMEOUT_MS"] = apparatus_timeout_ms

    # Register Security Headers (CSP + CORS)
    @app.after_request
    def add_security_headers(response):
        """Set Content-Security-Policy and CORS headers for all responses"""
        # CORS Headers - Intentionally permissive for demo
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS"
        )
        response.headers["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, X-Requested-With"
        )

        if request.path in {"/swagger", "/openapi.yaml"}:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self' https://unpkg.com; "
                "style-src 'self' https://unpkg.com 'unsafe-inline'; "
                "script-src 'self' https://unpkg.com 'unsafe-inline'; "
                "img-src 'self' data: https://unpkg.com; "
                "font-src 'self' https://unpkg.com; "
                "connect-src 'self'"
            )
            return response

        # SPA routes need relaxed CSP for Tailwind/Vite inline styles
        if not request.path.startswith(
            ("/api/", "/apidocs", "/flasgger_static", "/apispec")
        ):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "script-src 'self'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'"
            )
        else:
            response.headers["Content-Security-Policy"] = (
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

    # Import and register blueprints.
    # NOTE: main, recorder, diagnostics, throughput, admin, government,
    # telecom, energy_utilities, security_ops, loyalty, compliance, ics_ot,
    # infrastructure, genai, education, checkout, mobile, payments, and saas have been
    # migrated to Starlette (see app/asgi.py).
    # During the transition, migrated API domains listed below are mirrored
    # back into Flask via register_flask_compat_routes so app.py/local WSGI
    # callers keep working while the cutover remains in mixed mode.
    from app.blueprints.auth import auth_bp
    from app.blueprints.banking import banking_router
    from app.blueprints.mobile import mobile_router
    from app.blueprints.healthcare import healthcare_bp
    from app.blueprints.ecommerce import ecommerce_bp
    from app.blueprints.checkout import checkout_router
    from app.blueprints.payments import payments_router
    from app.blueprints.insurance import insurance_router
    from app.blueprints.integrations import integrations_bp
    from app.blueprints.saas import saas_router
    from app.blueprints.admin import admin_router
    from app.blueprints.testing import testing_bp
    from app.blueprints.education import education_router
    from app.blueprints.attack_sim import attack_sim_router
    from app.blueprints.government import government_router
    from app.blueprints.telecom import telecom_router
    from app.blueprints.energy_utilities import energy_utilities_router
    from app.blueprints.security_ops import security_ops_router
    from app.blueprints.loyalty import loyalty_router
    from app.blueprints.compliance import compliance_router
    from app.blueprints.ics_ot import ics_ot_router
    from app.blueprints.infrastructure import infrastructure_router
    from app.blueprints.genai import genai_router
    from app.blueprints.diagnostics import diagnostics_router
    from app.blueprints.throughput import throughput_router
    from app.blueprints.recorder import recorder_router
    from app.middleware.traffic_recorder import TrafficRecorder
    from app.routing import register_flask_compat_routes

    # Initialize Traffic Recorder
    TrafficRecorder(app)

    # Register remaining Flask blueprints while migrated routes stay mirrored via compat adapters.
    app.register_blueprint(auth_bp)
    app.register_blueprint(healthcare_bp)
    app.register_blueprint(ecommerce_bp)
    app.register_blueprint(integrations_bp)
    app.register_blueprint(testing_bp)

    register_flask_compat_routes(app, admin_router, endpoint_prefix="admin")
    register_flask_compat_routes(app, attack_sim_router, endpoint_prefix="attack_sim")
    register_flask_compat_routes(app, government_router, endpoint_prefix="government")
    register_flask_compat_routes(app, telecom_router, endpoint_prefix="telecom")
    register_flask_compat_routes(
        app, energy_utilities_router, endpoint_prefix="energy_utilities"
    )
    register_flask_compat_routes(
        app, security_ops_router, endpoint_prefix="security_ops"
    )
    register_flask_compat_routes(app, loyalty_router, endpoint_prefix="loyalty")
    register_flask_compat_routes(app, compliance_router, endpoint_prefix="compliance")
    register_flask_compat_routes(app, ics_ot_router, endpoint_prefix="ics_ot")
    register_flask_compat_routes(
        app, infrastructure_router, endpoint_prefix="infrastructure"
    )
    register_flask_compat_routes(app, genai_router, endpoint_prefix="genai")
    register_flask_compat_routes(app, education_router, endpoint_prefix="education")
    register_flask_compat_routes(app, checkout_router, endpoint_prefix="checkout")
    register_flask_compat_routes(app, mobile_router, endpoint_prefix="mobile")
    register_flask_compat_routes(app, payments_router, endpoint_prefix="payments")
    register_flask_compat_routes(app, saas_router, endpoint_prefix="saas")
    register_flask_compat_routes(app, banking_router, endpoint_prefix="banking")
    register_flask_compat_routes(app, insurance_router, endpoint_prefix="insurance")
    register_flask_compat_routes(app, diagnostics_router, endpoint_prefix="diagnostics")
    register_flask_compat_routes(app, throughput_router, endpoint_prefix="throughput")
    register_flask_compat_routes(app, recorder_router, endpoint_prefix="recorder")

    # Healthz + home — previously served by main_bp (now Starlette-only).
    # Provide minimal Flask equivalents so Docker healthchecks and SPA tests work.
    @app.route("/healthz")
    @app.route("/api/v1/healthz")
    def _healthz():
        return jsonify({"status": "healthy"}), 200

    from flask import render_template_string as _rts
    from app.utils import DEMO_PAGE_TEMPLATE as _DEMO_PAGE_TEMPLATE

    _web_dist_dir = os.path.join(os.path.dirname(__file__), "web_dist")
    _spa_index = os.path.join(_web_dist_dir, "index.html")

    @app.route("/")
    def _home():
        if os.path.isfile(_spa_index):
            return send_from_directory(_web_dist_dir, "index.html")
        return _rts(_DEMO_PAGE_TEMPLATE)

    # Register database vulnerable endpoints (if database mode enabled)
    if use_database:
        from app.blueprints.database_vulnerable import db_vuln_bp

        app.register_blueprint(db_vuln_bp)
        print("✓ SQL injection test endpoints enabled")

    # Static OpenAPI spec + Swagger UI
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))

    @app.get("/openapi.yaml")
    def openapi_spec():
        return send_from_directory(docs_dir, "openapi.yaml")

    @app.get("/swagger")
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
        return Response(html, mimetype="text/html")

    # Initialize demo data
    with app.app_context():
        from app.utils import init_demo_data

        init_demo_data()

    # --- SPA serving: bundle the React frontend into Flask ---
    web_dist_dir = os.path.join(os.path.dirname(__file__), "web_dist")
    spa_index = os.path.join(web_dist_dir, "index.html")
    _API_PREFIXES = ("api/", "apidocs", "flasgger_static", "apispec")

    if os.path.isfile(spa_index):
        print("✓ SPA mode — serving web portal from app/web_dist/")

        # Replace the main blueprint's / handler instead of adding a
        # duplicate URL rule (blueprint routes match before app routes).
        def _serve_spa_index():
            return send_from_directory(web_dist_dir, "index.html")

        app.view_functions["main.home"] = _serve_spa_index

        @app.route("/<path:path>")
        def spa_catch_all(path):
            # Let API and Swagger routes return 404 so error handlers work
            if path.startswith(_API_PREFIXES):
                return jsonify({"error": "Not found"}), 404

            # Serve actual static files (JS, CSS, images, etc.)
            static_path = os.path.join(web_dist_dir, path)
            if os.path.isfile(static_path):
                return send_from_directory(web_dist_dir, path)

            # Everything else → index.html (React Router handles it)
            return send_from_directory(web_dist_dir, "index.html")

    else:
        print("✓ API-only mode — no web_dist/index.html found")

    return app
