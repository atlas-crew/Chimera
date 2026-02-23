"""
Unit tests for input validation utilities.

Tests cover:
- Email validation (valid/invalid cases)
- String validation (length, characters)
- Integer/float validation
- Security checks (SQL injection, XSS, path traversal, command injection)
- Validation bypass for demo mode
- Request validation decorators
"""

import pytest
import re
from unittest.mock import Mock, patch
from app.utils.validators import (
    ValidationError,
    validate_email,
    validate_string,
    validate_integer,
    validate_float,
    check_sql_injection,
    check_xss,
    check_path_traversal,
    check_command_injection,
    sanitize_input,
    validate_required_fields,
    validate_json_request,
    validate_query_params,
    EMAIL_PATTERN,
    ALPHANUMERIC_PATTERN
)


class TestValidationError:
    """Test ValidationError exception class."""

    def test_validation_error_attributes(self):
        """Test ValidationError stores field, message, and code."""
        error = ValidationError('email', 'Invalid format', 'INVALID_FORMAT')

        assert error.field == 'email'
        assert error.message == 'Invalid format'
        assert error.code == 'INVALID_FORMAT'

    def test_validation_error_default_code(self):
        """Test ValidationError uses default code."""
        error = ValidationError('field', 'message')

        assert error.code == 'VALIDATION_ERROR'

    def test_validation_error_to_dict(self):
        """Test ValidationError converts to dictionary."""
        error = ValidationError('email', 'Invalid format', 'INVALID_FORMAT')

        result = error.to_dict()

        assert result == {
            'field': 'email',
            'message': 'Invalid format',
            'code': 'INVALID_FORMAT'
        }

    def test_validation_error_str_representation(self):
        """Test ValidationError string representation."""
        error = ValidationError('email', 'Invalid format')

        assert str(error) == 'Invalid format'


class TestEmailValidation:
    """Test email validation function."""

    @pytest.mark.parametrize('email', [
        'user@example.com',
        'test.user@example.com',
        'user+tag@example.com',
        'user_name@test-domain.com',
        'user123@example.co.uk',
        'a@b.co'
    ])
    def test_validate_email_valid_emails(self, email):
        """Test validation passes for valid email addresses."""
        assert validate_email(email) is True

    @pytest.mark.parametrize('email', [
        'invalid',
        '@example.com',
        'user@',
        'user @example.com',
        'user@.com',
        'user@example',
        ''
    ])
    def test_validate_email_invalid_emails(self, email):
        """Test validation fails for invalid email addresses."""
        with pytest.raises(ValidationError):
            validate_email(email)

    def test_validate_email_empty_required(self):
        """Test empty email fails when required."""
        with pytest.raises(ValidationError, match='required'):
            validate_email('', required=True)

    def test_validate_email_empty_not_required(self):
        """Test empty email passes when not required."""
        assert validate_email('', required=False) is True

    def test_validate_email_bypass(self):
        """Test bypass skips validation."""
        # Invalid email should pass with bypass=True
        assert validate_email('not-an-email', bypass=True) is True


class TestStringValidation:
    """Test string validation function."""

    def test_validate_string_valid(self):
        """Test validation passes for valid string."""
        assert validate_string('ValidString', 'name', min_length=3, max_length=50) is True

    def test_validate_string_too_short(self):
        """Test validation fails when string too short."""
        with pytest.raises(ValidationError, match='at least 5 characters'):
            validate_string('abc', 'name', min_length=5)

    def test_validate_string_too_long(self):
        """Test validation fails when string too long."""
        with pytest.raises(ValidationError, match='must not exceed 10 characters'):
            validate_string('a' * 20, 'name', max_length=10)

    def test_validate_string_pattern_match(self):
        """Test validation with pattern matching."""
        pattern = re.compile(r'^[a-z]+$')

        assert validate_string('lowercase', 'name', pattern=pattern) is True

        with pytest.raises(ValidationError, match='format is invalid'):
            validate_string('UPPERCASE', 'name', pattern=pattern)

    def test_validate_string_empty_required(self):
        """Test empty string fails when required."""
        with pytest.raises(ValidationError, match='required'):
            validate_string('', 'name', required=True)

    def test_validate_string_empty_not_required(self):
        """Test empty string passes when not required."""
        assert validate_string('', 'name', required=False) is True

    def test_validate_string_non_string_type(self):
        """Test validation fails for non-string types."""
        with pytest.raises(ValidationError, match='must be a string'):
            validate_string(123, 'name')

    def test_validate_string_bypass(self):
        """Test bypass skips all validation."""
        # Too long string should pass with bypass
        assert validate_string('a' * 1000, 'name', max_length=10, bypass=True) is True


