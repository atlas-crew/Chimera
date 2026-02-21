#!/usr/bin/env python3
"""
Quick test script to verify error handlers and testing endpoints.

Run with: python test_error_handlers.py
"""

from app import create_app
import json


def test_error_handlers():
    """Test that error handlers are working correctly."""
    app = create_app()
    client = app.test_client()

    print("Testing Error Handlers and Testing Blueprint")
    print("=" * 60)

    # Test 1: Health check
    print("\n1. Testing health check endpoint...")
    response = client.get('/api/test/health')
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    print("   ✓ Health check passed")

    # Test 2: 404 Not Found handler
    print("\n2. Testing 404 handler...")
    response = client.get('/nonexistent/endpoint')
    print(f"   Status: {response.status_code}")
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'NotFound'
    assert 'stack_trace' in data or 'exception_details' in data
    print(f"   ✓ 404 handler working - leaked {len(data.keys())} fields")

    # Test 3: Generic exception
    print("\n3. Testing exception trigger...")
    response = client.get('/api/test/error/exception?message=Test')
    print(f"   Status: {response.status_code}")
    assert response.status_code == 500
    data = response.get_json()
    assert data['error'] == 'Exception'
    assert 'stack_trace' in data
    assert 'stack_frames' in data
    print(f"   ✓ Exception handler working - stack has {len(data['stack_trace'])} frames")

    # Test 4: Division by zero
    print("\n4. Testing divide by zero...")
    response = client.get('/api/test/error/divide_zero')
    print(f"   Status: {response.status_code}")
    assert response.status_code == 500
    data = response.get_json()
    assert data['error'] == 'ZeroDivisionError'
    assert 'stack_trace' in data
    print("   ✓ Division by zero caught")

    # Test 5: Status code endpoint
    print("\n5. Testing status code endpoint...")
    response = client.get('/api/test/status/418?message=I am a teapot')
    print(f"   Status: {response.status_code}")
    assert response.status_code == 418
    data = response.get_json()
    assert data['status_code'] == 418
    assert "teapot" in data['message']
    print("   ✓ Custom status code working")

    # Test 6: Timeout (quick test)
    print("\n6. Testing timeout endpoint...")
    response = client.get('/api/test/error/timeout?delay=0')
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200
    data = response.get_json()
    assert data['error_type'] == 'timeout'
    print("   ✓ Timeout endpoint working")

    # Test 7: Header leak
    print("\n7. Testing header leak endpoint...")
    response = client.get(
        '/api/test/leak/headers?test=value',
        headers={'X-Custom-Header': 'secret-value'}
    )
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200
    data = response.get_json()
    assert 'headers' in data
    assert 'X-Custom-Header' in data['headers']
    print(f"   ✓ Header leak working - leaked {len(data['headers'])} headers")

    # Test 8: Config leak
    print("\n8. Testing config leak endpoint...")
    response = client.get('/api/test/leak/config')
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200
    data = response.get_json()
    assert 'config' in data
    assert 'secret_key' in data
    assert 'blueprints' in data
    print(f"   ✓ Config leak working - leaked {len(data['config'])} config keys")

    # Test 9: Status code with abort
    print("\n9. Testing status code with abort (triggers error handler)...")
    response = client.get('/api/test/status/403?abort=true&message=Access Denied')
    print(f"   Status: {response.status_code}")
    assert response.status_code == 403
    data = response.get_json()
    assert data['error'] == 'Forbidden'
    assert 'permission_debug' in data
    print("   ✓ Abort triggering error handler correctly")

    # Test 10: SQL injection test
    print("\n10. Testing SQL injection error simulation...")
    response = client.get('/api/test/error/sql?username=admin&password=test')
    print(f"   Status: {response.status_code}")
    assert response.status_code == 500
    data = response.get_json()
    assert 'SELECT * FROM users' in str(data)
    print("   ✓ SQL error simulation working")

    print("\n" + "=" * 60)
    print("All tests passed! Error handlers are working correctly.")
    print("\nKey features verified:")
    print("  ✓ Verbose error responses with stack traces")
    print("  ✓ Request data leakage (headers, body, cookies)")
    print("  ✓ System information leakage")
    print("  ✓ Multiple error type triggers")
    print("  ✓ Custom status code responses")
    print("  ✓ Configuration and environment leaks")
    print("\nWARNING: This is intentionally insecure for WAF testing!")
    print("=" * 60)


if __name__ == '__main__':
    test_error_handlers()
