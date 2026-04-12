import os
import json
from starlette.requests import Request
from starlette.responses import JSONResponse
from . import recorder_router

LOG_FILE = os.environ.get('TRAFFIC_LOG_FILE', 'traffic_log.json')

@recorder_router.route('/api/recorder/traffic', methods=['GET'])
async def get_traffic(request: Request):
    """Get recorded traffic log"""
    if not os.path.exists(LOG_FILE):
        return JSONResponse([])
    
    try:
        with open(LOG_FILE, 'r') as f:
            data = json.load(f)
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code = 500)

@recorder_router.route('/api/recorder/traffic', methods=['DELETE'])
async def clear_traffic(request: Request):
    """Clear recorded traffic log"""
    try:
        with open(LOG_FILE, 'w') as f:
            json.dump([], f)
        return JSONResponse({'status': 'cleared'})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code = 500)

@recorder_router.route('/api/recorder/status', methods=['GET'])
async def recorder_status(request: Request):
    """Check if recording is enabled"""
    enabled = os.environ.get('RECORD_TRAFFIC', 'false').lower() == 'true'
    return JSONResponse({
        'enabled': enabled,
        'log_file': LOG_FILE,
        'entry_count': len(json.load(open(LOG_FILE))) if os.path.exists(LOG_FILE) else 0
    })
