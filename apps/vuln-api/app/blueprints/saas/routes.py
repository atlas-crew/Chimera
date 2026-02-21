"""
Routes for SaaS platform endpoints.
Demonstrates tenant isolation, identity access, and billing abuse vulnerabilities.
"""

from flask import request, jsonify, session
from datetime import datetime
import uuid
import random
import time

from . import saas_bp
from app.models import *


# ============================================================================
# TENANT ISOLATION & DATA EXPOSURE
# ============================================================================

@saas_bp.route('/api/v1/saas/tenants/<tenant_id>/projects')
def list_tenant_projects(tenant_id):
    """List tenant projects - IDOR vulnerability"""
    projects = saas_projects_db.get(tenant_id)

    if not projects:
        projects = [
            {
                'project_id': f'proj-{random.randint(100, 999)}',
                'name': 'Recovered Project',
                'status': 'active',
                'last_updated': datetime.now().isoformat()
            }
        ]
        saas_projects_db[tenant_id] = projects

    return jsonify({
        'tenant_id': tenant_id,
        'projects': projects,
        'count': len(projects)
    })


@saas_bp.route('/api/v1/saas/tenants/<tenant_id>/export')
def tenant_export(tenant_id):
    """Export tenant data - admin data exfiltration"""
    include_pii = request.args.get('include_pii', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 1000))

    tenant = saas_tenants_db.get(tenant_id, {'tenant_id': tenant_id, 'name': 'Unknown'})
    users = get_saas_users_for_tenant(tenant_id)
    if not include_pii:
        for payload in users:
            payload.pop('email', None)

    users = users[:limit]

    return jsonify({
        'tenant': tenant,
        'users': users,
        'include_pii': include_pii,
        'exported': len(users)
    })


@saas_bp.route('/api/v1/saas/tenants/switch', methods=['POST'])
def tenant_switch():
    """Switch tenant context - bypass membership"""
    data = request.get_json() or {}
    tenant_id = data.get('tenant_id')
    bypass_membership = data.get('bypass_membership', False)

    session['tenant_id'] = tenant_id

    return jsonify({
        'active_tenant': tenant_id,
        'bypass_membership': bypass_membership,
        'warning': 'Tenant context switched without membership validation'
    })


@saas_bp.route('/api/v1/saas/share/links')
def share_links():
    """Shared links enumeration - scraping vulnerability"""
    include_private = request.args.get('include_private', 'false').lower() == 'true'
    limit = int(request.args.get('limit', 100))

    links = [link for link in saas_shared_links_db if include_private or not link.get('private')]

    return jsonify({
        'links': links[:limit],
        'count': len(links[:limit]),
        'include_private': include_private
    })


@saas_bp.route('/api/v1/saas/tenants/<tenant_id>/settings', methods=['PUT'])
def update_workspace_settings(tenant_id):
    """Update tenant settings - tampering vulnerability"""
    data = request.get_json() or {}
    settings = saas_workspace_settings_db.get(tenant_id, {'data_retention_days': 30, 'audit_enabled': True})

    settings.update({
        'data_retention_days': data.get('data_retention_days', settings['data_retention_days']),
        'audit_enabled': not data.get('disable_audit', False),
        'ip_allowlist': data.get('ip_allowlist', settings.get('ip_allowlist', []))
    })

    saas_workspace_settings_db[tenant_id] = settings

    return jsonify({
        'tenant_id': tenant_id,
        'settings': settings,
        'warning': 'Settings updated without authorization controls'
    })


@saas_bp.route('/api/v1/saas/org/invites', methods=['POST'])
def org_invites():
    """Organization invites - membership bypass"""
    data = request.get_json() or {}
    invite_id = f'invite-{uuid.uuid4().hex[:8]}'
    invite = {
        'invite_id': invite_id,
        'email': data.get('email'),
        'role': data.get('role', 'member'),
        'tenant_id': data.get('tenant_id', 'tenant-1'),
        'bypass_approval': data.get('bypass_approval', False),
        'created_at': datetime.now().isoformat()
    }
    saas_org_invites_db[invite_id] = invite

    return jsonify({
        'invite': invite,
        'warning': 'Invite issued without approval workflow'
    }), 201


# ============================================================================
# IDENTITY, SSO & ACCESS CONTROL
# ============================================================================

