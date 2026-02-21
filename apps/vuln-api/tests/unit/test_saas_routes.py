"""Unit tests for SaaS routes."""


def test_tenant_projects_idor(client):
    response = client.get('/api/v1/saas/tenants/tenant-1/projects')
    assert response.status_code == 200
    data = response.get_json()
    assert data['tenant_id'] == 'tenant-1'
    assert isinstance(data['projects'], list)


def test_sso_callback_tampered(client):
    response = client.post(
        '/api/v1/saas/auth/sso/callback',
        json={'assertion': 'tampered_saml_assertion', 'force_admin': True}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['role'] == 'owner'


def test_billing_usage_overflow(client):
    response = client.post(
        '/api/v1/saas/billing/usage',
        json={'usage_units': 9999999, 'plan_id': 'free', 'bypass_limits': True}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['billable_units'] == 0


def test_org_invite_bypass(client):
    response = client.post(
        '/api/v1/saas/org/invites',
        json={'email': 'attacker@evil.com', 'role': 'owner', 'tenant_id': 'tenant-1', 'bypass_approval': True}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['invite']['bypass_approval'] is True


def test_saml_config_tamper(client):
    response = client.put(
        '/api/v1/saas/auth/saml/config',
        json={'tenant_id': 'tenant-1', 'entity_id': 'urn:evil:saml', 'bypass_validation': True}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['config']['bypass_validation'] is True


def test_session_revoke_abuse(client):
    response = client.post(
        '/api/v1/saas/sessions/revoke',
        json={'session_id': 'sess-123', 'force_revoke': True}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['session_id'] == 'sess-123'
