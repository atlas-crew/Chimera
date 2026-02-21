#!/bin/bash
# Test script for Workstream 1: Auth & Identity
# Tests all implemented endpoints with both secure and vulnerable modes

set -e

BASE_URL="${BASE_URL:-http://localhost:5000}"
DEMO_MODE="${DEMO_MODE:-full}"

echo "================================================"
echo "Workstream 1: Auth & Identity Test Suite"
echo "================================================"
echo "Base URL: $BASE_URL"
echo "DEMO_MODE: $DEMO_MODE"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success_count=0
fail_count=0

test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_code="$5"

    echo -n "Testing: $name... "

    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>&1)
    fi

    http_code=$(echo "$response" | tail -n 1)

    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        ((success_count++))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_code, got $http_code)"
        ((fail_count++))
    fi
}

test_vulnerability() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local search_pattern="$5"

    echo -n "Testing Vuln: $name... "

    response=$(curl -s -X "$method" "$BASE_URL$endpoint" \
        -H "Content-Type: application/json" \
        -d "$data" 2>&1)

    if echo "$response" | grep -q "$search_pattern"; then
        echo -e "${YELLOW}⚠ VULNERABLE${NC} (Pattern found: $search_pattern)"
        ((success_count++))
    else
        echo -e "${GREEN}✓ PROTECTED${NC}"
        ((fail_count++))
    fi
}

echo "=== Core Authentication Endpoints ==="
echo ""

# Test 1: Auth Methods Discovery
test_endpoint "Auth Methods" "GET" "/api/v1/auth/methods" "" "200"

# Test 2: User Registration
test_endpoint "User Registration" "POST" "/api/v1/auth/register" \
    '{"username":"testuser1","email":"test1@demo.com","password":"TestPass123"}' "201"

# Test 3: User Login (normal)
test_endpoint "User Login (Normal)" "POST" "/api/v1/auth/login" \
    '{"username":"testuser1","password":"TestPass123"}' "200"

# Test 4: User Login (invalid)
test_endpoint "User Login (Invalid)" "POST" "/api/v1/auth/login" \
    '{"username":"testuser1","password":"wrong"}' "401"

# Test 5: Auth Status (unauthenticated)
test_endpoint "Auth Status" "GET" "/api/v1/auth/status" "" "200"

# Test 6: Password Reset Request
test_endpoint "Password Reset Request" "POST" "/api/v1/auth/forgot" \
    '{"email":"test1@demo.com"}' "200"

# Test 7: Logout
test_endpoint "Logout" "POST" "/api/v1/auth/logout" "" "200"

echo ""
echo "=== MFA Endpoints ==="
echo ""

# Test 8: MFA Enable (will fail without session, but endpoint should exist)
test_endpoint "MFA Enable" "POST" "/api/v1/auth/mfa/enable" \
    '{"method":"totp"}' "401"

# Test 9: MFA Verify (invalid challenge)
test_endpoint "MFA Verify" "POST" "/api/v1/auth/mfa/verify" \
    '{"challenge_id":"invalid","code":"123456"}' "400"

# Test 10: MFA Backup Codes (unauthenticated)
test_endpoint "MFA Backup Codes" "POST" "/api/v1/auth/mfa/backup" "" "401"

echo ""
echo "=== OAuth/Social Endpoints ==="
echo ""

# Test 11: OAuth Authorize
test_endpoint "OAuth Authorize" "GET" "/api/v1/auth/oauth/authorize?client_id=test&redirect_uri=http://localhost/callback" "" "200"

# Test 12: OAuth Callback (invalid code)
test_endpoint "OAuth Callback" "POST" "/api/v1/auth/oauth/callback" \
    '{"code":"invalid"}' "400"

# Test 13: Social Login
test_endpoint "Social Login (Google)" "POST" "/api/v1/auth/social/google" \
    '{"access_token":"fake_token"}' "200"

echo ""
echo "=== SAML Endpoints ==="
echo ""

# Test 14: SAML Metadata
test_endpoint "SAML Metadata" "GET" "/api/v1/auth/saml/metadata" "" "200"

# Test 15: SAML Login
test_endpoint "SAML Login" "POST" "/api/v1/auth/saml/login" \
    '{"RelayState":"test"}' "200"

# Test 16: SAML Callback (requires full mode)
if [ "$DEMO_MODE" = "full" ]; then
    test_endpoint "SAML Callback" "POST" "/api/v1/auth/saml/callback" \
        '{"SAMLResponse":"{\"nameid\":\"saml@demo.com\"}"}' "200"
else
    test_endpoint "SAML Callback" "POST" "/api/v1/auth/saml/callback" \
        '{"SAMLResponse":"test"}' "501"
fi

echo ""
echo "=== API Key Endpoints ==="
echo ""

# Test 17: List API Keys (unauthenticated)
test_endpoint "List API Keys" "GET" "/api/v1/auth/apikeys" "" "401"

