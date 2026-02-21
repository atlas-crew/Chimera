"""
Unit tests for response helper utilities.

Tests cover:
- Success responses
- Error responses (400, 401, 403, 404, 500)
- Paginated responses
- Response formatting consistency
- HTTP status codes and headers
"""

import pytest
import json
from datetime import datetime
from app.utils.responses import (
    success_response,
    error_response,
    validation_error_response,
    not_found_response,
    unauthorized_response,
    forbidden_response,
    conflict_response,
    too_many_requests_response,
    internal_server_error_response,
    created_response,
    accepted_response,
    no_content_response,
    paginated_response,
    build_api_envelope
)


class TestSuccessResponse:
    """Test success response helper."""

    def test_success_response_basic(self, app):
        """Test basic success response structure."""
        with app.app_context():
            response, status_code = success_response()

            assert status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'timestamp' in data

    def test_success_response_with_data(self, app):
        """Test success response with data payload."""
        with app.app_context():
            test_data = {'user_id': '123', 'name': 'Alice'}
            response, status_code = success_response(data=test_data)

            data = response.get_json()
            assert data['success'] is True
            assert data['data'] == test_data

    def test_success_response_with_message(self, app):
        """Test success response with message."""
        with app.app_context():
            response, status_code = success_response(message='Operation completed')

            data = response.get_json()
            assert data['message'] == 'Operation completed'

    def test_success_response_custom_status_code(self, app):
        """Test success response with custom status code."""
        with app.app_context():
            response, status_code = success_response(status_code=201)

            assert status_code == 201

    def test_success_response_with_metadata(self, app):
        """Test success response with metadata."""
        with app.app_context():
            metadata = {'request_id': 'req_123', 'version': '1.0'}
            response, status_code = success_response(metadata=metadata)

            data = response.get_json()
            assert data['metadata'] == metadata

    def test_success_response_with_headers(self, app):
        """Test success response with custom headers."""
        with app.app_context():
            headers = {'X-Custom-Header': 'value'}
            response, status_code = success_response(headers=headers)

            assert response.headers.get('X-Custom-Header') == 'value'


class TestErrorResponse:
    """Test error response helper."""

    def test_error_response_basic(self, app):
        """Test basic error response structure."""
        with app.app_context():
            response, status_code = error_response('Error occurred')

            assert status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert data['error']['message'] == 'Error occurred'
            assert data['error']['code'] == 'ERROR'

    def test_error_response_custom_code(self, app):
        """Test error response with custom error code."""
        with app.app_context():
            response, status_code = error_response(
                'Validation failed',
                code='VALIDATION_ERROR'
            )

            data = response.get_json()
            assert data['error']['code'] == 'VALIDATION_ERROR'

    def test_error_response_with_details(self, app):
        """Test error response with details."""
        with app.app_context():
            details = {'field': 'email', 'issue': 'invalid format'}
            response, status_code = error_response(
                'Validation failed',
                details=details
            )

            data = response.get_json()
            assert data['error']['details'] == details

    def test_error_response_includes_status_text(self, app):
        """Test error response includes HTTP status text."""
        with app.app_context():
            response, status_code = error_response('Not found', status_code=404)

            data = response.get_json()
            assert data['error']['status'] == 'Not Found'

    def test_error_response_with_headers(self, app):
        """Test error response with custom headers."""
        with app.app_context():
            headers = {'X-Error-ID': 'err_123'}
            response, status_code = error_response('Error', headers=headers)

            assert response.headers.get('X-Error-ID') == 'err_123'


class TestValidationErrorResponse:
    """Test validation error response helper."""

    def test_validation_error_response_dict(self, app):
        """Test validation error with field-level errors dict."""
        with app.app_context():
            errors = {'email': 'Invalid format', 'password': 'Too short'}
            response, status_code = validation_error_response(errors)

            assert status_code == 400
            data = response.get_json()
            assert data['error']['code'] == 'VALIDATION_ERROR'
            assert data['error']['details']['validation_errors'] == errors

    def test_validation_error_response_list(self, app):
        """Test validation error with list of errors."""
        with app.app_context():
            errors = [
                {'field': 'email', 'message': 'Invalid'},
                {'field': 'password', 'message': 'Too short'}
            ]
            response, status_code = validation_error_response(errors)

            data = response.get_json()
            assert data['error']['details']['validation_errors'] == errors

    def test_validation_error_response_custom_message(self, app):
        """Test validation error with custom message."""
        with app.app_context():
            response, status_code = validation_error_response(
                errors={},
                message='Custom validation message'
            )

            data = response.get_json()
            assert data['error']['message'] == 'Custom validation message'


