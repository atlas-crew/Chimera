"""Unit tests for the Apparatus service wrapper."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
import requests
from flask import Flask

from app.services import (
    ApparatusService,
    ApparatusServiceConfigError,
    ApparatusServiceDisabledError,
    ApparatusServiceNetworkError,
    ApparatusServiceUpstreamError,
    build_apparatus_settings,
)


@dataclass
class FakeResponse:
    """Simple response stub for Apparatus service tests."""

    status_code: int
    payload: object = None
    text: str = ''
    headers: dict[str, str] | None = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self):
        return self.payload


class FakeSession:
    """Request stub that returns queued responses or raises queued errors."""

    def __init__(self, events):
        self.events = list(events)
        self.calls = []

    def request(self, method, url, timeout=None, **kwargs):
        self.calls.append({
            'method': method,
            'url': url,
            'timeout': timeout,
            'kwargs': kwargs,
        })
        event = self.events.pop(0)
        if isinstance(event, Exception):
            raise event
        return event


def test_build_apparatus_settings_uses_defaults():
    app = Flask(__name__)
    app.config['APPARATUS_ENABLED'] = False
    app.config['APPARATUS_BASE_URL'] = 'http://127.0.0.1:8090/'
    app.config['APPARATUS_TIMEOUT_MS'] = '2500'

    with app.app_context():
        settings = build_apparatus_settings()

    assert settings.enabled is False
    assert settings.base_url == 'http://127.0.0.1:8090'
    assert settings.timeout_ms == 2500
    assert settings.timeout_seconds == 2.5


def test_build_apparatus_settings_falls_back_for_invalid_timeout_value():
    settings = build_apparatus_settings({
        'APPARATUS_ENABLED': True,
        'APPARATUS_BASE_URL': 'http://127.0.0.1:8090/',
        'APPARATUS_TIMEOUT_MS': 'invalid',
    })

    assert settings.enabled is True
    assert settings.timeout_ms == 5000


def test_build_apparatus_settings_clamps_non_positive_timeout():
    settings = build_apparatus_settings({
        'APPARATUS_ENABLED': True,
        'APPARATUS_BASE_URL': 'http://127.0.0.1:8090/',
        'APPARATUS_TIMEOUT_MS': 0,
    })

    assert settings.timeout_ms == 1
    assert settings.timeout_seconds == 0.001


def test_get_status_returns_health_and_ghost_details():
    session = FakeSession([
        FakeResponse(200, payload={'status': 'ok'}, headers={'Content-Type': 'application/json'}),
        FakeResponse(200, payload={'running': False}, headers={'Content-Type': 'application/json'}),
    ])
    service = ApparatusService(
        settings=build_apparatus_settings({
            'APPARATUS_ENABLED': True,
            'APPARATUS_BASE_URL': 'http://apparatus.local',
            'APPARATUS_TIMEOUT_MS': 5000,
        }),
        session=session,
    )

    status = service.get_status()

    assert status == {
        'enabled': True,
        'configured': True,
        'reachable': True,
        'baseUrl': 'http://apparatus.local',
        'health': {'status': 'ok'},
        'ghosts': {'running': False},
    }
    assert session.calls[0]['url'] == 'http://apparatus.local/healthz'
    assert session.calls[1]['url'] == 'http://apparatus.local/ghosts'


def test_get_history_applies_limit():
    session = FakeSession([
        FakeResponse(
            200,
            payload={'count': 3, 'entries': [{'id': '1'}, {'id': '2'}, {'id': '3'}]},
            headers={'Content-Type': 'application/json'},
        ),
    ])
    service = ApparatusService(
        settings=build_apparatus_settings({
            'APPARATUS_ENABLED': True,
            'APPARATUS_BASE_URL': 'http://apparatus.local',
            'APPARATUS_TIMEOUT_MS': 5000,
        }),
        session=session,
    )

    history = service.get_history(limit=2)

    assert history == {
        'count': 2,
        'entries': [{'id': '1'}, {'id': '2'}],
    }


def test_service_raises_when_disabled():
    service = ApparatusService(
        settings=build_apparatus_settings({
            'APPARATUS_ENABLED': False,
            'APPARATUS_BASE_URL': 'http://apparatus.local',
            'APPARATUS_TIMEOUT_MS': 5000,
        }),
        session=FakeSession([]),
    )

    with pytest.raises(ApparatusServiceDisabledError, match='disabled'):
        service.get_status()


def test_service_raises_when_base_url_missing():
    service = ApparatusService(
        settings=build_apparatus_settings({
            'APPARATUS_ENABLED': True,
            'APPARATUS_BASE_URL': '',
            'APPARATUS_TIMEOUT_MS': 5000,
        }),
        session=FakeSession([]),
    )

    with pytest.raises(ApparatusServiceConfigError, match='APPARATUS_BASE_URL'):
        service.get_status()


def test_service_normalizes_timeout_errors():
    service = ApparatusService(
        settings=build_apparatus_settings({
            'APPARATUS_ENABLED': True,
            'APPARATUS_BASE_URL': 'http://apparatus.local',
            'APPARATUS_TIMEOUT_MS': 5000,
        }),
        session=FakeSession([requests.Timeout('timed out')]),
    )

    with pytest.raises(ApparatusServiceNetworkError, match='timed out'):
        service.get_status()


def test_service_normalizes_request_errors():
    service = ApparatusService(
        settings=build_apparatus_settings({
            'APPARATUS_ENABLED': True,
            'APPARATUS_BASE_URL': 'http://apparatus.local',
            'APPARATUS_TIMEOUT_MS': 5000,
        }),
        session=FakeSession([requests.ConnectionError('boom')]),
    )

    with pytest.raises(ApparatusServiceNetworkError, match='failed'):
        service.get_status()


def test_service_raises_on_upstream_error_response():
    service = ApparatusService(
        settings=build_apparatus_settings({
            'APPARATUS_ENABLED': True,
            'APPARATUS_BASE_URL': 'http://apparatus.local',
            'APPARATUS_TIMEOUT_MS': 5000,
        }),
        session=FakeSession([
            FakeResponse(
                503,
                payload={'error': 'unavailable'},
                headers={'Content-Type': 'application/json'},
            ),
        ]),
    )

    with pytest.raises(ApparatusServiceUpstreamError, match='returned 503') as exc_info:
        service.start_ghosts({'rps': 5})

    assert exc_info.value.status_code == 503
    assert exc_info.value.body == {'error': 'unavailable'}