# Test 18: Create API Key (unauthenticated)
test_endpoint "Create API Key" "POST" "/api/v1/auth/apikeys/create" \
    '{"name":"Test Key"}' "401"

# Test 19: Revoke API Key (unauthenticated)
test_endpoint "Revoke API Key" "POST" "/api/v1/auth/apikeys/revoke" \
    '{"key_id":"test"}' "401"

echo ""
echo "=== Legacy Endpoints ==="
echo ""

# Test 20: Legacy forgot-password
test_endpoint "Legacy Forgot Password" "POST" "/api/v1/auth/forgot-password" \
    '{"email":"test@demo.com"}' "200"

# Test 21: Legacy verify-mfa
test_endpoint "Legacy Verify MFA" "POST" "/api/v1/auth/verify-mfa" \
    '{"challenge_id":"invalid","code":"123456"}' "400"

# Test 22: Device Register (unauthenticated)
test_endpoint "Device Register" "POST" "/api/v1/device/register" \
    '{"device_name":"Test Device"}' "401"

# Test 23: Legacy OAuth Authorize
test_endpoint "Legacy OAuth Authorize" "GET" "/api/oauth/authorize?client_id=test&redirect_uri=http://localhost/callback" "" "200"

# Test 24: Legacy OAuth Token
test_endpoint "Legacy OAuth Token" "POST" "/api/oauth/token" \
    '{"grant_type":"authorization_code","code":"invalid"}' "400"

# Test 25: Legacy Auth Register
test_endpoint "Legacy Auth Register" "POST" "/api/auth/register" \
    '{"username":"testuser2","email":"test2@demo.com","password":"TestPass123"}' "201"

# Test 26: Legacy SAML Metadata
test_endpoint "Legacy SAML Metadata" "GET" "/api/saml/metadata" "" "200"

# Test 27: Legacy SAML SSO
test_endpoint "Legacy SAML SSO" "POST" "/api/saml/sso" \
    '{"RelayState":"test"}' "200"

echo ""
echo "=== Vulnerability Tests (DEMO_MODE=$DEMO_MODE) ==="
echo ""

if [ "$DEMO_MODE" = "full" ]; then
    echo "Running vulnerability tests..."
    echo ""

    # Vuln 1: SQL Injection
    test_vulnerability "SQL Injection in Login" "POST" "/api/v1/auth/login" \
        '{"username":"admin'\'' --","password":"anything"}' "injection"

    # Vuln 2: User Enumeration (specific error)
    test_vulnerability "User Enumeration (Register)" "POST" "/api/v1/auth/register" \
        '{"username":"testuser1","email":"new@demo.com","password":"test"}' "already exists"

    # Vuln 3: Reset Token Leakage
    test_vulnerability "Reset Token Leakage" "POST" "/api/v1/auth/forgot" \
        '{"email":"test1@demo.com"}' "reset_token"

    # Vuln 4: SAML Private Key Exposure
    test_vulnerability "SAML Private Key Exposure" "GET" "/api/v1/auth/saml/metadata" \
        "" "BEGIN PRIVATE KEY"

    # Vuln 5: Token Forgery Endpoint
    test_vulnerability "Token Forgery" "POST" "/api/oauth/token/forge" \
        '{"client_id":"test","username":"forged_user"}' "access_token"

    # Vuln 6: Open Redirect (OAuth)
    echo -n "Testing Vuln: OAuth Open Redirect... "
    response=$(curl -s "$BASE_URL/api/v1/auth/oauth/authorize?client_id=test&redirect_uri=https://evil.com/phishing")
    if echo "$response" | grep -q "evil.com"; then
        echo -e "${YELLOW}⚠ VULNERABLE${NC}"
        ((success_count++))
    else
        echo -e "${GREEN}✓ PROTECTED${NC}"
        ((fail_count++))
    fi

    # Vuln 7: JWT Algorithm Confusion
    echo -n "Testing Vuln: JWT Algorithm Confusion... "
    response=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -H "X-JWT-Algorithm: none" \
        -d '{"username":"testuser1","password":"TestPass123"}')
    # Check if token is returned (vulnerable behavior)
    if echo "$response" | grep -q "token"; then
        echo -e "${YELLOW}⚠ ACCEPTS NONE ALG${NC}"
        ((success_count++))
    else
        echo -e "${GREEN}✓ PROTECTED${NC}"
        ((fail_count++))
    fi

    # Vuln 8: SAML Injection
    test_vulnerability "SAML Injection" "POST" "/api/v1/auth/saml/callback" \
        '{"SAMLResponse":"{\"nameid\":\"attacker@evil.com\"}"}' "success"

else
    echo -e "${YELLOW}Skipping vulnerability tests (DEMO_MODE=strict)${NC}"
    echo "Set DEMO_MODE=full to test vulnerabilities"
fi

echo ""
echo "================================================"
echo "Test Summary"
echo "================================================"
echo -e "Passed: ${GREEN}$success_count${NC}"
echo -e "Failed: ${RED}$fail_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
