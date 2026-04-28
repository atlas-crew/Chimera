"""
Routes for integrations endpoints.
"""
from starlette.requests import Request
from starlette.responses import JSONResponse
from datetime import datetime, timedelta
import uuid
import random
import json
import time

import logging

from . import integrations_router
from app.config import app_config
from app.routing import safe_json
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
        return JSONResponse(exc.to_dict(), status_code = 503)
    if isinstance(exc, ApparatusServiceConfigError):
        return JSONResponse(exc.to_dict(), status_code = 500)
    if isinstance(exc, ApparatusServiceNetworkError):
        return JSONResponse(exc.to_dict(), status_code = 502)
    if isinstance(exc, ApparatusServiceUpstreamError):
        return JSONResponse(exc.to_dict(), status_code = 502)
    logging.getLogger('chimera').exception('Unexpected Apparatus integration error', exc_info=exc)
    return JSONResponse({
        'error': 'apparatus_error',
        'message': 'An internal error occurred while processing the Apparatus integration request.',
    }, status_code = 500)


def _get_apparatus_service():
    return ApparatusService(build_apparatus_settings())


@integrations_router.route('/api/v1/integrations/ws/simulate-frame', methods=['POST'])
async def ws_simulate_frame(request: Request):
    """
    Simulated WebSocket message frame processor.
    VULNERABILITY: Insecure Message Processing, Logic Manipulation
    """
    data = await safe_json(request)
    frame_type = data.get('type', 'text')
    payload = data.get('data', {})
    
    # Intentionally vulnerable to admin_override manipulation in the simulated frame
    is_admin = payload.get('admin_override', False)
    
    return JSONResponse({
        'status': 'frame_processed',
        'type': frame_type,
        'effective_privileges': 'admin' if is_admin else 'user',
        'warning': 'Simulated WebSocket frame processed without signature validation'
    })


@integrations_router.route('/api/v1/integrations/apparatus/status')
async def integrations_apparatus_status(request: Request):
    """Surface Apparatus connectivity and ghost status for Chimera UI clients."""
    settings = build_apparatus_settings()

    if not settings.enabled:
        return JSONResponse(_apparatus_status_fallback(
            enabled=False,
            configured=bool(settings.base_url),
            base_url=settings.base_url,
            error='apparatus_disabled',
            message='Apparatus integration is disabled.',
        ))

    if not settings.base_url:
        return JSONResponse(_apparatus_status_fallback(
            enabled=True,
            configured=False,
            base_url='',
            error='apparatus_config_error',
            message='APPARATUS_BASE_URL must be configured when Apparatus is enabled.',
        ))

    service = _get_apparatus_service()
    try:
        return JSONResponse(service.get_status())
    except (ApparatusServiceNetworkError, ApparatusServiceUpstreamError) as exc:
        return JSONResponse(_apparatus_status_fallback(
            enabled=True,
            configured=True,
            base_url=settings.base_url,
            error=exc.error_code,
            message=str(exc),
        ))


@integrations_router.route('/api/v1/integrations/apparatus/history')
async def integrations_apparatus_history(request: Request):
    """Return bounded Apparatus request history for UI display."""
    try:
        limit = int(request.query_params.get('limit', 50))
    except (TypeError, ValueError):
        limit = 50
    if limit <= 0:
        limit = 50
    limit = min(limit, 500)

    service = _get_apparatus_service()
    try:
        return JSONResponse(service.get_history(limit=limit))
    except (
        ApparatusServiceDisabledError,
        ApparatusServiceConfigError,
        ApparatusServiceNetworkError,
        ApparatusServiceUpstreamError,
    ) as exc:
        return _apparatus_error_response(exc)


