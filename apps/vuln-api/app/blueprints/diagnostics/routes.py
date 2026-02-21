import subprocess
import requests
from flask import request, jsonify
from . import diagnostics_bp

@diagnostics_bp.route('/api/v1/diagnostics/ping', methods=['POST'])
def ping_host():
    """
    Network Connectivity Check
    VULNERABILITY: Command Injection (RCE)
    """
    data = request.get_json() or {}
    host = data.get('host', '8.8.8.8')

    # VULNERABILITY: Direct concatenation of user input into shell command
    command = f"ping -c 3 {host}"

    try:
        # Intentionally vulnerable execution
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=5)
        return jsonify({
            'host': host,
            'output': output.decode('utf-8'),
            'status': 'success'
        })
    except subprocess.CalledProcessError as e:
        return jsonify({
            'host': host,
            'output': e.output.decode('utf-8') if e.output else str(e),
            'status': 'error'
        })
    except Exception as e:
        return jsonify({
            'host': host,
            'output': str(e),
            'status': 'error'
        })

@diagnostics_bp.route('/api/v1/diagnostics/webhook', methods=['POST'])
def test_webhook():
    """
    Webhook Integration Tester
    VULNERABILITY: Server-Side Request Forgery (SSRF)
    """
    data = request.get_json() or {}
    url = data.get('url', '')

    if not url:
        return jsonify({'error': 'URL required'}), 400

    try:
        # VULNERABILITY: No validation of destination IP/domain (allows internal scan)
        response = requests.get(url, timeout=3, allow_redirects=True)
        
        return jsonify({
            'url': url,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content_preview': response.text[:500] if response.text else "",
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'url': url,
            'error': str(e),
            'status': 'error'
        })