class TestNotFoundResponse:
    """Test 404 Not Found response helper."""

    def test_not_found_response_basic(self, app):
        """Test basic not found response."""
        with app.app_context():
            response, status_code = not_found_response()

            assert status_code == 404
            data = response.get_json()
            assert data['error']['code'] == 'NOT_FOUND'
            assert 'Resource not found' in data['error']['message']

    def test_not_found_response_with_resource_type(self, app):
        """Test not found with resource type."""
        with app.app_context():
            response, status_code = not_found_response('User')

            data = response.get_json()
            assert 'User not found' in data['error']['message']

    def test_not_found_response_with_resource_id(self, app):
        """Test not found with resource type and ID."""
        with app.app_context():
            response, status_code = not_found_response('User', resource_id='123')

            data = response.get_json()
            assert "User with ID '123' not found" in data['error']['message']


class TestUnauthorizedResponse:
    """Test 401 Unauthorized response helper."""

    def test_unauthorized_response_basic(self, app):
        """Test basic unauthorized response."""
        with app.app_context():
            response, status_code = unauthorized_response()

            assert status_code == 401
            data = response.get_json()
            assert data['error']['code'] == 'UNAUTHORIZED'
            assert 'Authentication required' in data['error']['message']
            assert response.headers.get('WWW-Authenticate') == 'Bearer'

    def test_unauthorized_response_custom_message(self, app):
        """Test unauthorized with custom message."""
        with app.app_context():
            response, status_code = unauthorized_response(
                message='Invalid token',
                code='INVALID_TOKEN'
            )

            data = response.get_json()
            assert data['error']['message'] == 'Invalid token'
            assert data['error']['code'] == 'INVALID_TOKEN'


class TestForbiddenResponse:
    """Test 403 Forbidden response helper."""

    def test_forbidden_response_basic(self, app):
        """Test basic forbidden response."""
        with app.app_context():
            response, status_code = forbidden_response()

            assert status_code == 403
            data = response.get_json()
            assert data['error']['code'] == 'FORBIDDEN'
            assert 'Access denied' in data['error']['message']

    def test_forbidden_response_custom_message(self, app):
        """Test forbidden with custom message."""
        with app.app_context():
            response, status_code = forbidden_response(
                message='Insufficient permissions',
                code='INSUFFICIENT_PERMS'
            )

            data = response.get_json()
            assert data['error']['message'] == 'Insufficient permissions'
            assert data['error']['code'] == 'INSUFFICIENT_PERMS'


class TestConflictResponse:
    """Test 409 Conflict response helper."""

    def test_conflict_response_basic(self, app):
        """Test basic conflict response."""
        with app.app_context():
            response, status_code = conflict_response('Resource already exists')

            assert status_code == 409
            data = response.get_json()
            assert data['error']['code'] == 'CONFLICT'
            assert data['error']['message'] == 'Resource already exists'

    def test_conflict_response_with_resource(self, app):
        """Test conflict with resource type."""
        with app.app_context():
            response, status_code = conflict_response(
                'Email already registered',
                resource='User'
            )

            data = response.get_json()
            assert data['error']['details']['resource'] == 'User'

    def test_conflict_response_with_details(self, app):
        """Test conflict with additional details."""
        with app.app_context():
            response, status_code = conflict_response(
                'Email exists',
                details={'email': 'user@example.com'}
            )

            data = response.get_json()
            assert data['error']['details']['email'] == 'user@example.com'


