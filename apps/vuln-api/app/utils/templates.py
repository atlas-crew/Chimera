"""
HTML templates for the demo application.
"""

DEMO_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title> Protected Demo Site - API Endpoints</title>
    <link rel="stylesheet" href="/static/api-styles.css">
</head>
<body>
    <div class="container">
        <h1>🛡️  Protected Demo Site - API Testing Platform</h1>

        <div class="status">
            ✅ <strong>Status:</strong> 150+ API endpoints active for WAF testing
        </div>

        <div class="demo-section">
            <h2>🏦 Banking & Financial Services</h2>
            <div class="endpoint"><span class="method post">POST</span><code>/api/v1/auth/login</code> - Banking portal authentication</div>
            <div class="endpoint"><span class="method get">GET</span><code>/api/v1/accounts/balance</code> - Account balance inquiry</div>
            <div class="endpoint"><span class="method get">GET</span><code>/api/v1/accounts/list</code> - Account enumeration</div>
            <div class="endpoint"><span class="method post">POST</span><code>/api/v1/transfers/wire</code> - Wire transfers</div>
            <div class="endpoint"><span class="method post">POST</span><code>/api/payments/process</code> - Payment processing</div>
        </div>

        <div class="demo-section">
            <h2>📱 Mobile Banking Security</h2>
            <div class="endpoint"><span class="method get">GET</span><code>/api/mobile/v2/config/app-settings</code> - Mobile app configuration</div>
            <div class="endpoint"><span class="method get">GET</span><code>/api/mobile/v2/auth/biometric/supported-methods</code> - Biometric methods</div>
            <div class="endpoint"><span class="method post">POST</span><code>/api/mobile/device/fingerprint</code> - Device fingerprinting</div>
            <div class="endpoint"><span class="method post">POST</span><code>/api/mobile/v2/auth/biometric/verify</code> - Biometric bypass</div>
            <div class="endpoint"><span class="method post">POST</span><code>/api/mobile/v2/auth/session/transfer</code> - Session hijacking</div>
            <div class="endpoint"><span class="method get">GET</span><code>/api/mobile/v2/admin/customer-accounts/list</code> - Admin access</div>
        </div>

        <div class="demo-section">
            <h2>🏥 Healthcare & HIPAA</h2>
            <div class="endpoint"><span class="method get">GET</span><code>/api/hipaa/directory</code> - Healthcare system discovery</div>
            <div class="endpoint"><span class="method get">GET</span><code>/api/providers/network/search</code> - Provider network enumeration</div>
            <div class="endpoint"><span class="method get">GET</span><code>/api/hipaa/records/patient</code> - Medical records access</div>
            <div class="endpoint"><span class="method get">GET</span><code>/api/medical/genetics/profiles</code> - Genetic information theft</div>
            <div class="endpoint"><span class="method get">GET</span><code>/api/medical/mental-health/sessions</code> - Mental health records</div>
            <div class="endpoint"><span class="method post">POST</span><code>/api/hipaa/transfer/encrypted</code> - Data exfiltration</div>
        </div>

        <div class="demo-section">
            <h2>🛒 E-commerce & Retail</h2>
            <div class="endpoint"><span class="method get">GET</span><code>/api/products/search</code> - Product catalog</div>
            <div class="endpoint"><span class="method post">POST</span><code>/api/cart/add</code> - Add items to cart</div>
            <div class="endpoint"><span class="method put">PUT</span><code>/api/cart/update</code> - Update cart quantities</div>
            <div class="endpoint"><span class="method post">POST</span><code>/api/checkout/process</code> - Checkout processing</div>
            <div class="endpoint"><span class="method post">POST</span><code>/api/pricing/calculate</code> - Price calculation</div>
        </div>

        <div class="demo-section">
            <h2>📋 Insurance Services</h2>
            <div class="endpoint"><span class="method post">POST</span><code>/api/claims/submit</code> - Claims submission</div>
            <div class="endpoint"><span class="method get">GET</span><code>/api/claims/history</code> - Claims history</div>
            <div class="endpoint"><span class="method put">PUT</span><code>/api/policies/POL-123456789/limits</code> - Policy limits</div>
            <div class="endpoint"><span class="method post">POST</span><code>/api/underwriting/risk-assessment</code> - Risk assessment</div>
        </div>

        <div class="demo-section">
            <h2>🔐 API Gateway & OAuth</h2>
            <div class="endpoint"><span class="method get">GET</span><code>/api/gateway/routes</code> - Route enumeration</div>
            <div class="endpoint"><span class="method get">GET</span><code>/api/oauth/authorize</code> - OAuth authorization</div>
            <div class="endpoint"><span class="method post">POST</span><code>/api/oauth/token</code> - Token requests</div>
            <div class="endpoint"><span class="method get">GET</span><code>/api/microservices/mesh</code> - Service mesh</div>
        </div>

        <div class="demo-section">
            <h2>⚖️ Regulatory & Compliance</h2>
            <div class="endpoint"><span class="method get">GET</span><code>/api/compliance/aml/monitor</code> - AML monitoring bypass</div>
            <div class="endpoint"><span class="method post">POST</span><code>/api/transactions/split</code> - Transaction structuring</div>
            <div class="endpoint"><span class="method post">POST</span><code>/api/reporting/sar</code> - Suspicious activity reports</div>
            <div class="endpoint"><span class="method post">POST</span><code>/api/kyc/verify</code> - Know Your Customer fraud</div>
            <div class="endpoint"><span class="method put">PUT</span><code>/api/compliance/override</code> - Compliance bypass</div>
            <div class="endpoint"><span class="method get">GET</span><code>/api/sanctions/check</code> - OFAC sanctions screening</div>
        </div>

        <h2>🧪 Test Commands</h2>
        <pre class="code-block">
# Banking authentication test
curl -X POST http://localhost:8880/api/v1/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"username": "demo@chimera.com", "password": "demo123"}'

# Mobile biometric bypass test
curl -X POST http://localhost:8880/api/mobile/v2/auth/biometric/verify \\
  -H "Content-Type: application/json" \\
  -d '{"biometric_template": "fake_fingerprint_data", "method": "fingerprint"}'

# HIPAA medical records access
curl -X GET "http://localhost:8880/api/hipaa/records/patient?patient_id=patient_789" \\
  -H "Authorization: Bearer PROVIDER-token"

# Compliance bypass test
curl -X PUT http://localhost:8880/api/compliance/override \\
  -H "Content-Type: application/json" \\
  -d '{"override_code": "COMPLIANCE-BYPASS-2024", "rule_id": "AML-001"}'

# E-commerce cart manipulation
curl -X PUT http://localhost:8880/api/cart/update \\
  -H "Content-Type: application/json" \\
  -d '{"product_id": "PROD-001", "quantity": -5}'

# Claims submission test
curl -X POST http://localhost:8880/api/claims/submit \\
  -H "Content-Type: application/json" \\
  -d '{"policy_number": "POL-123456", "claim_type": "auto", "amount": 5000}'
        </pre>

        <footer class="site-footer">
            <p>Powered by  WAF • <em>150+ API Endpoints for Comprehensive Testing</em></p>
        </footer>
    </div>
</body>
</html>
"""
