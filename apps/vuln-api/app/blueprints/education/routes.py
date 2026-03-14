from flask import jsonify, request, session, current_app
from . import education_bp
from app.utils.vuln_registry import VULN_REGISTRY
from app.utils.security_config import security_config

def _filter_vuln_meta(meta):
    """Remove internal implementation details from the public response."""
    filtered = meta.copy()
    filtered.pop('config_key', None)
    return filtered

@education_bp.before_request
def check_access():
    """
    Lightweight auth gate for educational metadata.
    Operational infrastructure should not be enumerable by unauthenticated scanners.
    """
    # P0-001 Fix (Review 9): Only allow local bypass in debug mode using trusted remote_addr.
    # access_route is client-controlled (spoofable) and thus not trusted for security gates.
    is_local = current_app.debug and request.remote_addr == '127.0.0.1'
    has_session = bool(session.get('user_id'))
    
    if not is_local and not has_session:
        return jsonify({
            'error': 'Authentication required to access educational metadata',
            'note': 'This endpoint is part of the lab infrastructure, not an intentional vulnerability.'
        }), 401

@education_bp.route('/api/v1/education/vulns', methods=['GET'])
def get_all_vulns():
    """Get the full vulnerability catalog"""
    portal = request.args.get('portal')
    
    if portal:
        filtered = {k: _filter_vuln_meta(v) for k, v in VULN_REGISTRY.items() if v['portal'] == portal}
        return jsonify(filtered)
        
    return jsonify({k: _filter_vuln_meta(v) for k, v in VULN_REGISTRY.items()})

@education_bp.route('/api/v1/education/vulns/<vuln_id>', methods=['GET'])
def get_vuln_detail(vuln_id):
    """Get deep dive for a specific vulnerability"""
    vuln = VULN_REGISTRY.get(vuln_id)
    if not vuln:
        return jsonify({'error': 'Vulnerability not found'}), 404
        
    # Enrich with current patch status
    config_key = vuln.get('config_key')
    is_patched = False
    if config_key:
        is_patched = getattr(security_config, config_key, False)
        
    response = _filter_vuln_meta(vuln)
    response['is_patched'] = is_patched
    
    return jsonify(response)

@education_bp.route('/api/v1/education/portals', methods=['GET'])
def get_portals():
    """Get all available industry portals"""
    portals = sorted(list(set(v['portal'] for v in VULN_REGISTRY.values())))
    return jsonify({'portals': portals})

@education_bp.route('/api/v1/education/owasp', methods=['GET'])
def get_owasp_categories():
    """Get vulns grouped by OWASP category"""
    categories = {}
    for vid, meta in VULN_REGISTRY.items():
        owasp = meta['owasp']
        if owasp not in categories:
            categories[owasp] = []
        categories[owasp].append(vid)
    return jsonify(categories)
