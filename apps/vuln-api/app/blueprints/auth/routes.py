"""
Routes for auth endpoints.
WARNING: This code contains intentional vulnerabilities for WAF testing purposes.
DO NOT use in production environments.
"""

from flask import request, jsonify, render_template_string, session, current_app
from datetime import datetime, timedelta
import uuid
import random
import json
import time
import hashlib
import hmac
import base64
import os
import secrets
import jwt as pyjwt

from . import auth_bp
from app.models import *

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_demo_mode():
    """Get demo mode from environment"""
    return os.getenv('DEMO_MODE', 'strict').lower()

def weak_hash_password(password):
    """Intentionally weak password hashing for demo purposes"""
    # In strict mode, use better hashing
    if get_demo_mode() == 'strict':
        return hashlib.sha256(password.encode()).hexdigest()
    # In full mode, use MD5 (weak)
    return hashlib.md5(password.encode()).hexdigest()

def generate_weak_token():
    """Generate predictable token for demo purposes"""
    if get_demo_mode() == 'strict':
        return secrets.token_urlsafe(32)
    # Predictable token in full mode
    return hashlib.md5(str(time.time()).encode()).hexdigest()

def generate_jwt(user_id, username, expires_in=3600):
    """Generate JWT token with intentional vulnerabilities"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in),
        'iat': datetime.utcnow()
    }

    # In full demo mode, support "none" algorithm vulnerability
    if get_demo_mode() == 'full':
        # Accept algorithm from request header if present
        alg = request.headers.get('X-JWT-Algorithm', 'HS256')
        if alg.lower() == 'none':
            # Vulnerable: no signature verification
            return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

    # Normal JWT signing
    secret = current_app.secret_key
    return pyjwt.encode(payload, secret, algorithm='HS256')

def verify_jwt(token):
    """Verify JWT token with intentional vulnerabilities"""
    try:
        # In full mode, accept unsigned tokens
        if get_demo_mode() == 'full' and '.' not in token:
            payload = json.loads(base64.urlsafe_b64decode(token))
            return payload

        secret = current_app.secret_key
        payload = pyjwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except Exception as e:
        return None

def vulnerable_sql_check(username, password):
    """
    INTENTIONAL VULNERABILITY: SQL Injection in authentication
    Only active when DEMO_MODE=full
    """
    if get_demo_mode() != 'full':
        return None

    # Simulate SQL injection vulnerability
    # In real code, this would be: f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    # Attacker payload: username = "admin' --" bypasses password check
    if "' --" in username or "' #" in username or "' OR '1'='1" in username:
        # Simulate successful SQL injection
        return {
            'user_id': 'sqli-bypass-001',
            'username': 'admin',
            'email': 'admin@demo.com',
            'role': 'admin',
            'injection': True
        }
    return None

def timing_attack_user_enum(email):
    """
    INTENTIONAL VULNERABILITY: Timing attack for user enumeration
    Returns different response times based on user existence
    """
    user_exists = user_exists_by_email(email)
    if get_demo_mode() == 'full':
        # Simulate database lookup time
        time.sleep(0.2 if user_exists else 0.05)
    return user_exists

# ============================================================================
# CORE AUTH ENDPOINTS
# ============================================================================

@auth_bp.route('/api/v1/auth/methods')
def auth_methods():
    """Authentication methods discovery"""
    return jsonify({
        'supported_methods': [
            'password',
            'mfa_sms',
            'mfa_email',
            'biometric_fingerprint',
            'hardware_token'
        ],
        'mfa_required': True,
        'session_timeout': 1800
    })


@auth_bp.route('/api/v1/auth/login', methods=['POST'])
def auth_login():
    """
    Primary login endpoint
    VULNERABILITIES:
    - SQL injection when DEMO_MODE=full
    - User enumeration via timing attacks
    - Weak session tokens
    ---
    tags:
      - Authentication
    summary: Authenticate user and get JWT
    description: |
        Authenticates a user and returns a JWT token.
        
        **Intentionally Vulnerable Endpoint:**
        This endpoint contains SQL injection and timing attack vulnerabilities when running in demo mode.
        
        **Attack Vectors:**
        - **SQL Injection:** Use `admin' OR '1'='1` as username to bypass password check.
    parameters:
      - in: body
        name: credentials
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              example: "admin"
            password:
              type: string
              example: "password123"
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            token:
              type: string
              description: JWT access token
            user:
              type: object
              properties:
                id:
                  type: string
                username:
                  type: string
                role:
                  type: string
      400:
        description: Missing credentials
      401:
        description: Invalid credentials
    """
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    # VULNERABILITY: SQL injection check (full mode only)
    sqli_result = vulnerable_sql_check(username, password)
    if sqli_result:
        session['user_id'] = sqli_result['user_id']
        session['username'] = sqli_result['username']
        session['role'] = sqli_result['role']

        token = generate_jwt(sqli_result['user_id'], sqli_result['username'])

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': sqli_result,
            'vulnerability': 'SQL Injection bypassed authentication'
        }), 200

    # Normal authentication flow
    user = get_user_by_identifier(username)

    # VULNERABILITY: Timing attack - different response times
    if get_demo_mode() == 'full':
        if user:
            time.sleep(0.15)
        else:
            time.sleep(0.05)

    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Check password
    password_hash = weak_hash_password(password)
    if user.get('password_hash') != password_hash:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Generate session
    session_id = generate_weak_token()
    session['user_id'] = user.get('user_id')
    session['username'] = user.get('username')
    session['session_id'] = session_id

    # Generate JWT
    token = generate_jwt(user.get('user_id'), user.get('username'))

    # Check if MFA is required
    if user.get('mfa_enabled'):
        challenge_id = str(uuid.uuid4())
        with mfa_challenges_db_lock:
            mfa_challenges_db[challenge_id] = {
                'user_id': user.get('user_id'),
                'created_at': datetime.utcnow().isoformat(),
                'code': str(random.randint(100000, 999999)),
                'attempts': 0
            }

        return jsonify({
            'mfa_required': True,
            'challenge_id': challenge_id,
            'method': user.get('mfa_method', 'sms')
        }), 200

    return jsonify({
        'success': True,
        'message': 'Login successful',
        'token': token,
        'session_id': session_id,
        'user': {
            'user_id': user.get('user_id'),
            'username': user.get('username'),
            'email': user.get('email'),
            'role': user.get('role', 'user')
        }
    }), 200


@auth_bp.route('/api/v1/auth/logout', methods=['POST'])
def auth_logout():
    """Session termination endpoint"""
    user_id = session.get('user_id')

    # Clear session
    session.clear()

    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200


@auth_bp.route('/api/v1/auth/register', methods=['POST'])
def auth_register_v1():
    """
    User registration endpoint
    VULNERABILITIES:
    - Weak password validation
    - No rate limiting
    - User enumeration
    """
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    name = data.get('name', '').strip()

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password required'}), 400

    # VULNERABILITY: User enumeration - specific error messages
    if get_demo_mode() == 'full':
        if user_exists_by_username(username):
            return jsonify({'error': 'Username already exists'}), 409
        if user_exists_by_email(email):
            return jsonify({'error': 'Email already registered'}), 409
    else:
        # Better: generic message
        if user_exists_by_username(username) or user_exists_by_email(email):
            return jsonify({'error': 'User already exists'}), 409

    # VULNERABILITY: Weak password validation (only in full mode)
    if get_demo_mode() == 'strict' and len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    # Create new user
    user_id = str(uuid.uuid4())
    password_hash = weak_hash_password(password)

    add_user(user_id, {
        'user_id': user_id,
        'username': username,
        'email': email,
        'password_hash': password_hash,
        'name': name,
        'role': 'user',
        'created_at': datetime.utcnow().isoformat(),
        'mfa_enabled': False
    })

    return jsonify({
        'success': True,
        'message': 'User registered successfully',
        'user_id': user_id,
        'username': username
    }), 201


@auth_bp.route('/api/v1/auth/forgot', methods=['POST'])
def auth_forgot():
    """
    Password reset initiation
    VULNERABILITIES:
    - Predictable reset tokens (full mode)
    - User enumeration via timing
    - No rate limiting
    """
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'error': 'Email required'}), 400

    # VULNERABILITY: Timing attack for user enumeration
    timing_attack_user_enum(email)

    # Find user
    user = get_user_by_email(email)

    # VULNERABILITY: In full mode, reveal if user exists
    if get_demo_mode() == 'full' and not user:
        return jsonify({'error': 'Email not found'}), 404

    if user:
        # Generate reset token
        if get_demo_mode() == 'full':
            # VULNERABILITY: Predictable token
            reset_token = hashlib.md5(f"{email}{int(time.time())}".encode()).hexdigest()
        else:
            reset_token = secrets.token_urlsafe(32)

        with password_reset_requests_lock:
            password_reset_requests[reset_token] = {
                'user_id': user.get('user_id'),
                'email': email,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                'used': False
            }

        return jsonify({
            'success': True,
            'message': 'Password reset email sent',
            'reset_token': reset_token if get_demo_mode() == 'full' else None  # Leak token in full mode
        }), 200

    # Generic response to prevent enumeration (strict mode)
    return jsonify({
        'success': True,
        'message': 'If email exists, password reset link has been sent'
    }), 200


@auth_bp.route('/api/v1/auth/reset', methods=['POST'])
def auth_reset():
    """
    Password reset completion
    VULNERABILITIES:
    - No token expiration check in full mode
    - Weak password validation
    """
    data = request.get_json() or {}
    reset_token = data.get('reset_token', '')
    new_password = data.get('new_password', '')

    if not reset_token or not new_password:
        return jsonify({'error': 'Reset token and new password required'}), 400

    # Check token
    with password_reset_requests_lock:
        reset_req = password_reset_requests.get(reset_token)
        if not reset_req:
            return jsonify({'error': 'Invalid reset token'}), 400

        if reset_req.get('used'):
            return jsonify({'error': 'Reset token already used'}), 400

        # VULNERABILITY: No expiration check in full mode
        if get_demo_mode() == 'strict':
            expires_at = datetime.fromisoformat(reset_req.get('expires_at'))
            if datetime.utcnow() > expires_at:
                return jsonify({'error': 'Reset token expired'}), 400

        # Update password
        user_id = reset_req.get('user_id')
        if not update_user(user_id, {'password_hash': weak_hash_password(new_password)}):
            return jsonify({'error': 'User not found'}), 404

        reset_req['used'] = True

        return jsonify({
            'success': True,
            'message': 'Password reset successful'
        }), 200


@auth_bp.route('/api/v1/auth/verify', methods=['POST'])
def auth_verify():
    """
    Email/phone verification
    VULNERABILITIES:
    - Predictable verification codes
    - No rate limiting on attempts
    """
    data = request.get_json() or {}
    user_id = data.get('user_id', '')
    code = data.get('code', '')

    if not user_id or not code:
        return jsonify({'error': 'User ID and verification code required'}), 400

    # In demo, accept any 6-digit code in full mode
    if get_demo_mode() == 'full' and len(code) == 6 and code.isdigit():
        if update_user(user_id, {'verified': True}):
            return jsonify({
                'success': True,
                'message': 'Verification successful'
            }), 200

    return jsonify({'error': 'Invalid verification code'}), 400


@auth_bp.route('/api/v1/auth/refresh', methods=['POST'])
def auth_refresh_v1():
    """
    Token refresh endpoint
    VULNERABILITIES:
    - Accepts expired tokens in full mode
    - No token rotation
    """
    data = request.get_json() or {}
    refresh_token = data.get('refresh_token', '')

    if not refresh_token:
        return jsonify({'error': 'Refresh token required'}), 400

    # Verify refresh token
    with refresh_tokens_db_lock:
        token_data = refresh_tokens_db.get(refresh_token)

    if not token_data:
        return jsonify({'error': 'Invalid refresh token'}), 401

    # VULNERABILITY: No expiration check in full mode
    if get_demo_mode() == 'strict':
        expires_at = datetime.fromisoformat(token_data.get('expires_at'))
        if datetime.utcnow() > expires_at:
            return jsonify({'error': 'Refresh token expired'}), 401

    user_id = token_data.get('user_id')
    user = get_user_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Generate new access token
    access_token = generate_jwt(user_id, user.get('username'))

    return jsonify({
        'success': True,
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': 3600
    }), 200


@auth_bp.route('/api/v1/auth/status', methods=['GET'])
def auth_status():
    """Authentication status check"""
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({
            'authenticated': False,
            'message': 'Not authenticated'
        }), 200

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({
            'authenticated': False,
            'message': 'User not found'
        }), 200

    return jsonify({
        'authenticated': True,
        'user': {
            'user_id': user.get('user_id'),
            'username': user.get('username'),
            'email': user.get('email'),
            'role': user.get('role', 'user')
        }
    }), 200


# ============================================================================
# MFA ENDPOINTS
# ============================================================================

@auth_bp.route('/api/v1/auth/mfa/enable', methods=['POST'])
def auth_mfa_enable():
    """
    Enable 2FA for user
    VULNERABILITIES:
    - No validation of user session
    - Weak TOTP secret generation
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json() or {}
    method = data.get('method', 'totp')  # totp, sms, email

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Generate TOTP secret
    if get_demo_mode() == 'full':
        # VULNERABILITY: Weak secret
        totp_secret = hashlib.md5(user_id.encode()).hexdigest()[:16]
    else:
        totp_secret = base64.b32encode(secrets.token_bytes(20)).decode()

    if not update_user(user_id, {
        'mfa_enabled': True,
        'mfa_method': method,
        'mfa_secret': totp_secret
    }):
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'success': True,
        'message': 'MFA enabled',
        'method': method,
        'secret': totp_secret,  # In production, only show during setup
        'qr_code_url': f'otpauth://totp/Demo:{user.get("email")}?secret={totp_secret}&issuer=Demo'
    }), 200


