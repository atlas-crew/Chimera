import os
import json
from flask import jsonify, request
from . import recorder_bp

LOG_FILE = os.environ.get('TRAFFIC_LOG_FILE', 'traffic_log.json')

@recorder_bp.route('/api/recorder/traffic', methods=['GET'])
def get_traffic():
    """Get recorded traffic log"""
    if not os.path.exists(LOG_FILE):
        return jsonify([])
    
    try:
        with open(LOG_FILE, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recorder_bp.route('/api/recorder/traffic', methods=['DELETE'])
def clear_traffic():
    """Clear recorded traffic log"""
    try:
        with open(LOG_FILE, 'w') as f:
            json.dump([], f)
        return jsonify({'status': 'cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recorder_bp.route('/api/recorder/status', methods=['GET'])
def recorder_status():
    """Check if recording is enabled"""
    enabled = os.environ.get('RECORD_TRAFFIC', 'false').lower() == 'true'
    return jsonify({
        'enabled': enabled,
        'log_file': LOG_FILE,
        'entry_count': len(json.load(open(LOG_FILE))) if os.path.exists(LOG_FILE) else 0
    })
