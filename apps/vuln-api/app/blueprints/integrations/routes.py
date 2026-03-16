"""
Routes for integrations endpoints.
"""

from flask import request, jsonify, current_app
from datetime import datetime, timedelta
import uuid
import random
import json
import time

from . import integrations_bp
from app.models import *
from app.services import (
    ApparatusService,
    ApparatusServiceConfigError,
    ApparatusServiceDisabledError,
    ApparatusServiceNetworkError,
    ApparatusServiceUpstreamError,
    build_apparatus_settings,
)


def _apparatus_status_fallback(*, enabled, configured, base_url, error, message):
    return {
        'enabled': enabled,
        'configured': configured,
        'reachable': False,
        'baseUrl': base_url,
        'health': None,
        'ghosts': None,
        'error': error,
        'message': message,
    }


def _apparatus_error_response(exc):
    if isinstance(exc, ApparatusServiceDisabledError):
        return jsonify(exc.to_dict()), 503
    if isinstance(exc, ApparatusServiceConfigError):
        return jsonify(exc.to_dict()), 500
    if isinstance(exc, ApparatusServiceNetworkError):
        return jsonify(exc.to_dict()), 502
    if isinstance(exc, ApparatusServiceUpstreamError):
        return jsonify(exc.to_dict()), 502
    current_app.logger.exception('Unexpected Apparatus integration error', exc_info=exc)
    return jsonify({
        'error': 'apparatus_error',
        'message': 'An internal error occurred while processing the Apparatus integration request.',
    }), 500


def _get_apparatus_service():
    return ApparatusService(build_apparatus_settings(current_app.config))


@integrations_bp.route('/api/v1/integrations/ws/simulate-frame', methods=['POST'])
def ws_simulate_frame():
    """
    Simulated WebSocket message frame processor.
    VULNERABILITY: Insecure Message Processing, Logic Manipulation
    """
    data = request.get_json() or {}
    frame_type = data.get('type', 'text')
    payload = data.get('data', {})
    
    # Intentionally vulnerable to admin_override manipulation in the simulated frame
    is_admin = payload.get('admin_override', False)
    
    return jsonify({
        'status': 'frame_processed',
        'type': frame_type,
        'effective_privileges': 'admin' if is_admin else 'user',
        'warning': 'Simulated WebSocket frame processed without signature validation'
    })


@integrations_bp.route('/api/v1/integrations/apparatus/status')
def integrations_apparatus_status():
    """Surface Apparatus connectivity and ghost status for Chimera UI clients."""
    settings = build_apparatus_settings(current_app.config)

    if not settings.enabled:
        return jsonify(_apparatus_status_fallback(
            enabled=False,
            configured=bool(settings.base_url),
            base_url=settings.base_url,
            error='apparatus_disabled',
            message='Apparatus integration is disabled.',
        ))

    if not settings.base_url:
        return jsonify(_apparatus_status_fallback(
            enabled=True,
            configured=False,
            base_url='',
            error='apparatus_config_error',
            message='APPARATUS_BASE_URL must be configured when Apparatus is enabled.',
        ))

    service = _get_apparatus_service()
    try:
        return jsonify(service.get_status())
    except (ApparatusServiceNetworkError, ApparatusServiceUpstreamError) as exc:
        return jsonify(_apparatus_status_fallback(
            enabled=True,
            configured=True,
            base_url=settings.base_url,
            error=exc.error_code,
            message=str(exc),
        ))


@integrations_bp.route('/api/v1/integrations/apparatus/history')
def integrations_apparatus_history():
    """Return bounded Apparatus request history for UI display."""
    limit = request.args.get('limit', default=50, type=int)
    if limit <= 0:
        limit = 50
    limit = min(limit, 500)

    service = _get_apparatus_service()
    try:
        return jsonify(service.get_history(limit=limit))
    except (
        ApparatusServiceDisabledError,
        ApparatusServiceConfigError,
        ApparatusServiceNetworkError,
        ApparatusServiceUpstreamError,
    ) as exc:
        return _apparatus_error_response(exc)


@integrations_bp.route('/api/v1/integrations/apparatus/ghosts/start', methods=['POST'])
def integrations_apparatus_ghosts_start():
    """Start Apparatus ghost traffic with Chimera-provided settings."""
    service = _get_apparatus_service()
    payload = request.get_json(silent=True) or {}
    allowed_keys = {'rps', 'duration', 'endpoints'}

    if not isinstance(payload, dict):
        return jsonify({
            'error': 'apparatus_validation_error',
            'message': 'Ghost start payload must be a JSON object.',
        }), 400

    unknown_keys = sorted(set(payload.keys()) - allowed_keys)
    if unknown_keys:
        return jsonify({
            'error': 'apparatus_validation_error',
            'message': f'Unsupported ghost start fields: {", ".join(unknown_keys)}.',
        }), 400

    try:
        return jsonify(service.start_ghosts(payload))
    except (
        ApparatusServiceDisabledError,
        ApparatusServiceConfigError,
        ApparatusServiceNetworkError,
        ApparatusServiceUpstreamError,
    ) as exc:
        return _apparatus_error_response(exc)