class TestIntegerValidation:
    """Test integer validation function."""

    @pytest.mark.parametrize('value', [0, 1, -5, 100, 999999])
    def test_validate_integer_valid(self, value):
        """Test validation passes for valid integers."""
        assert validate_integer(value, 'count') is True

    @pytest.mark.parametrize('value', ['abc', 'twelve', None, [], {}])
    def test_validate_integer_invalid(self, value):
        """Test validation fails for invalid types."""
        if value is None:
            with pytest.raises(ValidationError, match='required'):
                validate_integer(value, 'count', required=True)
        else:
            with pytest.raises(ValidationError, match='must be an integer'):
                validate_integer(value, 'count')

    def test_validate_integer_string_convertible(self):
        """Test validation converts string to integer."""
        assert validate_integer('42', 'count') is True

    def test_validate_integer_min_value(self):
        """Test validation enforces minimum value."""
        assert validate_integer(10, 'count', min_value=5) is True

        with pytest.raises(ValidationError, match='at least 10'):
            validate_integer(5, 'count', min_value=10)

    def test_validate_integer_max_value(self):
        """Test validation enforces maximum value."""
        assert validate_integer(50, 'count', max_value=100) is True

        with pytest.raises(ValidationError, match='must not exceed 100'):
            validate_integer(150, 'count', max_value=100)

    def test_validate_integer_none_not_required(self):
        """Test None passes when not required."""
        assert validate_integer(None, 'count', required=False) is True

    def test_validate_integer_bypass(self):
        """Test bypass skips validation."""
        assert validate_integer('invalid', 'count', bypass=True) is True


class TestFloatValidation:
    """Test float validation function."""

    @pytest.mark.parametrize('value', [0.0, 1.5, -3.14, 999.99])
    def test_validate_float_valid(self, value):
        """Test validation passes for valid floats."""
        assert validate_float(value, 'price') is True

    @pytest.mark.parametrize('value', ['abc', 'twelve', None, [], {}])
    def test_validate_float_invalid(self, value):
        """Test validation fails for invalid types."""
        if value is None:
            with pytest.raises(ValidationError, match='required'):
                validate_float(value, 'price', required=True)
        else:
            with pytest.raises(ValidationError, match='must be a number'):
                validate_float(value, 'price')

    def test_validate_float_string_convertible(self):
        """Test validation converts string to float."""
        assert validate_float('3.14', 'price') is True

    def test_validate_float_min_value(self):
        """Test validation enforces minimum value."""
        assert validate_float(5.5, 'price', min_value=0.0) is True

        with pytest.raises(ValidationError, match='at least 10'):
            validate_float(5.0, 'price', min_value=10.0)

    def test_validate_float_max_value(self):
        """Test validation enforces maximum value."""
        assert validate_float(50.0, 'price', max_value=100.0) is True

        with pytest.raises(ValidationError, match='must not exceed 100'):
            validate_float(150.0, 'price', max_value=100.0)

    def test_validate_float_bypass(self):
        """Test bypass skips validation."""
        assert validate_float('invalid', 'price', bypass=True) is True