class TestTooManyRequestsResponse:
    """Test 429 Too Many Requests response helper."""

    def test_too_many_requests_response_basic(self, app):
        """Test basic rate limit response."""
        with app.app_context():
            response, status_code = too_many_requests_response()

            assert status_code == 429
            data = response.get_json()
            assert data['error']['code'] == 'RATE_LIMIT_EXCEEDED'

    def test_too_many_requests_response_with_retry_after(self, app):
        """Test rate limit with retry-after header."""
        with app.app_context():
            response, status_code = too_many_requests_response(
                retry_after=60
            )

            assert response.headers.get('Retry-After') == '60'
            data = response.get_json()
            assert data['error']['details']['retry_after'] == 60


class TestInternalServerErrorResponse:
    """Test 500 Internal Server Error response helper."""

    def test_internal_server_error_basic(self, app):
        """Test basic internal server error response."""
        with app.app_context():
            response, status_code = internal_server_error_response()

            assert status_code == 500
            data = response.get_json()
            assert data['error']['code'] == 'INTERNAL_ERROR'

    def test_internal_server_error_with_error_id(self, app):
        """Test internal error with tracking ID."""
        with app.app_context():
            response, status_code = internal_server_error_response(
                error_id='ERR-2024-001'
            )

            data = response.get_json()
            assert 'ERR-2024-001' in data['error']['message']
            assert data['error']['details']['error_id'] == 'ERR-2024-001'

    def test_internal_server_error_with_details(self, app):
        """Test internal error with details in dev mode."""
        with app.app_context():
            response, status_code = internal_server_error_response(
                include_details=True,
                details={'exception': 'ValueError: test'}
            )

            data = response.get_json()
            assert 'exception' in data['error']['details']

    def test_internal_server_error_hides_details_production(self, app):
        """Test internal error hides details in production."""
        with app.app_context():
            response, status_code = internal_server_error_response(
                include_details=False,
                details={'sensitive': 'data'}
            )

            data = response.get_json()
            # Should not include details when include_details=False
            assert data['error'].get('details') is None or 'sensitive' not in data['error'].get('details', {})


class TestCreatedResponse:
    """Test 201 Created response helper."""

    def test_created_response_basic(self, app):
        """Test basic created response."""
        with app.app_context():
            data_obj = {'user_id': '123', 'email': 'user@example.com'}
            response, status_code = created_response(data_obj)

            assert status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert data['data'] == data_obj

    def test_created_response_with_location(self, app):
        """Test created response with Location header."""
        with app.app_context():
            response, status_code = created_response(
                data={'user_id': '123'},
                resource_url='/api/users/123'
            )

            assert response.headers.get('Location') == '/api/users/123'

    def test_created_response_with_message(self, app):
        """Test created response with message."""
        with app.app_context():
            response, status_code = created_response(
                data={'user_id': '123'},
                message='User created successfully'
            )

            data = response.get_json()
            assert data['message'] == 'User created successfully'


class TestAcceptedResponse:
    """Test 202 Accepted response helper."""

    def test_accepted_response_basic(self, app):
        """Test basic accepted response."""
        with app.app_context():
            response, status_code = accepted_response()

            assert status_code == 202
            data = response.get_json()
            assert data['success'] is True

    def test_accepted_response_with_job_id(self, app):
        """Test accepted response with job ID."""
        with app.app_context():
            response, status_code = accepted_response(
                job_id='job-123',
                status_url='/api/jobs/job-123'
            )

            data = response.get_json()
            assert data['data']['job_id'] == 'job-123'
            assert data['data']['status_url'] == '/api/jobs/job-123'
            assert response.headers.get('Location') == '/api/jobs/job-123'


class TestNoContentResponse:
    """Test 204 No Content response helper."""

    def test_no_content_response(self, app):
        """Test no content response."""
        with app.app_context():
            response, status_code = no_content_response()

            assert status_code == 204


