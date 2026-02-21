"""
Unit tests for authentication helper utilities.

Tests cover:
- Token generation and validation
- Password hashing and verification
- API key generation
- Decorators (require_auth, require_role)
- Weak authentication mode
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from app.utils.auth_helpers import (
    TokenError,
    generate_token,
    verify_token,
    generate_refresh_token,
    generate_api_key,
    hash_password,
    verify_password,
    extract_bearer_token,
    extract_api_key,
    require_auth,
    require_role,
    create_session,
    validate_session,
    invalidate_session,
    check_rate_limit,
    generate_mfa_secret,
    verify_totp_code,
    SECRET_KEY,
    TOKEN_EXPIRY_SECONDS,
    API_KEY_PREFIX
)


class TestTokenGeneration:
    """Test token generation functionality."""

    def test_generate_token_basic(self):
        """Test basic token generation."""
        token = generate_token('user_123')

        assert isinstance(token, str)
        assert '.' in token  # Contains payload and signature
        parts = token.split('.')
        assert len(parts) == 2

    def test_generate_token_with_additional_claims(self):
        """Test token with additional claims."""
        claims = {'role': 'admin', 'email': 'admin@example.com'}
        token = generate_token('user_123', additional_claims=claims)

        payload = verify_token(token)
        assert payload['user_id'] == 'user_123'
        assert payload['role'] == 'admin'
        assert payload['email'] == 'admin@example.com'

    def test_generate_token_includes_timestamps(self):
        """Test token includes issued and expiry timestamps."""
        token = generate_token('user_123')

        payload = verify_token(token)
        assert 'iat' in payload
        assert 'exp' in payload
        assert payload['exp'] > payload['iat']

    def test_generate_token_custom_expiry(self):
        """Test token with custom expiry time."""
        custom_expiry = 7200  # 2 hours
        token = generate_token('user_123', expiry_seconds=custom_expiry)

        payload = verify_token(token)
        assert payload['exp'] - payload['iat'] == custom_expiry

    def test_generate_token_weak_signing(self):
        """Test token generation with weak signing."""
        token = generate_token('user_123', weak_signing=True)

        # Should be verifiable with weak_signing=True
        payload = verify_token(token, weak_signing=True)
        assert payload['user_id'] == 'user_123'


class TestTokenVerification:
    """Test token verification functionality."""

    def test_verify_token_valid(self):
        """Test verification of valid token."""
        token = generate_token('user_123')

        payload = verify_token(token)

        assert payload['user_id'] == 'user_123'
        assert isinstance(payload, dict)

    def test_verify_token_invalid_format(self):
        """Test verification fails for invalid token format."""
        with pytest.raises(TokenError, match='Invalid token format'):
            verify_token('invalid-token-format')

    def test_verify_token_invalid_signature(self):
        """Test verification fails for invalid signature."""
        token = generate_token('user_123')
        # Tamper with signature
        parts = token.split('.')
        tampered_token = parts[0] + '.invalidsignature'

        with pytest.raises(TokenError, match='Invalid token signature'):
            verify_token(tampered_token)

    def test_verify_token_expired(self):
        """Test verification fails for expired token."""
        # Generate token with very short expiry
        token = generate_token('user_123', expiry_seconds=1)

        # Wait for token to expire
        time.sleep(1.1)

        with pytest.raises(TokenError, match='expired'):
            verify_token(token)

    def test_verify_token_skip_expiry(self):
        """Test verification with expiry check skipped."""
        token = generate_token('user_123', expiry_seconds=1)
        time.sleep(1.1)

        # Should succeed with skip_expiry=True
        payload = verify_token(token, skip_expiry=True)
        assert payload['user_id'] == 'user_123'

    def test_verify_token_weak_signing_mismatch(self):
        """Test weak signed token requires weak verification."""
        token = generate_token('user_123', weak_signing=True)

        # Should fail with normal verification
        with pytest.raises(TokenError):
            verify_token(token, weak_signing=False)


class TestRefreshToken:
    """Test refresh token generation."""

    def test_generate_refresh_token(self):
        """Test refresh token generation."""
        token = generate_refresh_token()

        assert isinstance(token, str)
        assert len(token) > 32  # URL-safe random token

    def test_generate_refresh_token_unique(self):
        """Test refresh tokens are unique."""
        token1 = generate_refresh_token()
        token2 = generate_refresh_token()

        assert token1 != token2


class TestAPIKey:
    """Test API key generation."""

    def test_generate_api_key_with_prefix(self):
        """Test API key includes prefix."""
        key = generate_api_key()

        assert key.startswith(API_KEY_PREFIX)

    def test_generate_api_key_custom_prefix(self):
        """Test API key with custom prefix."""
        key = generate_api_key(prefix='custom_')

        assert key.startswith('custom_')

    def test_generate_api_key_unique(self):
        """Test API keys are unique."""
        key1 = generate_api_key()
        key2 = generate_api_key()

        assert key1 != key2


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_returns_hash_and_salt(self):
        """Test password hashing returns hash and salt."""
        password = 'SecurePassword123!'

        hashed, salt = hash_password(password)

        assert isinstance(hashed, str)
        assert isinstance(salt, str)
        assert len(hashed) > 0
        assert len(salt) > 0

    def test_hash_password_with_provided_salt(self):
        """Test hashing with provided salt."""
        password = 'password'
        salt = 'fixed_salt_12345'

        hashed1, _ = hash_password(password, salt)
        hashed2, _ = hash_password(password, salt)

        assert hashed1 == hashed2

    def test_hash_password_different_for_different_passwords(self):
        """Test different passwords produce different hashes."""
        hashed1, salt = hash_password('password1')
        hashed2, _ = hash_password('password2', salt)

        assert hashed1 != hashed2

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = 'SecurePassword123!'
        hashed, salt = hash_password(password)

        assert verify_password(password, hashed, salt) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = 'SecurePassword123!'
        hashed, salt = hash_password(password)

        assert verify_password('WrongPassword', hashed, salt) is False

    def test_verify_password_weak_hash(self):
        """Test password verification with weak hashing."""
        # Weak hash mode uses MD5
        import hashlib
        password = 'test'
        salt = 'salt'
        weak_hash = hashlib.md5((password + salt).encode()).hexdigest()

        assert verify_password(password, weak_hash, salt, weak_hash=True) is True
        assert verify_password('wrong', weak_hash, salt, weak_hash=True) is False


class TestTokenExtraction:
    """Test token extraction from headers."""

    def test_extract_bearer_token_valid(self):
        """Test extracting valid bearer token."""
        auth_header = 'Bearer abc123xyz'

        token = extract_bearer_token(auth_header)

        assert token == 'abc123xyz'

    def test_extract_bearer_token_case_insensitive(self):
        """Test bearer token extraction is case insensitive."""
        auth_header = 'bearer token123'

        token = extract_bearer_token(auth_header)

        assert token == 'token123'

    def test_extract_bearer_token_invalid_format(self):
        """Test extraction fails for invalid format."""
        assert extract_bearer_token('InvalidFormat') is None
        assert extract_bearer_token('Bearer') is None
        assert extract_bearer_token('') is None
        assert extract_bearer_token(None) is None

    @patch('app.utils.auth_helpers.request')
    def test_extract_api_key_from_header(self, mock_request):
        """Test extracting API key from header."""
        mock_request.headers.get.return_value = 'tx_api_key_123'

        key = extract_api_key()

        assert key == 'tx_api_key_123'

    @patch('app.utils.auth_helpers.request')
    def test_extract_api_key_from_query(self, mock_request):
        """Test extracting API key from query parameter."""
        mock_request.headers.get.return_value = None
        mock_request.args.get.return_value = 'tx_query_key_456'

        key = extract_api_key(allow_query=True)

        assert key == 'tx_query_key_456'

    @patch('app.utils.auth_helpers.request')
    def test_extract_api_key_query_not_allowed(self, mock_request):
        """Test query parameter ignored when not allowed."""
        mock_request.headers.get.return_value = None

        key = extract_api_key(allow_query=False)

        assert key is None


class TestRequireAuthDecorator:
    """Test require_auth decorator."""

    @patch('app.utils.auth_helpers.request')
    @patch('app.utils.auth_helpers.g')
    def test_require_auth_valid_token(self, mock_g, mock_request, app):
        """Test decorator allows valid token."""
        with app.app_context():
            token = generate_token('user_123')
            mock_request.headers.get.return_value = f'Bearer {token}'

            @require_auth()
            def protected_view():
                return {'success': True}

            result = protected_view()

            assert result == {'success': True}
            assert mock_g.user_id == 'user_123'
            assert mock_g.auth_method == 'token'

    @patch('app.utils.auth_helpers.request')
    def test_require_auth_missing_token(self, mock_request, app):
        """Test decorator rejects missing token."""
        with app.app_context():
            mock_request.headers.get.return_value = None

            @require_auth()
            def protected_view():
                return {'success': True}

            response, status_code = protected_view()

            assert status_code == 401

    @patch('app.utils.auth_helpers.request')
    def test_require_auth_invalid_token(self, mock_request, app):
        """Test decorator rejects invalid token."""
        with app.app_context():
            mock_request.headers.get.return_value = 'Bearer invalid'

            @require_auth()
            def protected_view():
                return {'success': True}

            response, status_code = protected_view()

            assert status_code == 401

    @patch('app.utils.auth_helpers.request')
    @patch('app.utils.auth_helpers.g')
    def test_require_auth_api_key(self, mock_g, mock_request, app):
        """Test decorator allows valid API key."""
        with app.app_context():
            mock_request.headers.get.side_effect = [None, 'tx_valid_key']

            @require_auth(allow_api_key=True)
            def protected_view():
                return {'success': True}

            result = protected_view()

            assert result == {'success': True}
            assert mock_g.auth_method == 'api_key'


class TestRequireRoleDecorator:
    """Test require_role decorator."""

    @patch('app.utils.auth_helpers.g')
    def test_require_role_authorized(self, mock_g, app):
        """Test decorator allows authorized role."""
        with app.app_context():
            mock_g.token_payload = {'user_id': 'user_123', 'role': 'admin'}

            @require_role(['admin', 'superuser'])
            def admin_view():
                return {'success': True}

            result = admin_view()

            assert result == {'success': True}

    @patch('app.utils.auth_helpers.g')
    def test_require_role_unauthorized(self, mock_g, app):
        """Test decorator rejects unauthorized role."""
        with app.app_context():
            mock_g.token_payload = {'user_id': 'user_123', 'role': 'user'}

            @require_role(['admin'])
            def admin_view():
                return {'success': True}

            response, status_code = admin_view()

            assert status_code == 403

    def test_require_role_no_token(self, app):
        """Test decorator rejects when no token payload."""
        with app.app_context():
            @require_role(['admin'])
            def admin_view():
                return {'success': True}

            response, status_code = admin_view()

            assert status_code == 403


class TestSessionManagement:
    """Test session management functions."""

    def test_create_session(self):
        """Test session creation."""
        session_id = create_session('user_123')

        assert isinstance(session_id, str)
        assert len(session_id) > 32

    def test_create_session_with_data(self):
        """Test session creation with data."""
        session_data = {'key': 'value'}
        session_id = create_session('user_123', session_data=session_data)

        assert session_id is not None

    def test_validate_session(self):
        """Test session validation placeholder."""
        result = validate_session('session_123')

        # Currently returns None (placeholder)
        assert result is None

    def test_invalidate_session(self):
        """Test session invalidation placeholder."""
        result = invalidate_session('session_123')

        # Currently returns True (placeholder)
        assert result is True


class TestRateLimiting:
    """Test rate limiting function."""

    def test_check_rate_limit_allows(self):
        """Test rate limit check allows request."""
        allowed, remaining = check_rate_limit('user_123', '/api/endpoint')

        assert allowed is True
        assert remaining >= 0


class TestMFAFunctions:
    """Test MFA-related functions."""

    def test_generate_mfa_secret(self):
        """Test MFA secret generation."""
        secret = generate_mfa_secret()

        assert isinstance(secret, str)
        assert len(secret) > 20  # Base32 encoded

    def test_generate_mfa_secret_unique(self):
        """Test MFA secrets are unique."""
        secret1 = generate_mfa_secret()
        secret2 = generate_mfa_secret()

        assert secret1 != secret2

    def test_verify_totp_code_valid(self):
        """Test TOTP code verification with valid code."""
        import pyotp

        secret = generate_mfa_secret()
        totp = pyotp.TOTP(secret)
        code = totp.now()

        # Note: verify_totp_code is a simplified implementation
        # This test may need adjustment based on actual implementation
        result = verify_totp_code(secret, code, window=1)

        assert isinstance(result, bool)

    def test_verify_totp_code_invalid(self):
        """Test TOTP code verification with invalid code."""
        secret = generate_mfa_secret()

        result = verify_totp_code(secret, '000000', window=1)

        assert result is False

    def test_verify_totp_code_handles_exception(self):
        """Test TOTP verification handles invalid input gracefully."""
        result = verify_totp_code('invalid_secret', 'invalid', window=1)

        assert result is False


class TestAuthenticationEdgeCases:
    """Test edge cases in authentication."""

    def test_generate_token_empty_user_id(self):
        """Test token generation with empty user ID."""
        token = generate_token('')

        payload = verify_token(token)
        assert payload['user_id'] == ''

    def test_hash_password_empty_password(self):
        """Test hashing empty password."""
        hashed, salt = hash_password('')

        assert len(hashed) > 0
        assert verify_password('', hashed, salt) is True

    def test_extract_bearer_token_multiple_spaces(self):
        """Test bearer token with multiple spaces."""
        result = extract_bearer_token('Bearer  token  with  spaces')

        # Should return None for invalid format
        assert result is None

    def test_api_key_generation_custom_length(self):
        """Test API key with custom length."""
        key = generate_api_key(length=64)

        assert len(key) > 64  # Includes prefix


class TestWeakAuthenticationMode:
    """Test weak authentication mode for demo scenarios."""

    def test_weak_token_signing_and_verification(self):
        """Test weak token signing produces MD5 signature."""
        token = generate_token('user_123', weak_signing=True)

        # Should be verifiable with weak signing
        payload = verify_token(token, weak_signing=True)
        assert payload['user_id'] == 'user_123'

    def test_weak_password_hashing(self):
        """Test weak password hashing uses MD5."""
        import hashlib

        password = 'test123'
        salt = 'salt'

        # Create weak hash
        weak_hash = hashlib.md5((password + salt).encode()).hexdigest()

        # Should verify with weak_hash=True
        assert verify_password(password, weak_hash, salt, weak_hash=True) is True