class TestSQLInjectionCheck:
    """Test SQL injection detection."""

    @pytest.mark.parametrize('payload', [
        "' OR '1'='1",
        "1' UNION SELECT * FROM users--",
        "admin'--",
        "1; DROP TABLE users;--",
        "SELECT * FROM",
        "INSERT INTO",
        "DELETE FROM",
        "/* comment */",
        "' OR 1=1--"
    ])
    def test_check_sql_injection_detects_attack(self, payload):
        """Test detection of SQL injection patterns."""
        with pytest.raises(ValidationError, match='dangerous content'):
            check_sql_injection(payload, 'input')

    @pytest.mark.parametrize('safe_input', [
        'normal text',
        'user@example.com',
        'John Doe',
        '123-456-7890',
        'Product: Widget-2000'
    ])
    def test_check_sql_injection_allows_safe(self, safe_input):
        """Test safe inputs pass validation."""
        assert check_sql_injection(safe_input, 'input') is True

    def test_check_sql_injection_empty_string(self):
        """Test empty string passes validation."""
        assert check_sql_injection('', 'input') is True

    def test_check_sql_injection_bypass(self):
        """Test bypass allows malicious input."""
        assert check_sql_injection("'; DROP TABLE users;--", 'input', bypass=True) is True


class TestXSSCheck:
    """Test XSS (Cross-Site Scripting) detection."""

    @pytest.mark.parametrize('payload', [
        '<script>alert("xss")</script>',
        'javascript:alert(1)',
        '<img src=x onerror=alert(1)>',
        '<iframe src="javascript:alert(1)"></iframe>',
        '<script>',
        'onerror=alert(1)',
        'onload=javascript:void(0)'
    ])
    def test_check_xss_detects_attack(self, payload):
        """Test detection of XSS patterns."""
        with pytest.raises(ValidationError, match='dangerous content'):
            check_xss(payload, 'input')

    @pytest.mark.parametrize('safe_input', [
        'normal text',
        'this is <strong>bold</strong> but script-free',
        'alert is just a word',
        'javascript as a word'
    ])
    def test_check_xss_allows_safe(self, safe_input):
        """Test safe inputs pass validation."""
        assert check_xss(safe_input, 'input') is True

    def test_check_xss_bypass(self):
        """Test bypass allows malicious input."""
        assert check_xss('<script>alert(1)</script>', 'input', bypass=True) is True


class TestPathTraversalCheck:
    """Test path traversal detection."""

    @pytest.mark.parametrize('payload', [
        '../../../etc/passwd',
        '..\\..\\windows\\system32',
        '%2e%2e%2fetc%2fpasswd',
        '/root/.ssh/id_rsa',
        '/etc/shadow',
        '..\\config\\database.yml'
    ])
    def test_check_path_traversal_detects_attack(self, payload):
        """Test detection of path traversal patterns."""
        with pytest.raises(ValidationError, match='invalid path characters'):
            check_path_traversal(payload, 'path')

    @pytest.mark.parametrize('safe_path', [
        'documents/file.txt',
        'images/photo.jpg',
        'data-2024-01-01.csv',
        'report_final.pdf'
    ])
    def test_check_path_traversal_allows_safe(self, safe_path):
        """Test safe paths pass validation."""
        assert check_path_traversal(safe_path, 'path') is True

    def test_check_path_traversal_bypass(self):
        """Test bypass allows malicious input."""
        assert check_path_traversal('../../../etc/passwd', 'path', bypass=True) is True


class TestCommandInjectionCheck:
    """Test command injection detection."""

    @pytest.mark.parametrize('payload', [
        '; ls -la',
        '| cat /etc/passwd',
        '`whoami`',
        '$(rm -rf /)',
        '&& echo pwned',
        '> /dev/null',
        '< input.txt',
        '{ echo test; }'
    ])
    def test_check_command_injection_detects_attack(self, payload):
        """Test detection of command injection patterns."""
        with pytest.raises(ValidationError, match='invalid characters'):
            check_command_injection(payload, 'command')

    @pytest.mark.parametrize('safe_input', [
        'normal text',
        'filename.txt',
        'user-input-123',
        'data_2024_01_01'
    ])
    def test_check_command_injection_allows_safe(self, safe_input):
        """Test safe inputs pass validation."""
        assert check_command_injection(safe_input, 'command') is True

    def test_check_command_injection_bypass(self):
        """Test bypass allows malicious input."""
        assert check_command_injection('; rm -rf /', 'command', bypass=True) is True


