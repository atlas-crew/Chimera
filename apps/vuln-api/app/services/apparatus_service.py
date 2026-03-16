"""Service wrapper for communicating with an external Apparatus instance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import requests
from flask import current_app


@dataclass(frozen=True)
class ApparatusSettings:
    """Normalized Apparatus connectivity settings."""

    enabled: bool
    base_url: str
    timeout_ms: int

    @property
    def timeout_seconds(self) -> float:
        return max(self.timeout_ms, 1) / 1000


class ApparatusServiceError(RuntimeError):
    """Base error for Apparatus integration failures."""

    error_code = 'apparatus_error'

    def to_dict(self) -> dict[str, Any]:
        return {
            'error': self.error_code,
            'message': str(self),
        }


class ApparatusServiceDisabledError(ApparatusServiceError):
    error_code = 'apparatus_disabled'


class ApparatusServiceConfigError(ApparatusServiceError):
    error_code = 'apparatus_config_error'


class ApparatusServiceNetworkError(ApparatusServiceError):
    error_code = 'apparatus_network_error'


class ApparatusServiceUpstreamError(ApparatusServiceError):
    error_code = 'apparatus_upstream_error'

    def __init__(self, message: str, status_code: int, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload['status_code'] = self.status_code
        if self.body is not None:
            payload['body'] = self.body
        return payload


def build_apparatus_settings(config: Mapping[str, Any] | None = None) -> ApparatusSettings:
    """Create normalized Apparatus settings from app config or a mapping."""

    source = config if config is not None else current_app.config
    base_url = str(source.get('APPARATUS_BASE_URL', '') or '').strip()
    timeout_ms = source.get('APPARATUS_TIMEOUT_MS', 5000)

    try:
        timeout_ms = int(timeout_ms)
    except (TypeError, ValueError):
        timeout_ms = 5000

    return ApparatusSettings(
        enabled=bool(source.get('APPARATUS_ENABLED', False)),
        base_url=base_url.rstrip('/'),
        timeout_ms=max(timeout_ms, 1),
    )


class ApparatusService:
    """Thin HTTP wrapper around the Apparatus API surface Chimera needs."""

    def __init__(
        self,
        settings: ApparatusSettings | None = None,
        session: Any | None = None,
    ):
        self.settings = settings or build_apparatus_settings()
        self.session = session or requests

    def get_status(self) -> dict[str, Any]:
        """Fetch top-level Apparatus status details for Chimera surfaces."""

        health = self._request_json('GET', '/healthz')
        ghosts = self._request_json('GET', '/ghosts')
        return {
            'enabled': True,
            'configured': True,
            'reachable': True,
            'baseUrl': self.settings.base_url,
            'health': health,
            'ghosts': ghosts,
        }

    def get_history(self, limit: int | None = None) -> dict[str, Any]:
        """Fetch recent Apparatus request history, with an optional local limit."""

        history = self._request_json('GET', '/history')
        if not isinstance(history, dict):
            raise ApparatusServiceUpstreamError(
                'Apparatus history response must be a JSON object.',
                status_code=502,
                body=history,
            )

        entries = history.get('entries', [])
        if not isinstance(entries, list):
            raise ApparatusServiceUpstreamError(
                'Apparatus history entries must be a list.',
                status_code=502,
                body=history,
            )

        if limit is not None and limit >= 0:
            entries = entries[:limit]

        return {
            'count': len(entries),
            'entries': entries,
        }

    def start_ghosts(self, payload: Mapping[str, Any] | None = None) -> Any:
        """Start Apparatus ghost traffic with the provided configuration."""

        return self._request_json('POST', '/ghosts/start', json=payload or {})

    def stop_ghosts(self) -> Any:
        """Stop Apparatus ghost traffic."""

        return self._request_json('POST', '/ghosts/stop')

    def _request_json(self, method: str, path: str, **kwargs: Any) -> Any:
        self._ensure_ready()

        url = f'{self.settings.base_url}{path}'
        timeout = kwargs.pop('timeout', self.settings.timeout_seconds)

        try:
            response = self.session.request(method, url, timeout=timeout, **kwargs)
        except requests.Timeout as exc:
            raise ApparatusServiceNetworkError(
                f'Apparatus request timed out for {method} {path}.'
            ) from exc
        except requests.RequestException as exc:
            raise ApparatusServiceNetworkError(
                f'Apparatus request failed for {method} {path}: {exc}'
            ) from exc

        body = self._parse_response_body(response)
        if not response.ok:
            raise ApparatusServiceUpstreamError(
                f'Apparatus returned {response.status_code} for {method} {path}.',
                status_code=response.status_code,
                body=body,
            )

        return body

    def _ensure_ready(self) -> None:
        if not self.settings.enabled:
            raise ApparatusServiceDisabledError(
                'Apparatus integration is disabled. Set APPARATUS_ENABLED=true to use this service.'
            )

        if not self.settings.base_url:
            raise ApparatusServiceConfigError(
                'APPARATUS_BASE_URL must be configured when the Apparatus integration is enabled.'
            )

    @staticmethod
    def _parse_response_body(response: Any) -> Any:
        content_type = (response.headers or {}).get('Content-Type', '')
        if 'application/json' in content_type.lower():
            return response.json()

        text = response.text
        if not text:
            return None
        return text