@auth_bp.route('/api/v1/auth/mfa/verify', methods=['POST'])
def auth_mfa_verify():
    """
    Verify MFA code
    VULNERABILITIES:
    - No rate limiting
    - Accepts recent codes in full mode
    """
    data = request.get_json() or {}
    challenge_id = data.get('challenge_id', '')
    code = data.get('code', '')

    if not challenge_id or not code:
        return jsonify({'error': 'Challenge ID and code required'}), 400

    with mfa_challenges_db_lock:
        challenge = mfa_challenges_db.get(challenge_id)
        if not challenge:
            return jsonify({'error': 'Invalid challenge'}), 400

        # VULNERABILITY: No rate limiting in full mode
        challenge['attempts'] += 1

        too_many = get_demo_mode() == 'strict' and challenge['attempts'] > 3
        matches = code == challenge.get('code')
        user_id = challenge.get('user_id')

        if matches and not too_many:
            # Clean up challenge
            del mfa_challenges_db[challenge_id]

    if too_many:
        return jsonify({'error': 'Too many attempts'}), 429

    # Verify code
    if matches:
        user = get_user_by_id(user_id)

        if user:
            # Complete login
            session['user_id'] = user_id
            session['username'] = user.get('username')

            token = generate_jwt(user_id, user.get('username'))

            return jsonify({
                'success': True,
                'message': 'MFA verification successful',
                'token': token,
                'user': {
                    'user_id': user.get('user_id'),
                    'username': user.get('username'),
                    'email': user.get('email')
                }
            }), 200

    return jsonify({'error': 'Invalid MFA code'}), 401