class TestSanitizeInput:
    """Test input sanitization function."""

    def test_sanitize_input_removes_unexpected_fields(self):
        """Test sanitization removes fields not in allowed list."""
        data = {
            'name': 'Alice',
            'email': 'alice@example.com',
            'admin': True,  # Should be removed
            'password': 'secret'  # Should be removed
        }
        allowed = ['name', 'email']

        result = sanitize_input(data, allowed)

        assert result == {'name': 'Alice', 'email': 'alice@example.com'}
        assert 'admin' not in result
        assert 'password' not in result

    def test_sanitize_input_keeps_allowed_fields(self):
        """Test sanitization keeps all allowed fields."""
        data = {'field1': 'value1', 'field2': 'value2'}
        allowed = ['field1', 'field2', 'field3']

        result = sanitize_input(data, allowed)

        assert result == {'field1': 'value1', 'field2': 'value2'}

    def test_sanitize_input_bypass(self):
        """Test bypass returns all fields."""
        data = {'allowed': 'yes', 'disallowed': 'no'}
        allowed = ['allowed']

        result = sanitize_input(data, allowed, bypass=True)

        assert result == data


class TestValidateRequiredFields:
    """Test required fields validation."""

    def test_validate_required_fields_all_present(self):
        """Test validation passes when all required fields present."""
        data = {'name': 'Alice', 'email': 'alice@example.com', 'age': 30}
        required = ['name', 'email']

        assert validate_required_fields(data, required) is True

    def test_validate_required_fields_missing_field(self):
        """Test validation fails when required field missing."""
        data = {'name': 'Alice'}
        required = ['name', 'email']

        with pytest.raises(ValidationError, match='email is required'):
            validate_required_fields(data, required)

    def test_validate_required_fields_none_value(self):
        """Test validation fails when required field is None."""
        data = {'name': 'Alice', 'email': None}
        required = ['name', 'email']

        with pytest.raises(ValidationError, match='email is required'):
            validate_required_fields(data, required)

    def test_validate_required_fields_empty_string(self):
        """Test validation fails when required field is empty string."""
        data = {'name': 'Alice', 'email': ''}
        required = ['name', 'email']

        with pytest.raises(ValidationError, match='email is required'):
            validate_required_fields(data, required)

    def test_validate_required_fields_bypass(self):
        """Test bypass skips validation."""
        data = {'name': 'Alice'}
        required = ['name', 'email', 'phone']

        assert validate_required_fields(data, required, bypass=True) is True