@integrations_bp.route('/api/v1/integrations/apparatus/ghosts/stop', methods=['POST'])
def integrations_apparatus_ghosts_stop():
    """Stop Apparatus ghost traffic."""
    service = _get_apparatus_service()

    try:
        return jsonify(service.stop_ghosts())
    except (
        ApparatusServiceDisabledError,
        ApparatusServiceConfigError,
        ApparatusServiceNetworkError,
        ApparatusServiceUpstreamError,
    ) as exc:
        return _apparatus_error_response(exc)


@integrations_bp.route('/api/webhooks/register', methods=['POST'])
def webhooks_register():
    """Webhook registration for persistence"""
    data = request.get_json()
    callback_url = data.get('callback_url', '')


@integrations_bp.route('/api/integrations/discovery')
def integrations_discovery():
    """Service discovery endpoint - exposes internal architecture"""
    # Intentionally exposes internal service topology for reconnaissance
    return jsonify({
        'services': [
            {'name': 'auth-service', 'endpoint': 'http://internal-auth:8080', 'version': '2.1.0'},
            {'name': 'payment-gateway', 'endpoint': 'http://internal-payment:8081', 'version': '1.5.2'},
            {'name': 'database-proxy', 'endpoint': 'http://internal-db:5432', 'version': '14.5'},
            {'name': 'redis-cache', 'endpoint': 'http://internal-cache:6379', 'version': '7.0.5'},
            {'name': 'admin-panel', 'endpoint': 'http://internal-admin:9000', 'version': '3.2.1'}
        ],
        'internal_ips': ['10.0.1.5', '10.0.1.6', '10.0.1.7'],
        'api_gateway': 'http://api-gateway.internal:443',
        'service_mesh': 'istio-1.19.0',
        'load_balancer': 'nginx-1.24.0'
    })


@integrations_bp.route('/api/webhooks/callback', methods=['POST'])
def webhooks_callback():
    """Webhook callback endpoint - vulnerable to SSRF and hijacking"""
    data = request.get_json() or {}
    target_url = data.get('url', '')


@integrations_bp.route('/api/integrations/third-party', methods=['POST'])
def integrations_third_party():
    """Third-party integration registration - credential exposure"""
    data = request.get_json() or {}


@integrations_bp.route('/api/integrations/payment/webhook')
def integrations_payment_webhook():
    """Payment webhook endpoint - vulnerable to replay attacks"""
    # No signature verification
    # Accepts duplicate webhook events


@integrations_bp.route('/api/integrations/cdn/invalidate', methods=['POST'])
def integrations_cdn_invalidate():
    """CDN cache invalidation - vulnerable to cache poisoning"""
    data = request.get_json() or {}


@integrations_bp.route('/api/integrations/social/callback')
def integrations_social_callback():
    """Social OAuth callback - vulnerable to authorization code interception"""
    code = request.args.get('code', '')
    state = request.args.get('state', '')


@integrations_bp.route('/api/integrations/email/webhook', methods=['POST'])
def integrations_email_webhook():
    """Email service webhook - vulnerable to header injection"""
    data = request.get_json() or {}


@integrations_bp.route('/api/integrations/analytics/data')
def integrations_analytics_data():
    """Analytics data export - exposes PII and business intelligence"""
    # No authentication or authorization
    # Exposes sensitive analytics data


@integrations_bp.route('/api/integrations/crm/sync', methods=['POST'])
def integrations_crm_sync():
    """CRM data synchronization - mass data exfiltration vector"""
    data = request.get_json() or {}


@integrations_bp.route('/api/integrations/backdoor', methods=['POST'])
def integrations_backdoor():
    """Integration backdoor - persistent access mechanism"""
    data = request.get_json() or {}


@integrations_bp.route('/api/integrations/export')
def integrations_export():
    """Integration configuration export - credential exposure"""
    # Exports all integration configurations with credentials


@integrations_bp.route('/api/integrations/verify', methods=['POST'])
def integrations_verify():
    """Integration verification endpoint - insecure signature validation"""
    data = request.get_json() or {}
    signature = data.get('signature', '')
    payload = data.get('payload', {})