@saas_bp.route('/api/v1/saas/auth/sso/callback', methods=['POST'])
def saas_sso_callback():
    """SSO callback - assertion tampering"""
    data = request.get_json() or {}
    assertion = data.get('assertion', '')
    force_admin = data.get('force_admin', False)

    tampered = 'tampered' in assertion or force_admin
    role = 'owner' if tampered else 'member'

    return jsonify({
        'status': 'authenticated',
        'role': role,
        'assertion_validated': not tampered,
        'session_token': f'saas-sso-{uuid.uuid4().hex[:10]}'
    })


@saas_bp.route('/api/v1/saas/auth/saml/config', methods=['PUT'])
def saml_config_update():
    """SAML configuration tampering"""
    data = request.get_json() or {}
    tenant_id = data.get('tenant_id', 'tenant-1')
    config = {
        'tenant_id': tenant_id,
        'entity_id': data.get('entity_id'),
        'sso_url': data.get('sso_url'),
        'certificate': data.get('certificate'),
        'bypass_validation': data.get('bypass_validation', False),
        'updated_at': datetime.now().isoformat()
    }
    saas_saml_configs_db[tenant_id] = config

    return jsonify({
        'config': config,
        'warning': 'SAML configuration updated without validation'
    })


@saas_bp.route('/api/v1/saas/auth/token/refresh', methods=['POST'])
def token_refresh():
    """Token refresh - replay vulnerability"""
    data = request.get_json() or {}
    refresh_token = data.get('refresh_token')
    device_id = data.get('device_id', 'unknown')

    session_token = f'saas-token-{uuid.uuid4().hex[:12]}'

    return jsonify({
        'refresh_token': refresh_token,
        'device_id': device_id,
        'session_token': session_token,
        'rotation_enforced': False,
        'warning': 'Refresh token replay not detected'
    })


@saas_bp.route('/api/v1/saas/sessions/revoke', methods=['POST'])
def sessions_revoke():
    """Session revocation - unauthorized session termination"""
    data = request.get_json() or {}
    session_id = data.get('session_id', f'sess-{uuid.uuid4().hex[:6]}')
    saas_session_revocations_db[session_id] = {
        'session_id': session_id,
        'revoked': True,
        'force_revoke': data.get('force_revoke', False),
        'revoked_at': datetime.now().isoformat()
    }

    return jsonify({
        'session_id': session_id,
        'warning': 'Session revoked without authorization'
    })


@saas_bp.route('/api/v1/saas/auth/mfa/verify', methods=['POST'])
def saas_mfa_verify():
    """MFA verification - bypass vulnerability"""
    data = request.get_json() or {}
    code = data.get('code', '')
    bypass = data.get('bypass', False)

    return jsonify({
        'status': 'verified',
        'bypass_used': bypass or code == '000000',
        'message': 'MFA verification accepted'
    })


@saas_bp.route('/api/v1/saas/users/<user_id>/role', methods=['PUT'])
def update_user_role(user_id):
    """Role escalation - authorization bypass"""
    data = request.get_json() or {}
    new_role = data.get('role', 'member')
    bypass_approval = data.get('bypass_approval', False)

    current = saas_users_db.get(user_id, {'user_id': user_id, 'role': 'member'})
    old_role = current.get('role', 'member')
    update_saas_user(user_id, {'role': new_role})

    return jsonify({
        'user_id': user_id,
        'previous_role': old_role,
        'new_role': new_role,
        'bypass_approval': bypass_approval,
        'warning': 'Role change applied without approval'
    })


