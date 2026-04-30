"""Focused tests for Apparatus integration routes."""

from __future__ import annotations

import pytest

from app.services import (
    ApparatusServiceConfigError,
    ApparatusServiceDisabledError,
    ApparatusServiceNetworkError,
    ApparatusServiceUpstreamError,
)


class StubService:
    """Minimal service stub for route-level success-path tests."""

    def __init__(self, *, status=None, history=None, start=None, stop=None, exc=None):
        self._status = status
        self._history = history
        self._start = start
        self._stop = stop
        self._exc = exc
        self.calls = []

    def _maybe_raise(self):
        if self._exc is not None:
            raise self._exc

    def get_status(self):
        self.calls.append(('status', None))
        self._maybe_raise()
        return self._status

    def get_history(self, limit=None):
        self.calls.append(('history', limit))
        self._maybe_raise()
        return self._history

    def start_ghosts(self, payload):
        self.calls.append(('start', payload))
        self._maybe_raise()
        return self._start

    def stop_ghosts(self):
        self.calls.append(('stop', None))
        self._maybe_raise()
        return self._stop


@pytest.fixture
def apparatus_app(app, monkeypatch):
    """Configure Apparatus integration settings on the ASGI factory.

    The Apparatus service reads from ``app_config`` (the framework-agnostic
    singleton) post task-16.8; tests override the relevant attributes
    directly via monkeypatch so the changes don't leak between tests.
    """
    from app.config import app_config

    monkeypatch.setattr(app_config, 'apparatus_enabled', True)
    monkeypatch.setattr(app_config, 'apparatus_base_url', 'http://apparatus.local')
    monkeypatch.setattr(app_config, 'apparatus_timeout_ms', 5000)
    return app


@pytest.fixture
def apparatus_client(apparatus_app):
    from starlette.testclient import TestClient

    with TestClient(
        apparatus_app,
        client=("127.0.0.1", 50000),
        raise_server_exceptions=False,
    ) as client:
        yield client


def test_apparatus_status_returns_disabled_payload(apparatus_app, apparatus_client):
    from app.config import app_config
    app_config.apparatus_enabled = False

    response = apparatus_client.get('/api/v1/integrations/apparatus/status')

    assert response.status_code == 200
    assert response.json() == {
        'enabled': False,
        'configured': True,
        'reachable': False,
        'baseUrl': 'http://apparatus.local',
        'health': None,
        'ghosts': None,
        'error': 'apparatus_disabled',
        'message': 'Apparatus integration is disabled.',
    }


def test_apparatus_status_returns_config_error_payload(apparatus_app, apparatus_client):
    from app.config import app_config
    app_config.apparatus_base_url = ''

    response = apparatus_client.get('/api/v1/integrations/apparatus/status')

    assert response.status_code == 200
    assert response.json() == {
        'enabled': True,
        'configured': False,
        'reachable': False,
        'baseUrl': '',
        'health': None,
        'ghosts': None,
        'error': 'apparatus_config_error',
        'message': 'APPARATUS_BASE_URL must be configured when Apparatus is enabled.',
    }


def test_apparatus_status_returns_success_payload(apparatus_client, monkeypatch):
    service = StubService(status={
        'enabled': True,
        'configured': True,
        'reachable': True,
        'baseUrl': 'http://apparatus.local',
        'health': {'status': 'ok'},
        'ghosts': {'running': False},
    })
    monkeypatch.setattr(
        'app.blueprints.integrations.routes._get_apparatus_service',
        lambda: service,
    )

    response = apparatus_client.get('/api/v1/integrations/apparatus/status')

    assert response.status_code == 200
    assert response.json()['health'] == {'status': 'ok'}
    assert service.calls == [('status', None)]


def test_apparatus_status_returns_unreachable_payload(apparatus_client, monkeypatch):
    monkeypatch.setattr(
        'app.blueprints.integrations.routes._get_apparatus_service',
        lambda: StubService(exc=ApparatusServiceNetworkError('network down')),
    )

    response = apparatus_client.get('/api/v1/integrations/apparatus/status')

    assert response.status_code == 200
    payload = response.json()
    assert payload['reachable'] is False
    assert payload['error'] == 'apparatus_network_error'
    assert payload['message'] == 'network down'


def test_apparatus_history_returns_bounded_response(apparatus_client, monkeypatch):
    service = StubService(history={
        'count': 2,
        'entries': [{'id': '1'}, {'id': '2'}],
    })
    monkeypatch.setattr(
        'app.blueprints.integrations.routes._get_apparatus_service',
        lambda: service,
    )

    response = apparatus_client.get('/api/v1/integrations/apparatus/history?limit=2')

    assert response.status_code == 200
    assert response.json() == {
        'count': 2,
        'entries': [{'id': '1'}, {'id': '2'}],
    }
    assert service.calls == [('history', 2)]


def test_apparatus_history_defaults_invalid_limit(apparatus_client, monkeypatch):
    service = StubService(history={'count': 0, 'entries': []})
    monkeypatch.setattr(
        'app.blueprints.integrations.routes._get_apparatus_service',
        lambda: service,
    )

    response = apparatus_client.get('/api/v1/integrations/apparatus/history?limit=-1')

    assert response.status_code == 200
    assert service.calls == [('history', 50)]


