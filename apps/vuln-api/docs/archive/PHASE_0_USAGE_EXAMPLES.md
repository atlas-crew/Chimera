# Phase 0 Foundations: Usage Examples

This document provides practical examples of using the Phase 0 shared foundations in your blueprints.

## Table of Contents
1. [Data Access Layer](#data-access-layer)
2. [Input Validation](#input-validation)
3. [Response Helpers](#response-helpers)
4. [Authentication](#authentication)
5. [Monitoring](#monitoring)
6. [Complete Endpoint Example](#complete-endpoint-example)

---

## Data Access Layer

### Basic CRUD Operations

```python
from app.models import get_store

# Get a user store
users_store = get_store('users')

# Create a user
user_id = users_store.create('user_123', {
    'name': 'John Doe',
    'email': 'john@example.com',
    'role': 'admin'
})

# Read a user
user = users_store.read('user_123')
print(f"User: {user['name']}")

# Update a user
users_store.update('user_123', {'last_login': '2025-10-11'}, merge=True)

# Check if user exists
if users_store.exists('user_123'):
    print("User exists")

# Delete a user
users_store.delete('user_123')
```

### Finding Records

```python
from app.models import get_store

orders_store = get_store('orders')

# Find all pending orders
pending_orders = orders_store.find(
    lambda order: order.get('status') == 'pending',
    limit=10
)

# Find all orders over $100
high_value_orders = orders_store.find(
    lambda order: order.get('total', 0) > 100
)
```

### Using Transactional Store

```python
from app.models import get_store, TransactionalDataStore

# Get a transactional store for event logs
events_store = get_store('events', store_class=TransactionalDataStore)

# Append events
events_store.append('user_123_events', {
    'type': 'login',
    'ip': '192.168.1.1'
})

# Get recent events
recent_events = events_store.get_range('user_123_events', start=-10)

# Increment a counter
new_count = events_store.increment('stats', 'login_count')
```

---

## Input Validation

### Basic Field Validation

```python
from app.utils import (
    validate_email,
    validate_string,
    validate_integer,
    ValidationError
)
from flask import request

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()

    try:
        # Validate email
        validate_email(data.get('email'))

        # Validate username
        validate_string(
            data.get('username'),
            'username',
            min_length=3,
            max_length=50
        )

        # Validate age
        validate_integer(
            data.get('age'),
            'age',
            min_value=18,
            max_value=120
        )

        # Create user...
        return success_response({'user_id': '123'})

    except ValidationError as e:
        return error_response(
            message=e.message,
            code=e.code,
            status_code=400,
            details={'field': e.field}
        )
```

### Security Checks

```python
from app.utils import (
    check_sql_injection,
    check_xss,
    check_path_traversal,
    ValidationError
)
from flask import request

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '')

    try:
        # Check for SQL injection
        check_sql_injection(query, 'query')

        # Check for XSS
        check_xss(query, 'query')

        # Perform search...
        return success_response({'results': []})

    except ValidationError as e:
        return error_response(
            message='Invalid search query',
            code='SECURITY_VIOLATION',
            status_code=400
        )
```

### Using Validation Decorator

```python
from app.utils import validate_json_request
from flask import request

@app.route('/api/users', methods=['POST'])
@validate_json_request(required_fields=['email', 'name', 'password'])
def create_user():
    # If we get here, all required fields are present
    data = request.get_json()

    # Create user...
    return success_response({'user_id': '123'})
```

### Vulnerable Endpoint (For WAF Testing)

```python
from app.utils import validate_string, check_sql_injection
from flask import request

@app.route('/api/vulnerable/search', methods=['GET'])
def vulnerable_search():
    # Bypass validation for WAF testing
    query = request.args.get('q', '')

    try:
        # Validate but allow bypass
        check_sql_injection(query, 'query', bypass=True)

        # This endpoint intentionally accepts dangerous input
        # for WAF testing purposes
        results = unsafe_search(query)
        return success_response({'results': results})

    except Exception as e:
        return error_response(str(e), 'ERROR', 500)
```

---

## Response Helpers

### Success Responses

```python
from app.utils import success_response, created_response

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = get_user_by_id(user_id)

    return success_response(
        data={'user': user},
        message='User retrieved successfully'
    )

@app.route('/api/users', methods=['POST'])
def create_user():
    user = create_new_user(request.get_json())

    return created_response(
        data={'user': user},
        resource_url=f'/api/users/{user["id"]}',
        message='User created successfully'
    )
```

### Error Responses

```python
from app.utils import (
    not_found_response,
    unauthorized_response,
    forbidden_response,
    conflict_response
)

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = get_user_by_id(user_id)

    if not user:
        return not_found_response('User', user_id)

    return success_response(data={'user': user})

@app.route('/api/admin/users', methods=['GET'])
def list_admin_users():
    if not current_user_is_admin():
        return forbidden_response(
            message='Admin access required',
            code='INSUFFICIENT_PERMISSIONS'
        )

    users = get_all_users()
    return success_response(data={'users': users})

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    email = data.get('email')

    if email_exists(email):
        return conflict_response(
            message='Email already registered',
            resource='User',
            details={'email': email}
        )

    user = create_new_user(data)
    return created_response(data={'user': user})
```

### Paginated Responses

```python
from app.utils import paginated_response
from flask import request

@app.route('/api/users', methods=['GET'])
def list_users():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    # Get paginated users
    users, total_count = get_users_paginated(page, per_page)

    return paginated_response(
        items=users,
        page=page,
        per_page=per_page,
        total_items=total_count
    )
```

---

## Authentication

### Token-Based Authentication

```python
from app.utils import generate_token, verify_token, TokenError
from flask import request

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Verify credentials
    user = authenticate_user(email, password)
    if not user:
        return unauthorized_response(message='Invalid credentials')

    # Generate token
    token = generate_token(
        user_id=user['id'],
        additional_claims={'role': user['role']},
        expiry_seconds=3600
    )

    return success_response(data={'token': token, 'user': user})

@app.route('/api/auth/verify', methods=['POST'])
def verify():
    auth_header = request.headers.get('Authorization')
    token = auth_header.split()[1] if auth_header else None

    if not token:
        return unauthorized_response()

    try:
        payload = verify_token(token)
        return success_response(data={'user_id': payload['user_id']})
    except TokenError:
        return unauthorized_response(message='Invalid or expired token')
```

### Using Authentication Decorator

```python
from app.utils import require_auth, require_role
from flask import g

@app.route('/api/profile', methods=['GET'])
@require_auth()
def get_profile():
    # User ID is available in g.user_id (set by decorator)
    user = get_user_by_id(g.user_id)
    return success_response(data={'user': user})

@app.route('/api/admin/users', methods=['GET'])
@require_auth()
@require_role(['admin', 'superuser'])
def list_admin_users():
    # Only admin and superuser can access
    users = get_all_users()
    return success_response(data={'users': users})
```

### API Key Authentication

```python
from app.utils import generate_api_key
from flask import request

@app.route('/api/keys', methods=['POST'])
@require_auth()
def create_api_key():
    # Generate API key for authenticated user
    api_key = generate_api_key(prefix='tx_', length=32)

    # Store API key
    save_api_key(g.user_id, api_key)

    return created_response(data={'api_key': api_key})
```

### Password Management

```python
from app.utils import hash_password, verify_password

def create_user_account(email, password):
    # Hash password before storing
    hashed_password, salt = hash_password(password)

    user = {
        'email': email,
        'password': hashed_password,
        'salt': salt
    }

    save_user(user)
    return user

def authenticate_user(email, password):
    user = get_user_by_email(email)
    if not user:
        return None

    # Verify password
    if verify_password(password, user['password'], user['salt']):
        return user

    return None
```

---

## Monitoring

### Request Logging

```python
from app.utils import log_request

@app.route('/api/users', methods=['POST'])
@log_request(include_body=True, max_body_size=2048)
def create_user():
    # Request details are automatically logged
    user = create_new_user(request.get_json())
    return created_response(data={'user': user})
```

### Performance Tracking

```python
from app.utils import track_performance

@track_performance('user_search')
def search_users(query):
    # Performance metrics are automatically collected
    results = expensive_search_operation(query)
    return results

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q')
    results = search_users(query)
    return success_response(data={'results': results})
```

### Audit Logging

```python
from app.utils import log_audit_event
from flask import g

@app.route('/api/medical-records/<record_id>', methods=['GET'])
@require_auth()
def get_medical_record(record_id):
    record = get_record(record_id)

    if not record:
        return not_found_response('Medical Record', record_id)

    # Log access to sensitive data
    log_audit_event(
        event_type='data_access',
        user_id=g.user_id,
        resource='medical_record',
        resource_id=record_id,
        action='read',
        details={'reason': 'patient_portal_access'},
        severity='INFO'
    )

    return success_response(data={'record': record})
```

### Security Event Logging

```python
from app.utils import log_security_event

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')

    user = authenticate_user(email, data.get('password'))

    if not user:
        # Log failed authentication
        log_security_event(
            event_type='failed_auth',
            severity='WARNING',
            description='Failed login attempt',
            details={'email': email, 'ip': request.remote_addr}
        )
        return unauthorized_response()

    # Successful login
    token = generate_token(user_id=user['id'])
    return success_response(data={'token': token})
```

### Metrics Collection

```python
from app.utils import metrics

@app.route('/api/orders', methods=['POST'])
def create_order():
    # Increment order counter
    metrics.increment_counter('orders.created', tags={'source': 'api'})

    order = create_new_order(request.get_json())

    # Record order value
    metrics.record_histogram(
        'orders.value',
        order['total'],
        tags={'currency': 'USD'}
    )

    return created_response(data={'order': order})

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    # Export current metrics
    current_metrics = metrics.get_metrics()
    return success_response(data=current_metrics)
```

---

## Complete Endpoint Example

Here's a complete example combining all foundations:

```python
from flask import Blueprint, request, g
from app.utils import (
    # Validation
    validate_email,
    validate_string,
    validate_integer,
    ValidationError,
    sanitize_input,
    # Responses
    success_response,
    created_response,
    not_found_response,
    conflict_response,
    error_response,
    # Auth
    require_auth,
    hash_password,
    # Monitoring
    log_request,
    track_performance,
    log_audit_event,
    log_security_event,
    metrics,
    logger
)
from app.models import get_store

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

# Get user store
users_store = get_store('users')


@users_bp.route('', methods=['POST'])
@log_request(include_body=True)
def create_user():
    """
    Create a new user account.

    Request Body:
        {
            "email": "user@example.com",
            "name": "John Doe",
            "password": "secure_password",
            "age": 25
        }

    Returns:
        201: User created successfully
        400: Validation error
        409: Email already exists
    """
    try:
        data = request.get_json()

        # Sanitize input
        allowed_fields = ['email', 'name', 'password', 'age']
        data = sanitize_input(data, allowed_fields)

        # Validate fields
        validate_email(data.get('email'))
        validate_string(data.get('name'), 'name', min_length=2, max_length=100)
        validate_string(data.get('password'), 'password', min_length=8)
        validate_integer(data.get('age'), 'age', min_value=18, max_value=120)

        # Check for existing user
        if users_store.exists(data['email']):
            return conflict_response(
                message='Email already registered',
                resource='User',
                details={'email': data['email']}
            )

        # Hash password
        hashed_password, salt = hash_password(data['password'])

        # Create user
        user = {
            'email': data['email'],
            'name': data['name'],
            'password': hashed_password,
            'salt': salt,
            'age': data['age']
        }

        user_id = users_store.create(data['email'], user, auto_id=True)

        # Log audit event
        log_audit_event(
            event_type='user_management',
            resource='user',
            resource_id=user_id,
            action='create',
            details={'email': data['email']}
        )

        # Update metrics
        metrics.increment_counter('users.created')

        # Return success
        return created_response(
            data={'user_id': user_id, 'email': data['email']},
            resource_url=f'/api/users/{user_id}',
            message='User created successfully'
        )

    except ValidationError as e:
        return error_response(
            message=e.message,
            code=e.code,
            status_code=400,
            details={'field': e.field}
        )
    except Exception as e:
        logger.error('Failed to create user', exc_info=True)
        return error_response(
            message='Failed to create user',
            code='INTERNAL_ERROR',
            status_code=500
        )


@users_bp.route('/<user_id>', methods=['GET'])
@require_auth()
@log_request()
@track_performance('get_user')
def get_user(user_id):
    """
    Get user details by ID.

    Requires authentication.

    Returns:
        200: User details
        404: User not found
    """
    # Check authorization
    if g.user_id != user_id and not is_admin(g.user_id):
        return forbidden_response(
            message='You can only view your own profile'
        )

    # Get user
    user = users_store.read(user_id)

    if not user:
        return not_found_response('User', user_id)

    # Log access
    log_audit_event(
        event_type='data_access',
        user_id=g.user_id,
        resource='user',
        resource_id=user_id,
        action='read'
    )

    # Remove sensitive data
    safe_user = {
        'id': user_id,
        'email': user['email'],
        'name': user['name'],
        'age': user.get('age')
    }

    return success_response(data={'user': safe_user})


@users_bp.route('/<user_id>', methods=['PUT'])
@require_auth()
@log_request(include_body=True)
def update_user(user_id):
    """
    Update user details.

    Requires authentication and ownership.

    Request Body:
        {
            "name": "Updated Name",
            "age": 26
        }

    Returns:
        200: User updated successfully
        403: Unauthorized
        404: User not found
    """
    # Check authorization
    if g.user_id != user_id:
        log_security_event(
            event_type='unauthorized_access',
            severity='WARNING',
            description='User attempted to update another user',
            details={'actor': g.user_id, 'target': user_id}
        )
        return forbidden_response(
            message='You can only update your own profile'
        )

    try:
        data = request.get_json()

        # Validate updates
        if 'name' in data:
            validate_string(data['name'], 'name', min_length=2, max_length=100)
        if 'age' in data:
            validate_integer(data['age'], 'age', min_value=18, max_value=120)

        # Check user exists
        if not users_store.exists(user_id):
            return not_found_response('User', user_id)

        # Update user
        updated = users_store.update(user_id, data, merge=True)

        if not updated:
            return error_response('Failed to update user', 'UPDATE_FAILED', 500)

        # Log audit event
        log_audit_event(
            event_type='user_management',
            user_id=g.user_id,
            resource='user',
            resource_id=user_id,
            action='update',
            details={'fields': list(data.keys())}
        )

        # Get updated user
        user = users_store.read(user_id)

        return success_response(
            data={'user': user},
            message='User updated successfully'
        )

    except ValidationError as e:
        return error_response(
            message=e.message,
            code=e.code,
            status_code=400,
            details={'field': e.field}
        )
```

---

## Additional Examples

### Demo Data Management

```python
from app.utils import (
    reset_demo_data,
    get_demo_user,
    seed_additional_users,
    get_seed_statistics
)

@app.route('/api/admin/reset-demo', methods=['POST'])
@require_auth()
@require_role(['admin'])
def reset_demo():
    """Reset all demo data to initial state."""
    reset_demo_data()
    stats = get_seed_statistics()

    return success_response(
        data={'stats': stats},
        message='Demo data reset successfully'
    )

@app.route('/api/admin/seed-data', methods=['POST'])
@require_auth()
@require_role(['admin'])
def seed_data():
    """Seed additional test data."""
    data = request.get_json()
    user_count = data.get('user_count', 10)

    users = seed_additional_users(user_count)

    return success_response(
        data={'created_users': len(users)},
        message=f'Seeded {len(users)} users'
    )
```

### Request ID Middleware

```python
from app.utils import request_id_middleware

def create_app():
    app = Flask(__name__)

    # Add request ID middleware
    request_id_middleware(app)

    # All requests now have request IDs in headers and logs

    return app
```

This comprehensive set of examples should help you integrate the Phase 0 foundations into your blueprints!