@auth_bp.route('/api/v1/auth/mfa/backup', methods=['POST'])
def auth_mfa_backup():
    """
    Generate MFA backup codes
    VULNERABILITIES:
    - Predictable backup codes in full mode
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Generate backup codes
    backup_codes = []
    for i in range(10):
        if get_demo_mode() == 'full':
            # VULNERABILITY: Predictable codes
            code = hashlib.md5(f"{user_id}{i}".encode()).hexdigest()[:8]
        else:
            code = secrets.token_hex(4)
        backup_codes.append(code)

    if not update_user(user_id, {'backup_codes': backup_codes}):
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'success': True,
        'backup_codes': backup_codes
    }), 200


# ============================================================================
# OAUTH/SOCIAL ENDPOINTS
# ============================================================================

@auth_bp.route('/api/v1/auth/oauth/authorize', methods=['GET'])
def oauth_authorize_v1():
    """
    OAuth authorization endpoint
    VULNERABILITIES:
    - No redirect URI validation in full mode
    - State parameter not enforced
    """
    client_id = request.args.get('client_id', '')
    redirect_uri = request.args.get('redirect_uri', '')
    response_type = request.args.get('response_type', 'code')
    state = request.args.get('state', '')
    scope = request.args.get('scope', 'read')

    if not client_id or not redirect_uri:
        return jsonify({'error': 'client_id and redirect_uri required'}), 400

    # VULNERABILITY: No redirect URI validation in full mode
    if get_demo_mode() == 'strict':
        # Validate redirect_uri against registered clients
        valid_uris = ['http://localhost:3000/callback', 'https://demo.com/callback']
        if redirect_uri not in valid_uris:
            return jsonify({'error': 'Invalid redirect_uri'}), 400

    # Generate authorization code
    auth_code = generate_weak_token()

    # Store authorization
    session['oauth_auth'] = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'code': auth_code,
        'scope': scope,
        'state': state,
        'created_at': datetime.utcnow().isoformat()
    }

    return jsonify({
        'authorization_code': auth_code,
        'redirect_uri': redirect_uri,
        'state': state
    }), 200


@auth_bp.route('/api/v1/auth/oauth/callback', methods=['POST'])
def oauth_callback_v1():
    """
    OAuth callback endpoint
    VULNERABILITIES:
    - No state validation in full mode
    """
    data = request.get_json() or {}
    code = data.get('code', '')
    state = data.get('state', '')

    if not code:
        return jsonify({'error': 'Authorization code required'}), 400

    oauth_auth = session.get('oauth_auth')
    if not oauth_auth or oauth_auth.get('code') != code:
        return jsonify({'error': 'Invalid authorization code'}), 400

    # VULNERABILITY: No state validation in full mode
    if get_demo_mode() == 'strict':
        if state != oauth_auth.get('state'):
            return jsonify({'error': 'Invalid state parameter'}), 400

    # Generate access token
    user_id = session.get('user_id', 'demo-user')
    access_token = generate_jwt(user_id, 'oauth_user')

    return jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': 3600,
        'scope': oauth_auth.get('scope')
    }), 200


@auth_bp.route('/api/v1/auth/social/<provider>', methods=['POST'])
def social_login(provider):
    """
    Social login endpoint
    VULNERABILITIES:
    - No token validation
    - Accepts any provider
    """
    data = request.get_json() or {}
    access_token = data.get('access_token', '')

    if not access_token:
        return jsonify({'error': 'Access token required'}), 400

    # In demo, accept any token
    user_id = str(uuid.uuid4())
    username = f"{provider}_user_{random.randint(1000, 9999)}"

    # Create or get user
    if not get_user_by_id(user_id):
        add_user(user_id, {
            'user_id': user_id,
            'username': username,
            'email': f'{username}@{provider}.com',
            'provider': provider,
            'created_at': datetime.utcnow().isoformat()
        })

    token = generate_jwt(user_id, username)

    return jsonify({
        'success': True,
        'token': token,
        'user': get_user_by_id(user_id)
    }), 200


# ============================================================================
# SAML ENDPOINTS (Enhanced from existing)
# ============================================================================

@auth_bp.route('/api/v1/auth/saml/metadata')
def saml_metadata_v1():
    """SAML metadata endpoint - exposes sensitive configuration"""
    # Intentionally exposes SAML configuration including private keys
    return jsonify({
        'entity_id': 'https://demo.chimera.com/saml',
        'sso_url': 'https://demo.chimera.com/api/v1/auth/saml/login',
        'slo_url': 'https://demo.chimera.com/api/v1/auth/saml/logout',
        'certificate': '''-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKL0UG+mRKzYMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
-----END CERTIFICATE-----''',
        'private_key': '''-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj
MzEfYyjiWA4R4/M2bS1+fWIcPm15j9DP3Xzq9rKjZ7i+FPU4lqVXxQdQ7pjE
-----END PRIVATE KEY-----''',  # Intentionally exposed
        'nameid_format': 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
        'signing_algorithm': 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256',
        'encryption_algorithm': 'http://www.w3.org/2001/04/xmlenc#aes128-cbc',
        'assertion_consumer_service': 'https://demo.chimera.com/api/v1/auth/saml/callback',
        'attributes': ['email', 'firstName', 'lastName', 'groups', 'ssn', 'salary']  # Excessive attributes
    })


@auth_bp.route('/api/v1/auth/saml/login', methods=['POST'])
def saml_login():
    """
    SAML SSO login initiation
    VULNERABILITIES:
    - No signature validation in full mode
    """
    data = request.get_json() or {}
    relay_state = data.get('RelayState', '')

    # Generate SAML request
    request_id = str(uuid.uuid4())

    saml_request = {
        'id': request_id,
        'created_at': datetime.utcnow().isoformat(),
        'relay_state': relay_state,
        'issuer': 'https://demo.chimera.com/saml',
        'destination': 'https://idp.example.com/sso'
    }

    session['saml_request'] = saml_request

    return jsonify({
        'saml_request_id': request_id,
        'idp_url': 'https://idp.example.com/sso',
        'relay_state': relay_state
    }), 200


@auth_bp.route('/api/v1/auth/saml/callback', methods=['POST'])
def saml_callback():
    """
    SAML assertion consumer service
    VULNERABILITIES:
    - No signature validation
    - XML injection possible
    - Accepts any assertion in full mode
    """
    data = request.get_json() or {}
    saml_response = data.get('SAMLResponse', '')
    relay_state = data.get('RelayState', '')

    if not saml_response:
        return jsonify({'error': 'SAMLResponse required'}), 400

    # VULNERABILITY: No validation in full mode
    if get_demo_mode() == 'full':
        # Accept any SAML response, extract nameid from JSON
        try:
            # Simulate parsing (in reality would be XML)
            response_data = json.loads(saml_response)
            email = response_data.get('nameid', 'unknown@demo.com')
        except:
            email = 'saml-user@demo.com'

        # Create or get user
        with users_db_lock:
            user_id = email_to_id_map.get(email)
            user = users_db.get(user_id) if user_id else None

        if not user_id:
            user_id = str(uuid.uuid4())
            user = {
                'user_id': user_id,
                'username': email.split('@')[0],
                'email': email,
                'auth_method': 'saml',
                'created_at': datetime.utcnow().isoformat()
            }
            add_user(user_id, user)
        session['user_id'] = user_id
        session['username'] = user.get('username')

        token = generate_jwt(user_id, user.get('username'))

        return jsonify({
            'success': True,
            'token': token,
            'user': user,
            'relay_state': relay_state
        }), 200

    return jsonify({'error': 'SAML validation not implemented in strict mode'}), 501


# ============================================================================
# API KEY ENDPOINTS
# ============================================================================

@auth_bp.route('/api/v1/auth/apikeys', methods=['GET'])
def auth_apikeys_list():
    """
    List API keys for authenticated user
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    # Get user's API keys
    with api_keys_db_lock:
        user_keys = [
            k for k in api_keys_db.values()
            if k.get('user_id') == user_id and not k.get('revoked')
        ]

        # Sanitize keys (don't expose full key)
        sanitized_keys = []
        for key_data in user_keys:
            sanitized_keys.append({
                'key_id': key_data.get('key_id'),
                'name': key_data.get('name'),
                'prefix': key_data.get('key')[:8] + '...',
                'created_at': key_data.get('created_at'),
                'last_used': key_data.get('last_used'),
                'expires_at': key_data.get('expires_at')
            })

    return jsonify({
        'api_keys': sanitized_keys
    }), 200