def test_apparatus_history_defaults_zero_limit(apparatus_client, monkeypatch):
    service = StubService(history={'count': 0, 'entries': []})
    monkeypatch.setattr(
        'app.blueprints.integrations.routes._get_apparatus_service',
        lambda: service,
    )

    response = apparatus_client.get('/api/v1/integrations/apparatus/history?limit=0')

    assert response.status_code == 200
    assert service.calls == [('history', 50)]


def test_apparatus_history_caps_large_limit(apparatus_client, monkeypatch):
    service = StubService(history={'count': 0, 'entries': []})
    monkeypatch.setattr(
        'app.blueprints.integrations.routes._get_apparatus_service',
        lambda: service,
    )

    response = apparatus_client.get('/api/v1/integrations/apparatus/history?limit=9999')

    assert response.status_code == 200
    assert service.calls == [('history', 500)]


def test_apparatus_history_returns_structured_disabled_error(apparatus_client, monkeypatch):
    monkeypatch.setattr(
        'app.blueprints.integrations.routes._get_apparatus_service',
        lambda: StubService(exc=ApparatusServiceDisabledError('disabled now')),
    )

    response = apparatus_client.get('/api/v1/integrations/apparatus/history')

    assert response.status_code == 503
    assert response.json() == {
        'error': 'apparatus_disabled',
        'message': 'disabled now',
    }


def test_apparatus_history_returns_structured_config_error(apparatus_client, monkeypatch):
    monkeypatch.setattr(
        'app.blueprints.integrations.routes._get_apparatus_service',
        lambda: StubService(exc=ApparatusServiceConfigError('config missing')),
    )

    response = apparatus_client.get('/api/v1/integrations/apparatus/history')

    assert response.status_code == 500
    assert response.json() == {
        'error': 'apparatus_config_error',
        'message': 'config missing',
    }


def test_apparatus_history_returns_structured_upstream_error(apparatus_client, monkeypatch):
    monkeypatch.setattr(
        'app.blueprints.integrations.routes._get_apparatus_service',
        lambda: StubService(exc=ApparatusServiceUpstreamError('bad upstream', 503, {'error': 'bad'})),
    )

    response = apparatus_client.get('/api/v1/integrations/apparatus/history')

    assert response.status_code == 502
    assert response.json() == {
        'error': 'apparatus_upstream_error',
        'message': 'bad upstream',
        'status_code': 503,
        'body': {'error': 'bad'},
    }


def test_apparatus_ghosts_start_proxies_payload(apparatus_client, monkeypatch):
    service = StubService(start={'running': True, 'rps': 8})
    monkeypatch.setattr(
        'app.blueprints.integrations.routes._get_apparatus_service',
        lambda: service,
    )

    response = apparatus_client.post('/api/v1/integrations/apparatus/ghosts/start', json={
        'rps': 8,
        'duration': 30000,
    })

    assert response.status_code == 200
    assert response.json() == {'running': True, 'rps': 8}
    assert service.calls == [('start', {'rps': 8, 'duration': 30000})]


def test_apparatus_ghosts_start_rejects_non_object_payload(apparatus_client, monkeypatch):
    service = StubService(start={'running': True})
    monkeypatch.setattr(
        'app.blueprints.integrations.routes._get_apparatus_service',
        lambda: service,
    )

    response = apparatus_client.post('/api/v1/integrations/apparatus/ghosts/start', json=['unexpected'])

    assert response.status_code == 400
    assert response.json() == {
        'error': 'apparatus_validation_error',
        'message': 'Ghost start payload must be a JSON object.',
    }
    assert service.calls == []


def test_apparatus_ghosts_start_rejects_unknown_fields(apparatus_client, monkeypatch):
    service = StubService(start={'running': True})
    monkeypatch.setattr(
        'app.blueprints.integrations.routes._get_apparatus_service',
        lambda: service,
    )

    response = apparatus_client.post('/api/v1/integrations/apparatus/ghosts/start', json={'rps': 8, 'mode': 'burst'})

    assert response.status_code == 400
    assert response.json() == {
        'error': 'apparatus_validation_error',
        'message': 'Unsupported ghost start fields: mode.',
    }
    assert service.calls == []


def test_apparatus_ghosts_stop_proxies_response(apparatus_client, monkeypatch):
    service = StubService(stop={'running': False})
    monkeypatch.setattr(
        'app.blueprints.integrations.routes._get_apparatus_service',
        lambda: service,
    )

    response = apparatus_client.post('/api/v1/integrations/apparatus/ghosts/stop')

    assert response.status_code == 200
    assert response.json() == {'running': False}
    assert service.calls == [('stop', None)]


def test_apparatus_ghost_routes_return_network_error(apparatus_client, monkeypatch):
    monkeypatch.setattr(
        'app.blueprints.integrations.routes._get_apparatus_service',
        lambda: StubService(exc=ApparatusServiceNetworkError('timed out')),
    )

    start_response = apparatus_client.post('/api/v1/integrations/apparatus/ghosts/start', json={'rps': 3})
    stop_response = apparatus_client.post('/api/v1/integrations/apparatus/ghosts/stop')

    assert start_response.status_code == 502
    assert stop_response.status_code == 502
    assert start_response.json() == {
        'error': 'apparatus_network_error',
        'message': 'timed out',
    }