class TestValidateJSONRequestDecorator:
    """Test JSON request validation decorator."""

    def test_validate_json_request_valid(self, app):
        """Test decorator allows valid JSON request."""
        @app.route('/test', methods=['POST'])
        @validate_json_request(required_fields=['name', 'email'])
        def test_endpoint():
            return {'success': True}

        client = app.test_client()
        response = client.post(
            '/test',
            json={'name': 'Alice', 'email': 'alice@example.com'}
        )

        assert response.status_code == 200

    def test_validate_json_request_missing_content_type(self, app):
        """Test decorator rejects non-JSON content type."""
        @app.route('/test', methods=['POST'])
        @validate_json_request()
        def test_endpoint():
            return {'success': True}

        client = app.test_client()
        response = client.post('/test', data='not json')

        assert response.status_code == 400
        data = response.get_json()
        assert 'Content-Type must be application/json' in data['error']

    def test_validate_json_request_invalid_json(self, app):
        """Test decorator rejects invalid JSON."""
        @app.route('/test', methods=['POST'])
        @validate_json_request()
        def test_endpoint():
            return {'success': True}

        client = app.test_client()
        response = client.post(
            '/test',
            data='invalid json',
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_validate_json_request_missing_required_field(self, app):
        """Test decorator rejects missing required fields."""
        @app.route('/test', methods=['POST'])
        @validate_json_request(required_fields=['name', 'email'])
        def test_endpoint():
            return {'success': True}

        client = app.test_client()
        response = client.post('/test', json={'name': 'Alice'})

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_validate_json_request_bypass(self, app):
        """Test decorator bypass allows any request."""
        @app.route('/test', methods=['POST'])
        @validate_json_request(required_fields=['name'], bypass_validation=True)
        def test_endpoint():
            return {'success': True}

        client = app.test_client()
        response = client.post('/test', data='anything')

        assert response.status_code == 200


class TestValidateQueryParams:
    """Test query parameter validation."""

    def test_validate_query_params_integer_type(self):
        """Test validation converts and validates integer parameters."""
        params = {'page': '2', 'limit': '10'}
        schema = {
            'page': {'type': 'int', 'default': 1, 'min': 1},
            'limit': {'type': 'int', 'default': 10, 'min': 1, 'max': 100}
        }

        result = validate_query_params(params, schema)

        assert result['page'] == 2
        assert result['limit'] == 10
        assert isinstance(result['page'], int)

    def test_validate_query_params_float_type(self):
        """Test validation converts and validates float parameters."""
        params = {'price': '19.99'}
        schema = {
            'price': {'type': 'float', 'min': 0.0, 'max': 1000.0}
        }

        result = validate_query_params(params, schema)

        assert result['price'] == 19.99
        assert isinstance(result['price'], float)

    def test_validate_query_params_bool_type(self):
        """Test validation converts boolean parameters."""
        params = {'active': 'true', 'verified': '1', 'admin': 'false'}
        schema = {
            'active': {'type': 'bool'},
            'verified': {'type': 'bool'},
            'admin': {'type': 'bool'}
        }

        result = validate_query_params(params, schema)

        assert result['active'] is True
        assert result['verified'] is True
        assert result['admin'] is False

    def test_validate_query_params_default_values(self):
        """Test validation uses default values for missing params."""
        params = {}
        schema = {
            'page': {'type': 'int', 'default': 1},
            'limit': {'type': 'int', 'default': 10}
        }

        result = validate_query_params(params, schema)

        assert result['page'] == 1
        assert result['limit'] == 10

    def test_validate_query_params_required_missing(self):
        """Test validation fails for missing required params."""
        params = {}
        schema = {
            'user_id': {'type': 'int', 'required': True}
        }

        with pytest.raises(ValidationError, match='user_id is required'):
            validate_query_params(params, schema)

    def test_validate_query_params_range_validation(self):
        """Test validation enforces min/max ranges."""
        params = {'limit': '200'}
        schema = {
            'limit': {'type': 'int', 'min': 1, 'max': 100}
        }

        with pytest.raises(ValidationError, match='must not exceed 100'):
            validate_query_params(params, schema)

    def test_validate_query_params_bypass(self):
        """Test bypass returns params unchanged."""
        params = {'invalid': 'data'}
        schema = {'valid': {'type': 'int', 'required': True}}

        result = validate_query_params(params, schema, bypass=True)

        assert result == params


class TestValidationPatterns:
    """Test regex patterns used in validation."""

    def test_email_pattern(self):
        """Test EMAIL_PATTERN regex."""
        assert EMAIL_PATTERN.match('user@example.com')
        assert EMAIL_PATTERN.match('test.user+tag@domain.co.uk')
        assert not EMAIL_PATTERN.match('invalid')
        assert not EMAIL_PATTERN.match('@example.com')

    def test_alphanumeric_pattern(self):
        """Test ALPHANUMERIC_PATTERN regex."""
        assert ALPHANUMERIC_PATTERN.match('valid_name-123')
        assert ALPHANUMERIC_PATTERN.match('test')
        assert not ALPHANUMERIC_PATTERN.match('invalid space')
        assert not ALPHANUMERIC_PATTERN.match('invalid@symbol')


class TestSecurityBypassScenarios:
    """Test validation bypass scenarios for vulnerable endpoints."""

    def test_all_security_checks_bypass(self):
        """Test all security checks can be bypassed."""
        malicious_input = "'; DROP TABLE users; <script>alert(1)</script> ../../../etc/passwd | whoami"

        # All should pass with bypass=True
        assert check_sql_injection(malicious_input, 'field', bypass=True) is True
        assert check_xss(malicious_input, 'field', bypass=True) is True
        assert check_path_traversal(malicious_input, 'field', bypass=True) is True
        assert check_command_injection(malicious_input, 'field', bypass=True) is True

    def test_validation_functions_bypass(self):
        """Test all validation functions support bypass."""
        assert validate_email('not-an-email', bypass=True) is True
        assert validate_string('', 'field', min_length=10, bypass=True) is True
        assert validate_integer('invalid', 'field', bypass=True) is True
        assert validate_float('invalid', 'field', bypass=True) is True