@auth_bp.route('/api/v1/auth/apikeys/create', methods=['POST'])
def auth_apikeys_create():
    """
    Create new API key
    VULNERABILITIES:
    - Weak key generation in full mode
    - No rate limiting
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json() or {}
    name = data.get('name', 'Unnamed Key')
    expires_in_days = data.get('expires_in_days', 90)

    # Generate API key
    key_id = str(uuid.uuid4())

    if get_demo_mode() == 'full':
        # VULNERABILITY: Weak key generation
        api_key = f"demo_{hashlib.md5(f'{user_id}{time.time()}'.encode()).hexdigest()}"
    else:
        api_key = f"sk_{secrets.token_urlsafe(32)}"

    expires_at = (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat()
    record = {
        'key_id': key_id,
        'user_id': user_id,
        'key': api_key,
        'name': name,
        'created_at': datetime.utcnow().isoformat(),
        'expires_at': expires_at,
        'last_used': None,
        'revoked': False
    }
    with api_keys_db_lock:
        api_keys_db[key_id] = record

    return jsonify({
        'success': True,
        'key_id': key_id,
        'api_key': api_key,  # Only shown once
        'name': name,
        'expires_at': expires_at
    }), 201


@auth_bp.route('/api/v1/auth/apikeys/revoke', methods=['POST'])
def auth_apikeys_revoke():
    """Revoke API key"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json() or {}
    key_id = data.get('key_id', '')

    if not key_id:
        return jsonify({'error': 'key_id required'}), 400

    with api_keys_db_lock:
        key_data = api_keys_db.get(key_id)
        if not key_data:
            return jsonify({'error': 'API key not found'}), 404

        # Verify ownership
        if key_data.get('user_id') != user_id:
            return jsonify({'error': 'Unauthorized'}), 403

        # Revoke key
        key_data['revoked'] = True
        key_data['revoked_at'] = datetime.utcnow().isoformat()

    return jsonify({
        'success': True,
        'message': 'API key revoked'
    }), 200


