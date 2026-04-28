"""
Routes for auth endpoints.
WARNING: This code contains intentional vulnerabilities for WAF testing purposes.
DO NOT use in production environments.
"""
from starlette.requests import Request
from starlette.responses import JSONResponse
from datetime import datetime, timedelta
import uuid
import random
import json
import time
import hashlib

from app.config import app_config
from app.routing import safe_json
import base64
import os
import secrets
import jwt as pyjwt

from . import auth_router
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

def generate_jwt(request, user_id, username, expires_in=3600):
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
    secret = app_config.secret_key
    return pyjwt.encode(payload, secret, algorithm='HS256')

def verify_jwt(token):
    """Verify JWT token with intentional vulnerabilities"""
    try:
        # In full mode, accept unsigned tokens
        if get_demo_mode() == 'full' and '.' not in token:
            payload = json.loads(base64.urlsafe_b64decode(token))
            return payload

        secret = app_config.secret_key
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

@auth_router.route('/api/v1/auth/methods')
async def auth_methods(request: Request):
    """Authentication methods discovery"""
    return JSONResponse({
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


@auth_router.route('/api/v1/auth/login', methods=['POST'])
async def auth_login(request: Request):
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
    data = await safe_json(request)
    username = data.get('username', '')
    password = data.get('password', '')

    if not username or not password:
        return JSONResponse({'error': 'Username and password required'}, status_code = 400)

    # VULNERABILITY: SQL injection check (full mode only)
    sqli_result = vulnerable_sql_check(username, password)
    if sqli_result:
        request.session['user_id'] = sqli_result['user_id']
        request.session['username'] = sqli_result['username']
        request.session['role'] = sqli_result['role']

        token = generate_jwt(request, sqli_result['user_id'], sqli_result['username'])

        return JSONResponse({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': sqli_result,
            'vulnerability': 'SQL Injection bypassed authentication'
        }, status_code = 200)

    # Normal authentication flow
    user = get_user_by_identifier(username)

    # VULNERABILITY: Timing attack - different response times
    if get_demo_mode() == 'full':
        if user:
            time.sleep(0.15)
        else:
            time.sleep(0.05)

    if not user:
        return JSONResponse({'error': 'Invalid credentials'}, status_code = 401)

    # Check password
    password_hash = weak_hash_password(password)
    if user.get('password_hash') != password_hash:
        return JSONResponse({'error': 'Invalid credentials'}, status_code = 401)

    # Generate session
    session_id = generate_weak_token()
    request.session['user_id'] = user.get('user_id')
    request.session['username'] = user.get('username')
    request.session['session_id'] = session_id

    # Generate JWT
    token = generate_jwt(request, user.get('user_id'), user.get('username'))

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

        return JSONResponse({
            'mfa_required': True,
            'challenge_id': challenge_id,
            'method': user.get('mfa_method', 'sms')
        }, status_code = 200)

    return JSONResponse({
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
    }, status_code = 200)


@auth_router.route('/api/v1/auth/delete', methods=['POST'])
async def auth_delete(request: Request):
    """
    User account deletion (Right to be Forgotten).
    VULNERABILITY: Residual Data, Missing Authorization
    """
    user_id = request.session.get('user_id')
    data = await safe_json(request)
    
    return JSONResponse({
        'success': True,
        'message': 'Account deletion request received and processed.',
        'user_id': user_id,
        'note': 'Your data will be removed from all primary systems within 30 days.'
    }, status_code = 200)


@auth_router.route('/api/v1/auth/logout', methods=['POST'])
async def auth_logout(request: Request):
    """Session termination endpoint"""
    user_id = request.session.get('user_id')

    # Clear session
    request.session.clear()

    return JSONResponse({
        'success': True,
        'message': 'Logged out successfully'
    }, status_code = 200)


@auth_router.route('/api/v1/auth/register', methods=['POST'])
async def auth_register_v1(request: Request):
    """
    User registration endpoint
    VULNERABILITIES:
    - Weak password validation
    - No rate limiting
    - User enumeration
    """
    data = await safe_json(request)
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    name = data.get('name', '').strip()

    if not username or not email or not password:
        return JSONResponse({'error': 'Username, email, and password required'}, status_code = 400)

    # VULNERABILITY: User enumeration - specific error messages
    if get_demo_mode() == 'full':
        if user_exists_by_username(username):
            return JSONResponse({'error': 'Username already exists'}, status_code = 409)
        if user_exists_by_email(email):
            return JSONResponse({'error': 'Email already registered'}, status_code = 409)
    else:
        # Better: generic message
        if user_exists_by_username(username) or user_exists_by_email(email):
            return JSONResponse({'error': 'User already exists'}, status_code = 409)

    # VULNERABILITY: Weak password validation (only in full mode)
    if get_demo_mode() == 'strict' and len(password) < 8:
        return JSONResponse({'error': 'Password must be at least 8 characters'}, status_code = 400)

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

    return JSONResponse({
        'success': True,
        'message': 'User registered successfully',
        'user_id': user_id,
        'username': username
    }, status_code = 201)


@auth_router.route('/api/v1/auth/forgot', methods=['POST'])
async def auth_forgot(request: Request):
    """
    Password reset initiation
    VULNERABILITIES:
    - Predictable reset tokens (full mode)
    - User enumeration via timing
    - No rate limiting
    """
    data = await safe_json(request)
    email = data.get('email', '').strip().lower()

    if not email:
        return JSONResponse({'error': 'Email required'}, status_code = 400)

    # VULNERABILITY: Timing attack for user enumeration
    timing_attack_user_enum(email)

    # Find user
    user = get_user_by_email(email)

    # VULNERABILITY: In full mode, reveal if user exists
    if get_demo_mode() == 'full' and not user:
        return JSONResponse({'error': 'Email not found'}, status_code = 404)

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

        return JSONResponse({
            'success': True,
            'message': 'Password reset email sent',
            'reset_token': reset_token if get_demo_mode() == 'full' else None  # Leak token in full mode
        }, status_code = 200)

    # Generic response to prevent enumeration (strict mode)
    return JSONResponse({
        'success': True,
        'message': 'If email exists, password reset link has been sent'
    }, status_code = 200)


@auth_router.route('/api/v1/auth/reset', methods=['POST'])
async def auth_reset(request: Request):
    """
    Password reset completion
    VULNERABILITIES:
    - No token expiration check in full mode
    - Weak password validation
    """
    data = await safe_json(request)
    reset_token = data.get('reset_token', '')
    new_password = data.get('new_password', '')

    if not reset_token or not new_password:
        return JSONResponse({'error': 'Reset token and new password required'}, status_code = 400)

    # Check token
    with password_reset_requests_lock:
        reset_req = password_reset_requests.get(reset_token)
        if not reset_req:
            return JSONResponse({'error': 'Invalid reset token'}, status_code = 400)

        if reset_req.get('used'):
            return JSONResponse({'error': 'Reset token already used'}, status_code = 400)

        # VULNERABILITY: No expiration check in full mode
        if get_demo_mode() == 'strict':
            expires_at = datetime.fromisoformat(reset_req.get('expires_at'))
            if datetime.utcnow() > expires_at:
                return JSONResponse({'error': 'Reset token expired'}, status_code = 400)

        # Update password
        user_id = reset_req.get('user_id')
        if not update_user(user_id, {'password_hash': weak_hash_password(new_password)}):
            return JSONResponse({'error': 'User not found'}, status_code = 404)

        reset_req['used'] = True

        return JSONResponse({
            'success': True,
            'message': 'Password reset successful'
        }, status_code = 200)


@auth_router.route('/api/v1/auth/verify', methods=['POST'])
async def auth_verify(request: Request):
    """
    Email/phone verification
    VULNERABILITIES:
    - Predictable verification codes
    - No rate limiting on attempts
    """
    data = await safe_json(request)
    user_id = data.get('user_id', '')
    code = data.get('code', '')

    if not user_id or not code:
        return JSONResponse({'error': 'User ID and verification code required'}, status_code = 400)

    # In demo, accept any 6-digit code in full mode
    if get_demo_mode() == 'full' and len(code) == 6 and code.isdigit():
        if update_user(user_id, {'verified': True}):
            return JSONResponse({
                'success': True,
                'message': 'Verification successful'
            }, status_code = 200)

    return JSONResponse({'error': 'Invalid verification code'}, status_code = 400)


@auth_router.route('/api/v1/auth/refresh', methods=['POST'])
async def auth_refresh_v1(request: Request):
    """
    Token refresh endpoint
    VULNERABILITIES:
    - Accepts expired tokens in full mode
    - No token rotation
    """
    data = await safe_json(request)
    refresh_token = data.get('refresh_token', '')

    if not refresh_token:
        return JSONResponse({'error': 'Refresh token required'}, status_code = 400)

    # Verify refresh token
    with refresh_tokens_db_lock:
        token_data = refresh_tokens_db.get(refresh_token)

    if not token_data:
        return JSONResponse({'error': 'Invalid refresh token'}, status_code = 401)

    # VULNERABILITY: No expiration check in full mode
    if get_demo_mode() == 'strict':
        expires_at = datetime.fromisoformat(token_data.get('expires_at'))
        if datetime.utcnow() > expires_at:
            return JSONResponse({'error': 'Refresh token expired'}, status_code = 401)

    user_id = token_data.get('user_id')
    user = get_user_by_id(user_id)

    if not user:
        return JSONResponse({'error': 'User not found'}, status_code = 404)

    # Generate new access token
    access_token = generate_jwt(request, user_id, user.get('username'))

    return JSONResponse({
        'success': True,
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': 3600
    }, status_code = 200)


@auth_router.route('/api/v1/auth/status', methods=['GET'])
async def auth_status(request: Request):
    """Authentication status check"""
    user_id = request.session.get('user_id')

    if not user_id:
        return JSONResponse({
            'authenticated': False,
            'message': 'Not authenticated'
        }, status_code = 200)

    user = get_user_by_id(user_id)
    if not user:
        return JSONResponse({
            'authenticated': False,
            'message': 'User not found'
        }, status_code = 200)

    return JSONResponse({
        'authenticated': True,
        'user': {
            'user_id': user.get('user_id'),
            'username': user.get('username'),
            'email': user.get('email'),
            'role': user.get('role', 'user')
        }
    }, status_code = 200)


# ============================================================================
# MFA ENDPOINTS
# ============================================================================

@auth_router.route('/api/v1/auth/mfa/enable', methods=['POST'])
async def auth_mfa_enable(request: Request):
    """
    Enable 2FA for user
    VULNERABILITIES:
    - No validation of user session
    - Weak TOTP secret generation
    """
    user_id = request.session.get('user_id')
    if not user_id:
        return JSONResponse({'error': 'Authentication required'}, status_code = 401)

    data = await safe_json(request)
    method = data.get('method', 'totp')  # totp, sms, email

    user = get_user_by_id(user_id)
    if not user:
        return JSONResponse({'error': 'User not found'}, status_code = 404)

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
        return JSONResponse({'error': 'User not found'}, status_code = 404)

    return JSONResponse({
        'success': True,
        'message': 'MFA enabled',
        'method': method,
        'secret': totp_secret,  # In production, only show during setup
        'qr_code_url': f'otpauth://totp/Demo:{user.get("email")}?secret={totp_secret}&issuer=Demo'
    }, status_code = 200)


@auth_router.route('/api/v1/auth/mfa/verify', methods=['POST'])
async def auth_mfa_verify(request: Request):
    """
    Verify MFA code
    VULNERABILITIES:
    - No rate limiting
    - Accepts recent codes in full mode
    """
    data = await safe_json(request)
    challenge_id = data.get('challenge_id', '')
    code = data.get('code', '')

    if not challenge_id or not code:
        return JSONResponse({'error': 'Challenge ID and code required'}, status_code = 400)

    with mfa_challenges_db_lock:
        challenge = mfa_challenges_db.get(challenge_id)
        if not challenge:
            return JSONResponse({'error': 'Invalid challenge'}, status_code = 400)

        # VULNERABILITY: No rate limiting in full mode
        challenge['attempts'] += 1

        too_many = get_demo_mode() == 'strict' and challenge['attempts'] > 3
        matches = code == challenge.get('code')
        user_id = challenge.get('user_id')

        if matches and not too_many:
            # Clean up challenge
            del mfa_challenges_db[challenge_id]

    if too_many:
        return JSONResponse({'error': 'Too many attempts'}, status_code = 429)

    # Verify code
    if matches:
        user = get_user_by_id(user_id)

        if user:
            # Complete login
            request.session['user_id'] = user_id
            request.session['username'] = user.get('username')

            token = generate_jwt(request, user_id, user.get('username'))

            return JSONResponse({
                'success': True,
                'message': 'MFA verification successful',
                'token': token,
                'user': {
                    'user_id': user.get('user_id'),
                    'username': user.get('username'),
                    'email': user.get('email')
                }
            }, status_code = 200)

    return JSONResponse({'error': 'Invalid MFA code'}, status_code = 401)


@auth_router.route('/api/v1/auth/mfa/backup', methods=['POST'])
async def auth_mfa_backup(request: Request):
    """
    Generate MFA backup codes
    VULNERABILITIES:
    - Predictable backup codes in full mode
    """
    user_id = request.session.get('user_id')
    if not user_id:
        return JSONResponse({'error': 'Authentication required'}, status_code = 401)

    user = get_user_by_id(user_id)
    if not user:
        return JSONResponse({'error': 'User not found'}, status_code = 404)

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
        return JSONResponse({'error': 'User not found'}, status_code = 404)

    return JSONResponse({
        'success': True,
        'backup_codes': backup_codes
    }, status_code = 200)


# ============================================================================
# OAUTH/SOCIAL ENDPOINTS
# ============================================================================

@auth_router.route('/api/v1/auth/oauth/authorize', methods=['GET'])
async def oauth_authorize_v1(request: Request):
    """
    OAuth authorization endpoint
    VULNERABILITIES:
    - No redirect URI validation in full mode
    - State parameter not enforced
    """
    client_id = request.query_params.get('client_id', '')
    redirect_uri = request.query_params.get('redirect_uri', '')
    response_type = request.query_params.get('response_type', 'code')
    state = request.query_params.get('state', '')
    scope = request.query_params.get('scope', 'read')

    if not client_id or not redirect_uri:
        return JSONResponse({'error': 'client_id and redirect_uri required'}, status_code = 400)

    # VULNERABILITY: No redirect URI validation in full mode
    if get_demo_mode() == 'strict':
        # Validate redirect_uri against registered clients
        valid_uris = ['http://localhost:3000/callback', 'https://demo.com/callback']
        if redirect_uri not in valid_uris:
            return JSONResponse({'error': 'Invalid redirect_uri'}, status_code = 400)

    # Generate authorization code
    auth_code = generate_weak_token()

    # Store authorization
    request.session['oauth_auth'] = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'code': auth_code,
        'scope': scope,
        'state': state,
        'created_at': datetime.utcnow().isoformat()
    }

    return JSONResponse({
        'authorization_code': auth_code,
        'redirect_uri': redirect_uri,
        'state': state
    }, status_code = 200)


@auth_router.route('/api/v1/auth/oauth/callback', methods=['POST'])
async def oauth_callback_v1(request: Request):
    """
    OAuth callback endpoint
    VULNERABILITIES:
    - No state validation in full mode
    """
    data = await safe_json(request)
    code = data.get('code', '')
    state = data.get('state', '')

    if not code:
        return JSONResponse({'error': 'Authorization code required'}, status_code = 400)

    oauth_auth = request.session.get('oauth_auth')
    if not oauth_auth or oauth_auth.get('code') != code:
        return JSONResponse({'error': 'Invalid authorization code'}, status_code = 400)

    # VULNERABILITY: No state validation in full mode
    if get_demo_mode() == 'strict':
        if state != oauth_auth.get('state'):
            return JSONResponse({'error': 'Invalid state parameter'}, status_code = 400)

    # Generate access token
    user_id = request.session.get('user_id', 'demo-user')
    access_token = generate_jwt(request, user_id, 'oauth_user')

    return JSONResponse({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': 3600,
        'scope': oauth_auth.get('scope')
    }, status_code = 200)


@auth_router.route('/api/v1/auth/social/<provider>', methods=['POST'])
async def social_login(request: Request, provider):
    """
    Social login endpoint
    VULNERABILITIES:
    - No token validation
    - Accepts any provider
    """
    data = await safe_json(request)
    access_token = data.get('access_token', '')

    if not access_token:
        return JSONResponse({'error': 'Access token required'}, status_code = 400)

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

    token = generate_jwt(request, user_id, username)

    return JSONResponse({
        'success': True,
        'token': token,
        'user': get_user_by_id(user_id)
    }, status_code = 200)


# ============================================================================
# SAML ENDPOINTS (Enhanced from existing)
# ============================================================================

@auth_router.route('/api/v1/auth/saml/metadata')
async def saml_metadata_v1(request: Request):
    """SAML metadata endpoint - exposes sensitive configuration"""
    # Intentionally exposes SAML configuration including private keys
    return JSONResponse({
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


@auth_router.route('/api/v1/auth/saml/login', methods=['POST'])
async def saml_login(request: Request):
    """
    SAML SSO login initiation
    VULNERABILITIES:
    - No signature validation in full mode
    """
    data = await safe_json(request)
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

    request.session['saml_request'] = saml_request

    return JSONResponse({
        'saml_request_id': request_id,
        'idp_url': 'https://idp.example.com/sso',
        'relay_state': relay_state
    }, status_code = 200)


@auth_router.route('/api/v1/auth/saml/callback', methods=['POST'])
async def saml_callback(request: Request):
    """
    SAML assertion consumer service
    VULNERABILITIES:
    - No signature validation
    - XML injection possible
    - Accepts any assertion in full mode
    """
    data = await safe_json(request)
    saml_response = data.get('SAMLResponse', '')
    relay_state = data.get('RelayState', '')

    if not saml_response:
        return JSONResponse({'error': 'SAMLResponse required'}, status_code = 400)

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
        request.session['user_id'] = user_id
        request.session['username'] = user.get('username')

        token = generate_jwt(request, user_id, user.get('username'))

        return JSONResponse({
            'success': True,
            'token': token,
            'user': user,
            'relay_state': relay_state
        }, status_code = 200)

    return JSONResponse({'error': 'SAML validation not implemented in strict mode'}, status_code = 501)


# ============================================================================
# API KEY ENDPOINTS
# ============================================================================

@auth_router.route('/api/v1/auth/apikeys', methods=['GET'])
async def auth_apikeys_list(request: Request):
    """
    List API keys for authenticated user
    """
    user_id = request.session.get('user_id')
    if not user_id:
        return JSONResponse({'error': 'Authentication required'}, status_code = 401)

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

    return JSONResponse({
        'api_keys': sanitized_keys
    }, status_code = 200)


@auth_router.route('/api/v1/auth/apikeys/create', methods=['POST'])
async def auth_apikeys_create(request: Request):
    """
    Create new API key
    VULNERABILITIES:
    - Weak key generation in full mode
    - No rate limiting
    """
    user_id = request.session.get('user_id')
    if not user_id:
        return JSONResponse({'error': 'Authentication required'}, status_code = 401)

    data = await safe_json(request)
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

    return JSONResponse({
        'success': True,
        'key_id': key_id,
        'api_key': api_key,  # Only shown once
        'name': name,
        'expires_at': expires_at
    }, status_code = 201)


@auth_router.route('/api/v1/auth/apikeys/revoke', methods=['POST'])
async def auth_apikeys_revoke(request: Request):
    """Revoke API key"""
    user_id = request.session.get('user_id')
    if not user_id:
        return JSONResponse({'error': 'Authentication required'}, status_code = 401)

    data = await safe_json(request)
    key_id = data.get('key_id', '')

    if not key_id:
        return JSONResponse({'error': 'key_id required'}, status_code = 400)

    with api_keys_db_lock:
        key_data = api_keys_db.get(key_id)
        if not key_data:
            return JSONResponse({'error': 'API key not found'}, status_code = 404)

        # Verify ownership
        if key_data.get('user_id') != user_id:
            return JSONResponse({'error': 'Unauthorized'}, status_code = 403)

        # Revoke key
        key_data['revoked'] = True
        key_data['revoked_at'] = datetime.utcnow().isoformat()

    return JSONResponse({
        'success': True,
        'message': 'API key revoked'
    }, status_code = 200)


# ============================================================================
# LEGACY ENDPOINTS (Keep existing routes)
# ============================================================================

@auth_router.route('/api/v1/auth/forgot-password', methods=['POST'])
async def auth_forgot_password(request: Request):
    """Legacy endpoint - redirect to /forgot"""
    return await auth_forgot(request)


@auth_router.route('/api/v1/auth/verify-mfa', methods=['POST'])
async def auth_verify_mfa(request: Request):
    """Legacy endpoint - redirect to /mfa/verify"""
    return await auth_mfa_verify(request)


@auth_router.route('/api/v1/device/register', methods=['POST'])
async def device_register(request: Request):
    """Device binding and registration endpoint"""
    user_id = request.session.get('user_id')
    if not user_id:
        return JSONResponse({'error': 'Authentication required'}, status_code = 401)

    data = await safe_json(request)
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

    return JSONResponse({
        'success': True,
        'device_id': device_id
    }, status_code = 201)


@auth_router.route('/api/v1/auth/api-keys', methods=['POST'])
async def auth_api_keys(request: Request):
    """Legacy endpoint - redirect to /apikeys/create"""
    return await auth_apikeys_create(request)


@auth_router.route('/api/oauth/authorize')
async def oauth_authorize(request: Request):
    """Legacy OAuth endpoint"""
    return await oauth_authorize_v1(request)


@auth_router.route('/api/oauth/token', methods=['POST'])
async def oauth_token(request: Request):
    """Legacy OAuth token endpoint"""
    data = await safe_json(request)
    grant_type = data.get('grant_type', '')
    code = data.get('code', '')

    if grant_type == 'authorization_code':
        return await oauth_callback_v1(request)

    return JSONResponse({'error': 'Unsupported grant_type'}, status_code = 400)


@auth_router.route('/api/auth/register', methods=['POST'])
async def auth_register(request: Request):
    """Legacy registration endpoint"""
    return await auth_register_v1(request)


@auth_router.route('/api/oauth/token/forge', methods=['POST'])
async def oauth_token_forge(request: Request):
    """
    OAuth token endpoint - vulnerable to token forgery
    VULNERABILITY: Allows arbitrary token generation
    """
    data = await safe_json(request)
    client_id = data.get('client_id', 'unknown')
    username = data.get('username', 'forged_user')

    if get_demo_mode() != 'full':
        return JSONResponse({'error': 'Endpoint requires DEMO_MODE=full'}, status_code = 403)

    # VULNERABILITY: Generate token without authentication
    user_id = str(uuid.uuid4())
    token = generate_jwt(request, user_id, username, expires_in=86400)

    return JSONResponse({
        'access_token': token,
        'token_type': 'Bearer',
        'expires_in': 86400,
        'warning': 'Token forged without authentication'
    }, status_code = 200)


@auth_router.route('/api/saml/metadata')
async def saml_metadata(request: Request):
    """Legacy SAML metadata endpoint"""
    return await saml_metadata_v1(request)


@auth_router.route('/api/saml/sso', methods=['POST'])
async def saml_sso(request: Request):
    """Legacy SAML SSO endpoint"""
    return await saml_login(request)