@saas_bp.route('/api/v1/saas/auth/password-reset', methods=['POST'])
def password_reset():
    """Password reset - IDOR vulnerability"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    send_link = data.get('send_link', True)

    token = f"reset-{user_id}-{int(time.time())}"

    return jsonify({
        'user_id': user_id,
        'reset_token': token,
        'send_link': send_link,
        'warning': 'Password reset issued without ownership verification'
    })


# ============================================================================
# BILLING & USAGE ABUSE
# ============================================================================

@saas_bp.route('/api/v1/saas/billing/usage', methods=['POST'])
def billing_usage():
    """Usage reporting - overflow vulnerability"""
    data = request.get_json() or {}
    usage_units = int(data.get('usage_units', 0))
    plan_id = data.get('plan_id', 'free')
    bypass_limits = data.get('bypass_limits', False)

    saas_billing_usage_db['latest'] = {
        'usage_units': usage_units,
        'plan_id': plan_id,
        'reported_at': datetime.now().isoformat()
    }

    return jsonify({
        'plan_id': plan_id,
        'usage_units': usage_units,
        'bypass_limits': bypass_limits,
        'billable_units': 0 if bypass_limits else usage_units,
        'warning': 'Usage accepted without quota validation'
    })


@saas_bp.route('/api/v1/saas/billing/invoices/<invoice_id>')
def invoice_download(invoice_id):
    """Invoice download - IDOR vulnerability"""
    invoice = saas_billing_invoices_db.get(invoice_id)
    if not invoice:
        invoice = {
            'invoice_id': invoice_id,
            'tenant_id': 'tenant-1',
            'amount': random.randint(100, 5000),
            'status': 'open',
            'issued_at': datetime.now().isoformat()
        }
        saas_billing_invoices_db[invoice_id] = invoice

    return jsonify(invoice)


@saas_bp.route('/api/v1/saas/billing/apply-coupon', methods=['POST'])
def apply_coupon():
    """Coupon stacking - business logic abuse"""
    data = request.get_json() or {}
    codes = data.get('codes', [])
    bypass_expiry = data.get('bypass_expiry', False)

    total_discount = 0.0
    applied = []
    for code in codes:
        coupon = saas_coupons_db.get(code, {'discount': 0.0})
        total_discount += coupon.get('discount', 0.0)
        applied.append(code)

    return jsonify({
        'applied_codes': applied,
        'total_discount': min(total_discount, 1.0) if bypass_expiry else total_discount,
        'bypass_expiry': bypass_expiry,
        'warning': 'Multiple coupons applied without stacking validation'
    })


@saas_bp.route('/api/v1/saas/billing/seats', methods=['PUT'])
def update_seats():
    """Seat count manipulation - billing bypass"""
    data = request.get_json() or {}
    seats = int(data.get('seats', 1))
    billable_seats = int(data.get('billable_seats', seats))

    return jsonify({
        'requested_seats': seats,
        'billable_seats': billable_seats,
        'billing_enforced': False,
        'warning': 'Seat allocation updated without billing alignment'
    })


@saas_bp.route('/api/v1/saas/billing/upgrade', methods=['POST'])
def billing_upgrade():
    """Plan upgrade - price override vulnerability"""
    data = request.get_json() or {}
    plan_id = data.get('plan_id', 'enterprise')
    price_override = data.get('price_override')

    return jsonify({
        'plan_id': plan_id,
        'price_override': price_override,
        'upgraded': True,
        'warning': 'Plan upgraded without payment verification'
    })


# ============================================================================
# ADMIN & AUDIT LOGS
# ============================================================================

@saas_bp.route('/api/v1/saas/audit/logs')
def saas_audit_logs():
    """Audit log export - sensitive data exposure"""
    limit = int(request.args.get('limit', 1000))
    include_sensitive = request.args.get('include_sensitive', 'false').lower() == 'true'

    logs = []
    for i in range(min(limit, 25)):
        logs.append({
            'log_id': f'LOG-{uuid.uuid4().hex[:8]}',
            'actor': 'admin',
            'action': 'config_change',
            'sensitive': include_sensitive,
            'timestamp': datetime.now().isoformat()
        })

    return jsonify({
        'logs': logs,
        'include_sensitive': include_sensitive,
        'warning': 'Audit logs exported without authorization'
    })


@saas_bp.route('/api/v1/saas/audit/logs/<log_id>', methods=['PUT'])
def saas_audit_log_tamper(log_id):
    """Audit log tampering"""
    data = request.get_json() or {}
    saas_audit_logs_db[log_id] = {
        'log_id': log_id,
        'action': data.get('action', 'delete'),
        'bypass_audit': data.get('bypass_audit', False),
        'updated_at': datetime.now().isoformat()
    }

    return jsonify({
        'log_id': log_id,
        'status': 'modified',
        'warning': 'Audit log updated without integrity checks'
    })


@saas_bp.route('/api/v1/saas/audit/retention', methods=['PUT'])
def saas_retention_policy():
    """Retention policy override"""
    data = request.get_json() or {}
    return jsonify({
        'retention_days': data.get('retention_days', 0),
        'override_controls': data.get('override_controls', False),
        'warning': 'Retention policy changed without approval'
    })


# ============================================================================
# SCIM & PROVISIONING
# ============================================================================

@saas_bp.route('/api/v1/saas/scim/users', methods=['POST'])
def scim_user_create():
    """SCIM user creation - provisioning abuse"""
    data = request.get_json() or {}
    user_id = f'SCIM-{uuid.uuid4().hex[:8]}'
    saas_scim_users_db[user_id] = {
        'user_id': user_id,
        'user_name': data.get('user_name'),
        'role': data.get('role', 'member'),
        'bypass_approval': data.get('bypass_approval', False)
    }
    return jsonify({
        'user_id': user_id,
        'warning': 'User provisioned without approval'
    }), 201


@saas_bp.route('/api/v1/saas/scim/users/<user_id>', methods=['DELETE'])
def scim_user_delete(user_id):
    """SCIM user deletion - destructive action without review"""
    saas_scim_users_db.pop(user_id, None)
    return jsonify({
        'user_id': user_id,
        'deleted': True,
        'warning': 'User deleted without authorization'
    })


@saas_bp.route('/api/v1/saas/scim/groups/sync', methods=['POST'])
def scim_groups_sync():
    """Group sync - bypass checks"""
    data = request.get_json() or {}
    group_id = data.get('group_id', f'group-{uuid.uuid4().hex[:6]}')
    saas_scim_groups_db[group_id] = {
        'group_id': group_id,
        'force_sync': data.get('force_sync', False),
        'synced_at': datetime.now().isoformat()
    }
    return jsonify({
        'group_id': group_id,
        'warning': 'Group sync performed without validation'
    })


# ============================================================================
# API KEYS & TOKENS
# ============================================================================

@saas_bp.route('/api/v1/saas/api-keys', methods=['POST'])
def api_keys_create():
    """API key creation - excessive scopes"""
    data = request.get_json() or {}
    key_id = f'KEY-{uuid.uuid4().hex[:8]}'
    saas_api_keys_db[key_id] = {
        'key_id': key_id,
        'label': data.get('label', 'integration'),
        'scopes': data.get('scopes', []),
        'bypass_approval': data.get('bypass_approval', False),
        'secret': f'secret-{uuid.uuid4().hex[:12]}'
    }
    return jsonify({
        'key_id': key_id,
        'warning': 'API key created without approval'
    }), 201


@saas_bp.route('/api/v1/saas/api-keys/export')
def api_keys_export():
    """API key export - secret exposure"""
    include_secrets = request.args.get('include_secrets', 'false').lower() == 'true'
    keys = []
    for key in saas_api_keys_db.values():
        payload = dict(key)
        if not include_secrets:
            payload.pop('secret', None)
        keys.append(payload)
    return jsonify({
        'keys': keys,
        'include_secrets': include_secrets,
        'warning': 'API keys exported without authorization'
    })


@saas_bp.route('/api/v1/saas/api-keys/rotate', methods=['PUT'])
def api_keys_rotate():
    """API key rotation - forced rotate without validation"""
    data = request.get_json() or {}
    key_id = data.get('key_id')
    key = saas_api_keys_db.get(key_id, {'key_id': key_id})
    key['secret'] = f'secret-{uuid.uuid4().hex[:12]}'
    key['rotated_at'] = datetime.now().isoformat()
    saas_api_keys_db[key_id] = key
    return jsonify({
        'key_id': key_id,
        'warning': 'API key rotated without verification'
    })


# ============================================================================
# WEBHOOKS & INTEGRATIONS
# ============================================================================

@saas_bp.route('/api/v1/saas/webhooks/register', methods=['POST'])
def webhook_register():
    """Webhook registration - SSRF risk"""
    data = request.get_json() or {}
    hook_id = f'HOOK-{uuid.uuid4().hex[:8]}'
    saas_webhooks_db[hook_id] = {
        'hook_id': hook_id,
        'url': data.get('url'),
        'events': data.get('events', []),
        'bypass_validation': data.get('bypass_validation', False)
    }
    return jsonify({
        'hook_id': hook_id,
        'warning': 'Webhook registered without validation'
    }), 201


@saas_bp.route('/api/v1/saas/webhooks/secret', methods=['PUT'])
def webhook_secret_rotate():
    """Webhook secret override"""
    data = request.get_json() or {}
    hook_id = data.get('webhook_id')
    hook = saas_webhooks_db.get(hook_id, {'hook_id': hook_id})
    hook['secret'] = data.get('secret')
    hook['updated_at'] = datetime.now().isoformat()
    saas_webhooks_db[hook_id] = hook
    return jsonify({
        'hook_id': hook_id,
        'warning': 'Webhook secret updated without authorization'
    })


@saas_bp.route('/api/v1/saas/webhooks/replay', methods=['POST'])
def webhook_replay():
    """Webhook replay - event injection"""
    data = request.get_json() or {}
    return jsonify({
        'webhook_id': data.get('webhook_id'),
        'event_id': data.get('event_id'),
        'force_replay': data.get('force_replay', False),
        'warning': 'Webhook event replayed without validation'
    })