# ============================================================================
# LEGACY ENDPOINTS (Keep existing routes)
# ============================================================================

@auth_bp.route('/api/v1/auth/forgot-password', methods=['POST'])
def auth_forgot_password():
    """Legacy endpoint - redirect to /forgot"""
    return auth_forgot()


@auth_bp.route('/api/v1/auth/verify-mfa', methods=['POST'])
def auth_verify_mfa():
    """Legacy endpoint - redirect to /mfa/verify"""
    return auth_mfa_verify()


@auth_bp.route('/api/v1/device/register', methods=['POST'])
def device_register():
    """Device binding and registration endpoint"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json() or {}
    device_name = data.get('device_name', 'Unknown Device')
    device_type = data.get('device_type', 'mobile')

    device_id = str(uuid.uuid4())
    with registered_devices_db_lock:
        registered_devices_db[device_id] = {
            'device_id': device_id,
            'user_id': user_id,
            'device_name': device_name,
            'device_type': device_type,
            'registered_at': datetime.utcnow().isoformat(),
            'last_seen': datetime.utcnow().isoformat()
        }

    return jsonify({
        'success': True,
        'device_id': device_id
    }), 201


@auth_bp.route('/api/v1/auth/api-keys', methods=['POST'])
def auth_api_keys():
    """Legacy endpoint - redirect to /apikeys/create"""
    return auth_apikeys_create()


@auth_bp.route('/api/oauth/authorize')
def oauth_authorize():
    """Legacy OAuth endpoint"""
    return oauth_authorize_v1()


@auth_bp.route('/api/oauth/token', methods=['POST'])
def oauth_token():
    """Legacy OAuth token endpoint"""
    data = request.get_json() or {}
    grant_type = data.get('grant_type', '')
    code = data.get('code', '')

    if grant_type == 'authorization_code':
        return oauth_callback_v1()

    return jsonify({'error': 'Unsupported grant_type'}), 400


@auth_bp.route('/api/auth/register', methods=['POST'])
def auth_register():
    """Legacy registration endpoint"""
    return auth_register_v1()


@auth_bp.route('/api/oauth/token/forge', methods=['POST'])
def oauth_token_forge():
    """
    OAuth token endpoint - vulnerable to token forgery
    VULNERABILITY: Allows arbitrary token generation
    """
    data = request.get_json() or {}
    client_id = data.get('client_id', 'unknown')
    username = data.get('username', 'forged_user')

    if get_demo_mode() != 'full':
        return jsonify({'error': 'Endpoint requires DEMO_MODE=full'}), 403

    # VULNERABILITY: Generate token without authentication
    user_id = str(uuid.uuid4())
    token = generate_jwt(user_id, username, expires_in=86400)

    return jsonify({
        'access_token': token,
        'token_type': 'Bearer',
        'expires_in': 86400,
        'warning': 'Token forged without authentication'
    }), 200


@auth_bp.route('/api/saml/metadata')
def saml_metadata():
    """Legacy SAML metadata endpoint"""
    return saml_metadata_v1()


@auth_bp.route('/api/saml/sso', methods=['POST'])
def saml_sso():
    """Legacy SAML SSO endpoint"""
    return saml_login()
