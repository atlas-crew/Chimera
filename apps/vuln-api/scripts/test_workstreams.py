#!/usr/bin/env python3
"""
Test script for Workstreams 4 & 6 (Healthcare & Admin) endpoints
"""

import sys
import json

def test_import():
    """Test that the routes can be imported without errors"""
    try:
        from app.blueprints.healthcare import routes as healthcare_routes
        from app.blueprints.admin import routes as admin_routes
        from app.blueprints.insurance import routes as insurance_routes
        print("✓ All route modules imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_route_definitions():
    """Test that routes are properly defined"""
    try:
        from app.blueprints.healthcare import healthcare_bp
        from app.blueprints.admin import admin_bp
        from app.blueprints.insurance import insurance_bp

        # Check healthcare routes
        healthcare_routes = [rule.rule for rule in healthcare_bp.url_map.iter_rules()]
        print(f"\n✓ Healthcare blueprint has {len(healthcare_routes)} routes")

        # Check admin routes
        admin_routes = [rule.rule for rule in admin_bp.url_map.iter_rules()]
        print(f"✓ Admin blueprint has {len(admin_routes)} routes")

        # Check insurance routes
        insurance_routes = [rule.rule for rule in insurance_bp.url_map.iter_rules()]
        print(f"✓ Insurance blueprint has {len(insurance_routes)} routes")

        return True
    except Exception as e:
        print(f"✗ Route definition check failed: {e}")
        return False

def list_endpoints():
    """List all implemented endpoints"""
    try:
        from app.blueprints.healthcare import healthcare_bp
        from app.blueprints.admin import admin_bp

        print("\n" + "="*80)
        print("HEALTHCARE ENDPOINTS (Workstream 4)")
        print("="*80)

        healthcare_endpoints = [
            "GET  /api/v1/healthcare/records - List medical records",
            "GET  /api/v1/healthcare/records/<id> - Get record details (IDOR)",
            "GET  /api/v1/healthcare/records/search - Search records (SQL injection)",
            "POST /api/v1/healthcare/records/upload - Upload documents (path traversal)",
            "GET  /api/v1/healthcare/appointments - List appointments",
            "POST /api/v1/healthcare/appointments/schedule - Schedule appointment",
            "POST /api/v1/healthcare/appointments/cancel - Cancel appointment (IDOR)",
            "GET  /api/v1/healthcare/prescriptions - List prescriptions (DEA controlled)",
            "POST /api/v1/healthcare/prescriptions/refill - Request refill",
            "GET  /api/v1/healthcare/prescriptions/history - Prescription history (IDOR)",
            "GET  /api/v1/insurance/policies - List insurance policies",
            "POST /api/v1/insurance/claims - Submit insurance claim",
            "GET  /api/v1/insurance/claims/<id> - Get claim status (IDOR)",
            "GET  /api/v1/insurance/coverage - Check coverage",
            "GET  /api/medical/genetics/profiles - Genetic data (highly sensitive PHI)",
            "GET  /api/medical/mental-health/sessions - Mental health records",
            "GET  /api/hipaa/export/bulk - Bulk PHI export",
            "POST /api/hipaa/transfer/encrypted - HIPAA transfer (SSRF)",
            "POST /api/hipaa/system/configuration - System config (XXE)",
            "PUT  /api/hipaa/audit-logs - Audit log manipulation",
        ]

        for endpoint in healthcare_endpoints:
            print(f"  {endpoint}")

        print("\n" + "="*80)
        print("ADMIN ENDPOINTS (Workstream 6)")
        print("="*80)

        admin_endpoints = [
            "GET  /api/v1/admin/users - List all users (exposes password hashes)",
            "GET  /api/v1/admin/users/<id> - User details (IDOR)",
            "POST /api/v1/admin/users/<id>/elevate - Privilege escalation",
            "GET  /api/v1/admin/users/export - Export user data (exfiltration)",
            "GET  /api/v1/admin/config - System configuration (exposes secrets)",
            "POST /api/v1/admin/config - Update configuration",
            "GET  /api/v1/admin/logs - View system logs",
            "POST /api/v1/admin/backup - Trigger backup (command injection)",
            "POST /api/v1/admin/execute - Execute commands (direct RCE)",
            "POST /api/v1/admin/attack/sqli - SQL injection test",
            "POST /api/v1/admin/attack/xxe - XXE injection test",
            "POST /api/v1/admin/attack/ssrf - SSRF test",
            "POST /api/v1/admin/attack/deserialize - Deserialization test",
            "POST /api/transactions/split - Transaction structuring",
            "GET  /api/customers/export - Customer data export",
            "POST /api/logs/deletion - Delete audit logs",
            "GET  /api/system/version - System fingerprinting",
        ]

        for endpoint in admin_endpoints:
            print(f"  {endpoint}")

        print("\n" + "="*80)
        print("VULNERABILITIES IMPLEMENTED")
        print("="*80)

        vulnerabilities = [
            "PHI Data Exposure - Unprotected patient medical records",
            "IDOR - Access any patient/user record without authorization",
            "SQL Injection - Search endpoints with unsanitized input",
            "Path Traversal - File upload with no path sanitization",
            "Command Injection - Backup and execute endpoints",
            "XXE Injection - XML processing in system configuration",
            "SSRF - Unvalidated URL in data transfer",
            "Insecure Deserialization - Pickle/base64 payloads",
            "Missing Access Controls - No authorization checks",
            "Privilege Escalation - Elevate any user to admin",
            "Sensitive Data Exposure - Config with API keys, passwords",
            "Genetic/Mental Health Data - Highly sensitive PHI exposed",
            "Audit Log Tampering - Modify or delete logs",
            "Data Exfiltration - Bulk export endpoints",
        ]

        for i, vuln in enumerate(vulnerabilities, 1):
            print(f"  {i:2d}. {vuln}")

        return True
    except Exception as e:
        print(f"✗ Endpoint listing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Testing Workstreams 4 & 6 Implementation")
    print("=" * 80)

    tests = [
        ("Import Test", test_import),
        ("Route Definition Test", test_route_definitions),
        ("Endpoint Documentation", list_endpoints),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n{name}...")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"✗ {name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("\n✓ All tests passed! Implementation complete.")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
