"""
Fast-path endpoints for throughput testing.
"""

from flask import Response, jsonify, request, current_app

from . import throughput_bp
from app.throughput import build_throughput_payload

_SIZE_LABELS = {
    'small': 2 * 1024,
    'medium': 8 * 1024,
    'large': 64 * 1024
}


def _disabled():
    return jsonify({'error': 'Throughput mode disabled'}), 404


def _parse_int(value: str):
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


@throughput_bp.route('/fast/ping')
def fast_ping():
    if not current_app.config.get('DEMO_THROUGHPUT_MODE', False):
        return _disabled()

    return jsonify({
        'status': 'ok',
        'mode': 'throughput',
        'payload_bytes': current_app.config.get('DEMO_THROUGHPUT_PAYLOAD_BYTES', 0),
        'max_bytes': current_app.config.get('DEMO_THROUGHPUT_MAX_BYTES', 0)
    })


@throughput_bp.route('/fast/export')
def fast_export():
    if not current_app.config.get('DEMO_THROUGHPUT_MODE', False):
        return _disabled()

    cache = current_app.config.get('DEMO_THROUGHPUT_PAYLOAD_CACHE', {})
    default_bytes = current_app.config.get('DEMO_THROUGHPUT_PAYLOAD_BYTES', 2 * 1024)
    max_bytes = current_app.config.get('DEMO_THROUGHPUT_MAX_BYTES', 1024 * 1024)

    target_bytes = default_bytes
    size = request.args.get('size', '').lower()
    if size in _SIZE_LABELS:
        target_bytes = _SIZE_LABELS[size]
    else:
        bytes_param = _parse_int(request.args.get('bytes'))
        kb_param = _parse_int(request.args.get('kb'))
        if bytes_param and bytes_param > 0:
            target_bytes = bytes_param
        elif kb_param and kb_param > 0:
            target_bytes = kb_param * 1024

    if max_bytes and target_bytes > max_bytes:
        target_bytes = max_bytes

    payload = cache.get(target_bytes)
    if payload is None:
        payload = build_throughput_payload(target_bytes)
        cache[target_bytes] = payload

    response = Response(payload, mimetype='application/json')
    response.headers['X-Demo-Throughput'] = 'true'
    response.headers['X-Demo-Throughput-Bytes'] = str(len(payload))
    return response
