"""
Fast-path endpoints for throughput testing.
"""
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from . import throughput_router
from app.config import app_config
from app.throughput import build_throughput_payload

_SIZE_LABELS = {
    'small': 2 * 1024,
    'medium': 8 * 1024,
    'large': 64 * 1024
}


def _disabled():
    return JSONResponse({'error': 'Throughput mode disabled'}, status_code = 404)


def _parse_int(value: str):
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


_throughput_payload_cache: dict = {}


@throughput_router.route('/fast/ping')
async def fast_ping(request: Request):
    if not app_config.throughput_mode:
        return _disabled()

    return JSONResponse({
        'status': 'ok',
        'mode': 'throughput',
        'payload_bytes': app_config.throughput_payload_bytes,
        'max_bytes': app_config.throughput_max_bytes
    })


@throughput_router.route('/fast/export')
async def fast_export(request: Request):
    if not app_config.throughput_mode:
        return _disabled()

    default_bytes = app_config.throughput_payload_bytes
    max_bytes = app_config.throughput_max_bytes

    target_bytes = default_bytes
    size = request.query_params.get('size', '').lower()
    if size in _SIZE_LABELS:
        target_bytes = _SIZE_LABELS[size]
    else:
        bytes_param = _parse_int(request.query_params.get('bytes'))
        kb_param = _parse_int(request.query_params.get('kb'))
        if bytes_param and bytes_param > 0:
            target_bytes = bytes_param
        elif kb_param and kb_param > 0:
            target_bytes = kb_param * 1024

    if max_bytes and target_bytes > max_bytes:
        target_bytes = max_bytes

    payload = _throughput_payload_cache.get(target_bytes)
    if payload is None:
        payload = build_throughput_payload(target_bytes)
        _throughput_payload_cache[target_bytes] = payload

    return Response(
        content=payload,
        media_type='application/json',
        headers={
            'X-Demo-Throughput': 'true',
            'X-Demo-Throughput-Bytes': str(len(payload)),
        },
    )