@integrations_router.route('/api/v1/integrations/apparatus/ghosts/start', methods=['POST'])
async def integrations_apparatus_ghosts_start(request: Request):
    """Start Apparatus ghost traffic with Chimera-provided settings."""
    service = _get_apparatus_service()
    payload = await safe_json(request)
    allowed_keys = {'rps', 'duration', 'endpoints'}

    if not isinstance(payload, dict):
        return JSONResponse({
            'error': 'apparatus_validation_error',
            'message': 'Ghost start payload must be a JSON object.',
        }, status_code = 400)

    unknown_keys = sorted(set(payload.keys()) - allowed_keys)
    if unknown_keys:
        return JSONResponse({
            'error': 'apparatus_validation_error',
            'message': f'Unsupported ghost start fields: {", ".join(unknown_keys)}.',
        }, status_code = 400)

    try:
        return JSONResponse(service.start_ghosts(payload))
    except (
        ApparatusServiceDisabledError,
        ApparatusServiceConfigError,
        ApparatusServiceNetworkError,
        ApparatusServiceUpstreamError,
    ) as exc:
        return _apparatus_error_response(exc)


@integrations_router.route('/api/v1/integrations/apparatus/ghosts/stop', methods=['POST'])
async def integrations_apparatus_ghosts_stop(request: Request):
    """Stop Apparatus ghost traffic."""
    service = _get_apparatus_service()

    try:
        return JSONResponse(service.stop_ghosts())
    except (
        ApparatusServiceDisabledError,
        ApparatusServiceConfigError,
        ApparatusServiceNetworkError,
        ApparatusServiceUpstreamError,
    ) as exc:
        return _apparatus_error_response(exc)


@integrations_router.route('/api/webhooks/register', methods=['POST'])
async def webhooks_register(request: Request):
    """Webhook registration for persistence"""
    data = await request.json()
    callback_url = data.get('callback_url', '')


@integrations_router.route('/api/integrations/discovery')
async def integrations_discovery(request: Request):
    """Service discovery endpoint - exposes internal architecture"""
    # Intentionally exposes internal service topology for reconnaissance
    return JSONResponse({
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


@integrations_router.route('/api/webhooks/callback', methods=['POST'])
async def webhooks_callback(request: Request):
    """Webhook callback endpoint - vulnerable to SSRF and hijacking"""
    data = await safe_json(request)
    target_url = data.get('url', '')


@integrations_router.route('/api/integrations/third-party', methods=['POST'])
async def integrations_third_party(request: Request):
    """Third-party integration registration - credential exposure"""
    data = await safe_json(request)


@integrations_router.route('/api/integrations/payment/webhook')
async def integrations_payment_webhook(request: Request):
    """Payment webhook endpoint - vulnerable to replay attacks"""
    # No signature verification
    # Accepts duplicate webhook events


@integrations_router.route('/api/integrations/cdn/invalidate', methods=['POST'])
async def integrations_cdn_invalidate(request: Request):
    """CDN cache invalidation - vulnerable to cache poisoning"""
    data = await safe_json(request)


@integrations_router.route('/api/integrations/social/callback')
async def integrations_social_callback(request: Request):
    """Social OAuth callback - vulnerable to authorization code interception"""
    code = request.query_params.get('code', '')
    state = request.query_params.get('state', '')


@integrations_router.route('/api/integrations/email/webhook', methods=['POST'])
async def integrations_email_webhook(request: Request):
    """Email service webhook - vulnerable to header injection"""
    data = await safe_json(request)


@integrations_router.route('/api/integrations/analytics/data')
async def integrations_analytics_data(request: Request):
    """Analytics data export - exposes PII and business intelligence"""
    # No authentication or authorization
    # Exposes sensitive analytics data


@integrations_router.route('/api/integrations/crm/sync', methods=['POST'])
async def integrations_crm_sync(request: Request):
    """CRM data synchronization - mass data exfiltration vector"""
    data = await safe_json(request)


@integrations_router.route('/api/integrations/backdoor', methods=['POST'])
async def integrations_backdoor(request: Request):
    """Integration backdoor - persistent access mechanism"""
    data = await safe_json(request)


@integrations_router.route('/api/integrations/export')
async def integrations_export(request: Request):
    """Integration configuration export - credential exposure"""
    # Exports all integration configurations with credentials


@integrations_router.route('/api/integrations/verify', methods=['POST'])
async def integrations_verify(request: Request):
    """Integration verification endpoint - insecure signature validation"""
    data = await safe_json(request)
    signature = data.get('signature', '')
    payload = data.get('payload', {})
