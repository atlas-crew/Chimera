import subprocess
import requests
from starlette.requests import Request
from starlette.responses import JSONResponse
from . import diagnostics_router

@diagnostics_router.route('/api/v1/diagnostics/ping', methods=['POST'])
async def ping_host(request: Request):
    """
    Network Connectivity Check
    VULNERABILITY: Command Injection (RCE)
    """
    data = await request.json() or {}
    host = data.get('host', '8.8.8.8')

    # VULNERABILITY: Direct concatenation of user input into shell command
    command = f"ping -c 3 {host}"

    try:
        # Intentionally vulnerable execution
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=5)
        return JSONResponse({
            'host': host,
            'output': output.decode('utf-8'),
            'status': 'success'
        })
    except subprocess.CalledProcessError as e:
        return JSONResponse({
            'host': host,
            'output': e.output.decode('utf-8') if e.output else str(e),
            'status': 'error'
        })
    except Exception as e:
        return JSONResponse({
            'host': host,
            'output': str(e),
            'status': 'error'
        })

@diagnostics_router.route('/api/v1/diagnostics/webhook', methods=['GET', 'POST'])
async def test_webhook(request: Request):
    """
    Webhook Integration Tester
    VULNERABILITY: Server-Side Request Forgery (SSRF)
    """
    if request.method == 'POST':
        data = await request.json() or {}
        url = data.get('url', '')
    else:
        url = request.query_params.get('url', '')

    if not url:
        return JSONResponse({'error': 'URL required'}, status_code = 400)

    try:
        # VULNERABILITY: No validation of destination IP/domain (allows internal scan)
        response = requests.get(url, timeout=3, allow_redirects=True)
        
        return JSONResponse({
            'url': url,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content_preview': response.text[:500] if response.text else "",
            'status': 'success'
        })
    except Exception as e:
        return JSONResponse({
            'url': url,
            'error': str(e),
            'status': 'error'
        })