class TestPaginatedResponse:
    """Test paginated response helper."""

    def test_paginated_response_basic(self, app):
        """Test basic paginated response."""
        with app.app_context():
            items = [{'id': 1}, {'id': 2}, {'id': 3}]
            response, status_code = paginated_response(
                items=items,
                page=1,
                per_page=3,
                total_items=10
            )

            data = response.get_json()
            assert data['success'] is True
            assert data['data'] == items
            assert 'pagination' in data['metadata']

    def test_paginated_response_metadata(self, app):
        """Test paginated response includes correct metadata."""
        with app.app_context():
            response, status_code = paginated_response(
                items=[],
                page=2,
                per_page=10,
                total_items=45
            )

            data = response.get_json()
            pagination = data['metadata']['pagination']

            assert pagination['page'] == 2
            assert pagination['per_page'] == 10
            assert pagination['total_items'] == 45
            assert pagination['total_pages'] == 5
            assert pagination['has_next'] is True
            assert pagination['has_prev'] is True

    def test_paginated_response_first_page(self, app):
        """Test pagination metadata for first page."""
        with app.app_context():
            response, status_code = paginated_response(
                items=[],
                page=1,
                per_page=10,
                total_items=30
            )

            data = response.get_json()
            pagination = data['metadata']['pagination']

            assert pagination['has_prev'] is False
            assert pagination['has_next'] is True

    def test_paginated_response_last_page(self, app):
        """Test pagination metadata for last page."""
        with app.app_context():
            response, status_code = paginated_response(
                items=[],
                page=3,
                per_page=10,
                total_items=30
            )

            data = response.get_json()
            pagination = data['metadata']['pagination']

            assert pagination['has_prev'] is True
            assert pagination['has_next'] is False

    def test_paginated_response_total_pages_calculation(self, app):
        """Test total pages calculation with ceiling division."""
        with app.app_context():
            # 45 items / 10 per page = 5 pages (ceiling)
            response, status_code = paginated_response(
                items=[],
                page=1,
                per_page=10,
                total_items=45
            )

            data = response.get_json()
            assert data['metadata']['pagination']['total_pages'] == 5


class TestBuildAPIEnvelope:
    """Test API envelope builder."""

    def test_build_api_envelope_success(self):
        """Test building success envelope."""
        envelope = build_api_envelope(
            data={'key': 'value'},
            success=True,
            message='Operation succeeded'
        )

        assert envelope['success'] is True
        assert envelope['data'] == {'key': 'value'}
        assert envelope['message'] == 'Operation succeeded'
        assert 'timestamp' in envelope

    def test_build_api_envelope_with_errors(self):
        """Test building envelope with errors."""
        envelope = build_api_envelope(
            data=None,
            success=False,
            errors=['Error 1', 'Error 2']
        )

        assert envelope['success'] is False
        assert envelope['errors'] == ['Error 1', 'Error 2']

    def test_build_api_envelope_with_warnings(self):
        """Test building envelope with warnings."""
        envelope = build_api_envelope(
            data={'result': 'partial'},
            success=True,
            warnings=['Warning: deprecated API']
        )

        assert envelope['success'] is True
        assert envelope['warnings'] == ['Warning: deprecated API']

    def test_build_api_envelope_minimal(self):
        """Test building minimal envelope."""
        envelope = build_api_envelope(data=None)

        assert envelope['success'] is True
        assert 'timestamp' in envelope
        assert 'data' not in envelope


class TestResponseConsistency:
    """Test response format consistency across helpers."""

    def test_all_responses_include_timestamp(self, app):
        """Test all response helpers include timestamp."""
        with app.app_context():
            responses = [
                success_response(),
                error_response('error'),
                not_found_response(),
                unauthorized_response(),
                forbidden_response()
            ]

            for response, _ in responses:
                data = response.get_json()
                # Success responses have timestamp at root
                # Error responses have timestamp in error object
                assert 'timestamp' in data or 'timestamp' in data.get('error', {})

    def test_success_responses_consistent_structure(self, app):
        """Test all success responses have consistent structure."""
        with app.app_context():
            responses = [
                success_response(),
                created_response(data={}),
                accepted_response()
            ]

            for response, _ in responses:
                data = response.get_json()
                assert 'success' in data
                assert data['success'] is True
                assert 'timestamp' in data

    def test_error_responses_consistent_structure(self, app):
        """Test all error responses have consistent structure."""
        with app.app_context():
            responses = [
                error_response('error'),
                not_found_response(),
                unauthorized_response(),
                forbidden_response(),
                conflict_response('conflict'),
                internal_server_error_response()
            ]

            for response, _ in responses:
                data = response.get_json()
                assert 'success' in data
                assert data['success'] is False
                assert 'error' in data
                assert 'message' in data['error']
                assert 'code' in data['error']
