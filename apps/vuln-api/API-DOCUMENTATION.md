# Chimera - Comprehensive Documentation

> **Complete guide for the Flask API honeypot application with intentional vulnerabilities for WAF testing**

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Vulnerabilities](#vulnerabilities)
- [Testing](#testing)
- [Development](#development)
- [Configuration](#configuration)

## Overview

The Chimera is a Python Flask application serving as a honeypot with 456+ vulnerable endpoints designed to test and demonstrate  WAF capabilities. It simulates real-world applications with intentional security flaws for testing purposes.

### Key Features
- **456+ Vulnerable Endpoints** across 25+ blueprints and domains
- **Intentional Security Flaws** for WAF testing
- **Thread-Safe Data Layer** with validation bypass
- **Comprehensive Test Suite** with unit and security-focused coverage
- **Multiple API Patterns** (REST, GraphQL-like, SOAP-like)
- **Realistic Data Models** for various industries

> **Note on OpenAPI/Swagger**: The static OpenAPI specification (`docs/openapi.yaml`) is generated from the blueprint routes and aims to list the full endpoint surface. Schemas are intentionally minimal and some routes are conditional (e.g., database-vulnerable endpoints require `USE_DATABASE=true`). For deeper details, refer to the Blueprint Organization table below or inspect the `app/blueprints` source.

### Technology Stack
- **Framework**: Flask 2.3.3
- **Server**: Gunicorn with gevent workers
- **Testing**: Pytest with coverage reporting
- **Authentication**: JWT (including vulnerable "none" algorithm)
- **Data Storage**: In-memory thread-safe store

## Architecture

### Directory Structure
```
api-demo/
├── app/
│   ├── __init__.py                 # Flask app factory
│   ├── models/
│   │   └── dal.py                  # Data Access Layer (~450 lines)
│   ├── utils/
│   │   ├── validators.py           # Input validation (~200 lines)
│   │   ├── responses.py            # Response formatting (~180 lines)
│   │   ├── auth_helpers.py         # Auth utilities (~320 lines)
│   │   ├── demo_data.py            # Data seeding (~250 lines)
│   │   └── monitoring.py           # Logging/metrics (~150 lines)
│   └── blueprints/
│       ├── auth/                   # Authentication & identity
│       ├── banking/                # Financial operations
│       ├── healthcare/             # PHI, telehealth, pharmacy
│       ├── ecommerce/              # Cart, orders, marketplace
│       ├── saas/                   # Tenant isolation, SCIM, billing
│       ├── government/             # Citizen services, FOIA, alerts
│       ├── insurance/              # Claims, underwriting, brokers
│       ├── telecom/                # Subscriber, network, billing
│       ├── energy_utilities/       # Grid ops, outages, metering
│       ├── loyalty/                # Rewards & points abuse
│       ├── admin/                  # Admin operations
│       └── ...                     # payments, integrations, etc.
├── tests/
│   ├── unit/                       # Unit tests
│   └── integration/                # Integration tests (optional)
├── docs/                           # Documentation
├── static/                         # Static assets
├── app.py                          # Main application
├── gunicorn.conf.py               # Server configuration
├── pyproject.toml                # Dependencies
├── uv.lock                       # Locked dependency graph
├── Dockerfile                     # Container definition
└── Makefile                       # Build automation
```

### Blueprint Organization

The application is organized into domain-specific blueprints:

| Domain / Industry | Endpoints | Description |
|-------------------|-----------|-------------|
| **Admin** | ~19 | User management, system configuration, data export, and administrative overrides. |
| **Attack Sim** | ~24 | Simulation of kill-chain phases: reconnaissance, lateral movement, persistence, and exfiltration. |
| **Auth** | ~28 | Authentication flows including OAuth, MFA, SAML, API keys, and session management. |
| **Banking** | ~27 | Core banking operations: accounts, wire transfers, loans, KYC, and open banking. |
| **Checkout** | ~12 | E-commerce checkout flows: shipping, taxes, promotions, and payment processing. |
| **Compliance** | ~16 | Regulatory compliance features: AML monitoring, SAR reporting, and audit trails. |
| **Database Vuln** | ~8 | Dedicated endpoints for demonstrating various SQL injection techniques (Classic, Blind, Time-based). |
| **Ecommerce** | ~39 | Online marketplace features: product catalog, vendor management, inventory, and orders. |
| **Energy** | ~22 | Utility operations: grid dispatch, smart metering, outage management, and SCADA config. |
| **GenAI** | ~1 | LLM-based chat interfaces and prompt injection targets. |
| **Government** | ~30 | Public sector services: benefits, permits, licensing, FOIA requests, and citizen records. |
| **Healthcare** | ~27 | Medical systems: patient records (EMR), prescriptions, appointments, and HIPAA data. |
| **ICS / OT** | ~10 | Industrial control systems: PLC commands, setpoints, HMI interfaces, and sensor readings. |
| **Infrastructure** | ~19 | Cloud & DevOps targets: Kubernetes pods, service mesh, gateway routes, and secrets. |
| **Insurance** | ~42 | InsurTech operations: claims processing, underwriting, policy management, and premiums. |
| **Integrations** | ~13 | Third-party connectivity: webhooks, CRM sync, email gateways, and analytics. |
| **Loyalty** | ~14 | Rewards programs: points transfer, tier management, referrals, and cashback. |
| **Mobile** | ~13 | Mobile app backend: device fingerprinting, biometric auth, and app configuration. |
| **Payments** | ~19 | Payment gateway features: card processing, fraud rules, settlements, and disputes. |
| **SaaS** | ~30 | B2B SaaS features: multi-tenancy, billing/invoices, SSO/SCIM, and API key management. |
| **Security Ops** | ~8 | SOC workflows: incident creation, threat intelligence, and automated remediation. |
| **Telecom** | ~21 | Telco operations: subscriber profiles, SIM swap, network provisioning, and CDRs. |


### Data Access Layer

Thread-safe in-memory data store with:
- **CRUD Operations**: Create, Read, Update, Delete with locking
- **Validation Bypass**: `skip_validation=True` for vulnerable endpoints
- **Query Support**: Find by attributes, list all, count, exists
- **Metadata Tracking**: Automatic created_at/updated_at timestamps
- **Deep Copy**: Prevents external mutation of stored data

## Quick Start

### Local Development
```bash
# Navigate to api-demo
cd api-demo

# Install dependencies
uv sync --extra dev --frozen

# Run locally
uv run python app.py

# Access at http://localhost:5000
```

### Docker Deployment
```bash
# As part of WAF demo
./waf-demo --sites=demo start

# Or standalone
docker build -t demo-api ./api-demo
docker run -p 8080:80 demo-api
```

### Running Tests
```bash
# All tests
make test

# Quick tests only
make test-quick

# With coverage
make test-coverage

# Specific domain
pytest tests/unit/test_auth_routes.py -v
```

## API Endpoints

Below is a representative list of high-signal endpoints (especially those used by Gauntlet target configs). For the full surface area, review `app/blueprints/**/routes.py`.

### Authentication Domain (31 endpoints)

#### Core Authentication
- `POST /api/v1/auth/login` - User login (SQL injection)
- `POST /api/v1/auth/logout` - Session termination
- `POST /api/v1/auth/register` - User registration (enumeration)
- `POST /api/v1/auth/forgot` - Password reset (predictable tokens)
- `POST /api/v1/auth/reset` - Complete password reset
- `POST /api/v1/auth/verify` - Email/phone verification
- `POST /api/v1/auth/refresh` - Token refresh (no rotation)

#### Multi-Factor Authentication
- `POST /api/v1/auth/mfa/setup` - Setup MFA
- `POST /api/v1/auth/mfa/verify` - Verify MFA code
- `GET /api/v1/auth/mfa/backup` - Get backup codes
- `POST /api/v1/auth/mfa/disable` - Disable MFA

#### OAuth/Social
- `GET /api/v1/auth/oauth/authorize` - OAuth authorization
- `POST /api/v1/auth/oauth/token` - Token exchange
- `GET /api/v1/auth/social/google` - Google SSO
- `GET /api/v1/auth/social/facebook` - Facebook SSO

### Banking Domain (35+ endpoints)

#### Account Management
- `GET /api/v1/banking/accounts` - List accounts (IDOR)
- `GET /api/v1/banking/accounts/<account_id>` - Account details (IDOR)
- `POST /api/v1/banking/accounts/create` - Create account
- `GET /api/v1/banking/balance` - Balance lookup (parameter pollution)

#### Transactions & Statements
- `POST /api/v1/banking/transfer` - Fund transfer (tampering/race)
- `POST /api/v1/banking/transfer/bulk` - Bulk transfer (amplifies race)
- `GET /api/v1/banking/transactions` - Transaction history (IDOR)
- `GET /api/v1/banking/transactions/<transaction_id>` - Transaction details (IDOR)
- `GET /api/v1/banking/statements` - Download statements (IDOR)
- `POST /api/v1/banking/wire-transfer` - Wire transfer (AML bypass)
- `GET /api/v1/banking/beneficiaries/<beneficiary_id>` - Beneficiary lookup (IDOR)

#### Cards
- `GET /api/v1/banking/cards` - List cards (data exposure)
- `POST /api/v1/banking/cards/activate` - Activate card (brute-force risk)
- `POST /api/v1/banking/cards/block` - Block card (IDOR)

#### Recovery & Device Trust
- `POST /api/v1/banking/account-recovery` - Account recovery (bypass)
- `POST /api/v1/banking/device/verify` - Device trust (override)
- `POST /api/v1/banking/session/terminate` - Session termination (abuse)

#### Loans & Credit
- `POST /api/v1/banking/loans/apply` - Loan application (bypass)
- `POST /api/v1/banking/loans/underwrite` - Underwriting override
- `PUT /api/v1/banking/credit/limit` - Credit limit override

#### KYC & Compliance
- `GET /api/v1/banking/kyc/documents/export` - KYC document export (PII exposure)

#### Open Banking & Consent
- `POST /api/v1/banking/consents` - Create consent (scope escalation)
- `POST /api/v1/banking/consents/revoke` - Revoke consent (audit bypass)
- `POST /api/v1/banking/open-banking/token` - Token exchange (replay)

#### Remote Deposit & Wires
- `POST /api/v1/banking/checks/deposit` - Remote check deposit (XXE risk)
- `POST /api/v1/banking/wires/swift` - SWIFT wire transfer (logic flaw)

#### Payments
- `POST /api/v1/payments/process` - Process payment
- `POST /api/v1/payments/recurring` - Setup recurring
- `GET /api/v1/payments/methods` - Payment methods
- `POST /api/v1/payments/tokenize` - Tokenize card

### Healthcare Domain (30+ endpoints)

#### Patient Records
- `GET /api/v1/healthcare/records` - List records (PHI exposure)
- `GET /api/v1/healthcare/records/<id>` - Patient details
- `POST /api/v1/healthcare/records/upload` - Upload documents
- `GET /api/v1/healthcare/records/search` - Search records (SQL injection)
- `GET /api/v1/healthcare/providers/<provider_id>` - Provider directory (IDOR)
- `GET /api/v1/healthcare/lab-results/export` - Lab results export (PHI exposure)
- `GET /api/v1/healthcare/imaging/<record_id>/download` - Imaging download (IDOR)

#### Prescriptions
- `GET /api/v1/healthcare/prescriptions` - List prescriptions
- `POST /api/v1/healthcare/prescriptions` - Create prescription (forgery)
- `POST /api/v1/healthcare/prescriptions/refill` - Request refill
- `POST /api/v1/healthcare/prescriptions/validate` - Validate prescription
- `GET /api/v1/healthcare/prescriptions/history` - Medication history (IDOR)
- `GET /api/v1/healthcare/prescriptions/export` - Bulk export (PHI exposure)

#### Telehealth & Pharmacy Services
- `POST /api/v1/healthcare/telehealth/session` - Session hijack
- `POST /api/v1/healthcare/pharmacy/prior-auth` - Prior auth override

#### Healthcare Insurance (V1)
- `POST /api/v1/healthcare/insurance/claims` - Claims submission
- `GET /api/v1/healthcare/insurance/eligibility` - Eligibility lookup (IDOR)
- `POST /api/v1/healthcare/insurance/preauth` - Pre-auth override

#### Insurance (Legacy Namespace)
- `POST /api/v1/insurance/claims` - Submit claim
- `GET /api/v1/insurance/claims/<claim_id>` - Claim status (IDOR)
- `GET /api/v1/insurance/coverage` - Coverage check (data exposure)

### Ecommerce Domain (30+ endpoints)

#### Cart & Checkout
- `POST /api/v1/ecommerce/cart/add` - Cart add (price tampering)
- `POST /api/v1/ecommerce/cart/checkout` - Checkout (race/discount abuse)
- `GET /api/v1/ecommerce/cart/<cart_id>` - Cart details (IDOR)
- `POST /api/v1/ecommerce/cart/apply-discount` - Discount stacking
- `POST /api/v1/ecommerce/checkout/submit` - Checkout submit (race)
- `POST /api/v1/ecommerce/checkout/complete` - Payment bypass

#### Catalog & Inventory
- `GET /api/v1/ecommerce/products` - Product scraping
- `GET /api/v1/ecommerce/products/search` - Search (SQLi)
- `PUT /api/v1/ecommerce/inventory/<item_id>` - Inventory manipulation
- `POST /api/v1/ecommerce/inventory/reserve` - Reservation abuse
- `GET /api/v1/ecommerce/pricing/export` - Pricing export
- `PUT /api/v1/ecommerce/pricing/override` - Pricing override (tampering)

#### Orders, Returns & Payments
- `GET /api/v1/ecommerce/orders/<order_id>` - Order details (IDOR)
- `GET /api/v1/ecommerce/orders/export` - Order export (PII exposure)
- `POST /api/v1/ecommerce/orders/<order_id>/refund` - Refund fraud
- `POST /api/v1/ecommerce/returns/request` - Return abuse
- `PUT /api/v1/ecommerce/returns/approve` - Approval bypass
- `POST /api/v1/ecommerce/chargebacks/submit` - Chargeback fraud
- `GET /api/v1/ecommerce/payment-methods/<method_id>` - Payment method IDOR
- `POST /api/v1/ecommerce/gift-cards/generate` - Gift card abuse
- `GET /api/v1/ecommerce/gift-cards/<code>/balance` - Gift card balance scraping

#### Customers & Loyalty
- `GET /api/v1/ecommerce/customers/export` - Customer export (PII)
- `PUT /api/v1/ecommerce/customers/<customer_id>/email` - Account takeover
- `GET /api/v1/ecommerce/customers/<customer_id>/wishlist` - Wishlist scraping
- `POST /api/v1/ecommerce/loyalty/points/transfer` - Points transfer abuse
- `PUT /api/v1/ecommerce/loyalty/tiers` - Tier manipulation
- `PUT /api/v1/ecommerce/loyalty/redeem` - Redemption abuse

#### Marketplace Vendors
- `POST /api/v1/ecommerce/vendors/register` - Vendor onboarding bypass
- `GET /api/v1/ecommerce/vendors/<vendor_id>` - Vendor portal IDOR
- `POST /api/v1/ecommerce/vendors/payouts` - Payout manipulation
- `POST /api/v1/ecommerce/vendor/webhooks/register` - Vendor webhook (Blind SSRF)

### Loyalty Domain (15+ endpoints)

#### Points & Tiers
- `POST /api/loyalty/points/transfer` - Points transfer abuse
- `PUT /api/loyalty/points/redeem` - Redemption without checks
- `PUT /api/loyalty/tiers/status` - Tier manipulation
- `GET /api/loyalty/tiers/requirements` - Tier requirements exposure
- `GET /api/loyalty/program/details` - Program details exposure
- `GET /api/loyalty/points/exchange-rates` - Exchange rate abuse

#### Rewards & Referrals
- `POST /api/referrals/system/reward` - Referral reward abuse
- `POST /api/cashback/process` - Cashback manipulation
- `GET /api/loyalty/rewards/gift-cards` - Reward scraping
- `POST /api/loyalty/accounts/link` - Account linking bypass

#### Exports & Admin
- `GET /api/loyalty/customers/export` - Customer export (PII)
- `GET /api/loyalty/transactions/export` - Transaction export
- `POST /api/loyalty/system/configuration` - Config override
- `PUT /api/loyalty/audit-logs` - Audit log tampering

### GenAI Domain (4 endpoints)

#### LLM Interactions & RAG
- `POST /api/v1/genai/chat` - Chat interface (Prompt Injection)
- `POST /api/v1/genai/knowledge/upload` - RAG Upload (Unrestricted File Upload)
- `POST /api/v1/genai/agent/browse` - AI Agent Browse (SSRF)
- `GET /api/v1/genai/models/config` - Model Config (Sensitive Data Exposure)

### SaaS Domain (30+ endpoints)

#### Tenant Isolation & Data Exposure
- `GET /api/v1/saas/tenants/<id>/projects` - Tenant projects (IDOR)
- `GET /api/v1/saas/tenants/<id>/export` - Tenant export (PII exposure)
- `POST /api/v1/saas/tenants/switch` - Tenant switch (membership bypass)
- `GET /api/v1/saas/share/links` - Shared link scraping
- `PUT /api/v1/saas/tenants/<id>/settings` - Workspace settings (tampering)
- `POST /api/v1/saas/org/invites` - Organization invites (bypass)

#### Identity & Access Control
- `POST /api/v1/saas/auth/sso/callback` - SSO assertion tampering
- `PUT /api/v1/saas/auth/saml/config` - SAML config tampering
- `POST /api/v1/saas/auth/token/refresh` - Token replay (no rotation)
- `POST /api/v1/saas/auth/mfa/verify` - MFA bypass
- `PUT /api/v1/saas/users/<id>/role` - Role escalation
- `POST /api/v1/saas/auth/password-reset` - Password reset IDOR
- `POST /api/v1/saas/sessions/revoke` - Session revocation abuse

#### Billing & Usage Abuse
- `POST /api/v1/saas/billing/usage` - Usage overflow (quota bypass)
- `GET /api/v1/saas/billing/invoices/<id>` - Invoice download (IDOR)
- `POST /api/v1/saas/billing/apply-coupon` - Coupon stacking abuse
- `PUT /api/v1/saas/billing/seats` - Seat count manipulation
- `POST /api/v1/saas/billing/upgrade` - Plan upgrade bypass

#### Audit Logs & Retention
- `GET /api/v1/saas/audit/logs` - Audit log export (data exposure)
- `PUT /api/v1/saas/audit/logs/<id>` - Audit log tampering
- `PUT /api/v1/saas/audit/retention` - Retention override

#### SCIM & Provisioning
- `POST /api/v1/saas/scim/users` - SCIM user create (bypass)
- `DELETE /api/v1/saas/scim/users/<id>` - SCIM user delete
- `POST /api/v1/saas/scim/groups/sync` - Group sync (force)

#### API Keys & Tokens
- `POST /api/v1/saas/api-keys` - API key creation (scope abuse)
- `GET /api/v1/saas/api-keys/export` - API key export
- `PUT /api/v1/saas/api-keys/rotate` - Key rotation override

#### Webhooks & Integrations
- `POST /api/v1/saas/webhooks/register` - Webhook registration (SSRF risk)
- `PUT /api/v1/saas/webhooks/secret` - Secret override
- `POST /api/v1/saas/webhooks/replay` - Replay injection

### Government Domain (30+ endpoints)

#### Citizen Services & Casework
- `GET /api/v1/gov/cases/<id>` - Case details (IDOR)
- `GET /api/v1/gov/benefits/search` - Benefits search (SQL injection)
- `PUT /api/v1/gov/benefits/<application_id>/eligibility` - Eligibility override
- `POST /api/v1/gov/service-requests` - Service request tampering
- `GET /api/v1/gov/records/export` - Records export (data exfiltration)
- `PUT /api/v1/gov/cases/<id>/status` - Case status manipulation
- `PUT /api/v1/gov/cases/<case_id>/reassign` - Case reassignment bypass

#### Identity & Access Control
- `GET /api/v1/gov/identity/cards/<id>` - Access card lookup (IDOR)
- `PUT /api/v1/gov/users/<id>/roles` - Privilege escalation
- `POST /api/v1/gov/auth/mfa/verify` - MFA bypass
- `POST /api/v1/gov/auth/sso/callback` - Federation assertion tampering
- `GET /api/v1/gov/identity/credentials/export` - Credential export

#### Mission Data Integrity
- `DELETE /api/v1/gov/audit-logs/<id>` - Audit log tampering
- `GET /api/v1/gov/records/bulk-export` - Bulk export
- `POST /api/v1/gov/data/classify` - Classification bypass
- `GET /api/v1/gov/cases/history` - Case history SQL injection
- `PUT /api/v1/gov/records/<id>` - Record tampering

#### Licensing & Permits
- `POST /api/v1/gov/permits/apply` - Permit application bypass
- `PUT /api/v1/gov/permits/<permit_id>/approve` - Permit approval override
- `GET /api/v1/gov/licenses/<license_id>` - License lookup (IDOR)
- `GET /api/v1/gov/licenses/export` - License export (PII exposure)

#### Grants & Assistance
- `POST /api/v1/gov/grants/apply` - Grant application abuse
- `PUT /api/v1/gov/grants/<grant_id>/award` - Award manipulation
- `POST /api/v1/gov/grants/disburse` - Disbursement bypass

#### Public Records & FOIA
- `POST /api/v1/gov/foia/requests` - FOIA request tampering
- `GET /api/v1/gov/foia/export` - FOIA export (data exfiltration)
- `PUT /api/v1/gov/foia/requests/<request_id>/status` - Status override

#### Emergency Alerts & Broadcasts
- `POST /api/v1/gov/alerts/broadcast` - Unauthorized broadcast
- `PUT /api/v1/gov/alerts/<alert_id>/suppress` - Alert suppression
- `GET /api/v1/gov/alerts/target` - Geo targeting override

### Telecom Domain (25+ endpoints)

#### Subscriber Portal & Identity
- `GET /api/v1/telecom/subscribers/<id>/profile` - Subscriber profile (IDOR)
- `POST /api/v1/telecom/subscribers/<id>/sim-swap` - SIM swap bypass
- `PUT /api/v1/telecom/subscribers/<id>/plan` - Plan change tampering
- `GET /api/v1/telecom/subscribers/export` - Subscriber export (PII exposure)
- `POST /api/v1/telecom/devices/bind` - Device binding bypass

#### Network Provisioning & Access
- `GET /api/v1/telecom/network/towers/<id>` - Tower access (IDOR)
- `POST /api/v1/telecom/network/provision` - Provisioning bypass
- `PUT /api/v1/telecom/network/throttle` - Throttle manipulation
- `GET /api/v1/telecom/network/cdr/export` - CDR export (data exposure)
- `PUT /api/v1/telecom/imei/blacklist` - IMEI blacklist override

#### Billing & Usage
- `GET /api/v1/telecom/billing/invoices/<id>` - Invoice IDOR
- `PUT /api/v1/telecom/billing/adjustments` - Billing adjustment tampering
- `POST /api/v1/telecom/billing/payment-methods` - Payment method bypass
- `POST /api/v1/telecom/billing/refunds` - Refund abuse

#### Porting & SIM Integrity
- `POST /api/v1/telecom/porting/requests` - Port-out bypass
- `GET /api/v1/telecom/porting/requests/<id>` - Porting status (IDOR)
- `PUT /api/v1/telecom/porting/swap` - Number swap tampering
- `GET /api/v1/telecom/porting/export` - Porting export (PII exposure)
- `POST /api/v1/telecom/roaming/override` - Roaming override

#### Integrations & API Access
- `GET /api/v1/telecom/api-keys/export` - API key export
- `POST /api/v1/telecom/integrations/webhooks` - Webhook registration (SSRF risk)
- `POST /api/v1/telecom/integrations/cdr/stream` - CDR stream bypass
- `POST /api/v1/telecom/integrations/device-activate` - Device activation bypass

### Energy & Utilities Domain (25+ endpoints)

#### Grid Operations & Dispatch
- `POST /api/v1/energy-utilities/grid/dispatch` - Dispatch override
- `POST /api/v1/energy-utilities/grid/load-shed` - Load shed bypass
- `PUT /api/v1/energy-utilities/grid/breakers/<id>` - Breaker control (IDOR)
- `GET /api/v1/energy-utilities/grid/config/export` - Grid config export
- `POST /api/v1/energy-utilities/demand-response/dispatch` - Demand response override

#### Outage Management & Restoration
- `GET /api/v1/energy-utilities/outages/<id>` - Outage status (IDOR)
- `POST /api/v1/energy-utilities/outages/dispatch` - Crew dispatch tampering
- `PUT /api/v1/energy-utilities/outages/restore` - Restoration override
- `GET /api/v1/energy-utilities/outages/export` - Outage export (data exposure)

#### Smart Metering & Remote Actions
- `GET /api/v1/energy-utilities/meters/<id>/readings` - Meter readings (IDOR)
- `POST /api/v1/energy-utilities/meters/<id>/disconnect` - Disconnect bypass
- `PUT /api/v1/energy-utilities/meters/firmware` - Firmware update tampering
- `GET /api/v1/energy-utilities/meters/export` - Meter data export

#### Billing & Customer Operations
- `PUT /api/v1/energy-utilities/billing/adjustments` - Billing adjustment tampering
- `PUT /api/v1/energy-utilities/billing/autopay` - Autopay bypass
- `POST /api/v1/energy-utilities/billing/refunds` - Refund abuse
- `GET /api/v1/energy-utilities/customers/<id>` - Customer lookup (IDOR)
- `PUT /api/v1/energy-utilities/tariffs/override` - Tariff override

#### Asset Integrity & SCADA
- `GET /api/v1/energy-utilities/scada/config/export` - SCADA config export
- `PUT /api/v1/energy-utilities/assets/maintenance` - Maintenance override
- `POST /api/v1/energy-utilities/assets/calibration` - Sensor calibration tamper
- `GET /api/v1/energy-utilities/assets/<id>` - Asset registry (IDOR)
- `POST /api/v1/energy-utilities/der/interconnection/approve` - DER interconnection bypass

### Insurance Domain (40+ endpoints)

#### Claims Processing
- `GET /claims/portal` - Claims portal entry
- `POST /api/claims/submit` - Submit claim (fraud risk)
- `GET /api/claims/history` - Claims history (IDOR)
- `PUT /api/claims/<id>/status` - Claim status update (authorization bypass)
- `POST /api/claims/duplicate` - Duplicate claim (fraud)
- `POST /api/claims/photos/upload` - Evidence upload (validation bypass)
- `POST /api/claims/bulk-export` - Claims export (data exfiltration)
- `GET /api/claims/fraud-indicators` - Fraud indicators exposure
- `POST /api/claims/expedite` - Expedite claims (workflow bypass)
- `PUT /api/claims/amounts/inflate` - Inflate claim amounts

#### Policies & Underwriting
- `PUT /api/policies/<id>/limits` - Policy limits update (bypass)
- `GET /api/policies/search` - Policy search (data exposure)
- `PUT /api/policies/coverage-limits` - Coverage limit manipulation
- `GET /api/policies/pricing-models` - Pricing model exposure
- `POST /api/policies/backdoor` - Policy backdoor access
- `POST /api/policies/bulk-modify` - Bulk modifications
- `POST /api/underwriting/risk-assessment` - Risk assessment override
- `GET /api/underwriting/rules` - Underwriting rules exposure
- `POST /api/underwriting/override` - Underwriting override
- `GET /api/underwriting/export` - Underwriting export
- `PUT /api/actuarial/models/modify` - Actuarial model tampering
- `GET /api/risk/factors` - Risk factors exposure
- `PUT /api/risk/scores/manipulate` - Risk score manipulation
- `POST /api/premiums/calculate` - Premium calculation tampering

#### Insurance V1 (Gauntlet Targets)
- `GET /api/v1/insurance/claims/<claim_id>` - Claim details (IDOR)
- `GET /api/v1/insurance/claims/search` - Claims search (SQLi)
- `PUT /api/v1/insurance/claims/<claim_id>/payout` - Payout manipulation
- `GET /api/v1/insurance/claims/export` - Claims export (PII exposure)
- `POST /api/v1/insurance/claims/evidence/upload` - Evidence upload bypass
- `POST /api/v1/insurance/claims/override` - Fraud controls override
- `POST /api/v1/insurance/claims/settlement` - Settlement override
- `GET /api/v1/insurance/policies/<policy_id>` - Policy details (IDOR)
- `POST /api/v1/insurance/policies/<policy_id>/endorse` - Policy endorsement tampering
- `PUT /api/v1/insurance/policies/<policy_id>/cancel` - Policy cancellation override
- `POST /api/v1/insurance/underwriting/approve` - Underwriting bypass
- `PUT /api/v1/insurance/policies/<policy_id>/premium` - Premium tampering
- `POST /api/v1/insurance/policies/<policy_id>/beneficiary` - Beneficiary change
- `GET /api/v1/insurance/policies/<policy_id>/documents/export` - Document export
- `PUT /api/v1/insurance/risk/scores/manipulate` - Risk score manipulation
- `POST /api/v1/insurance/billing/tokenize` - Tokenization abuse
- `GET /api/v1/insurance/billing/invoices/<invoice_id>` - Invoice IDOR
- `POST /api/v1/insurance/billing/refund` - Refund abuse
- `PUT /api/v1/insurance/billing/autopay` - Autopay bypass
- `GET /api/v1/insurance/billing/statements` - Statements scraping
- `GET /api/v1/insurance/brokers/<broker_id>` - Broker portal IDOR
- `GET /api/v1/insurance/brokers/commissions/export` - Commissions export
- `PUT /api/v1/insurance/brokers/clients/<client_id>` - Broker client tampering

### Admin Domain (35 endpoints)

#### User Management
- `GET /api/v1/admin/users` - List users
- `POST /api/v1/admin/users` - Create user
- `PUT /api/v1/admin/users/<id>` - Update user (privilege escalation)
- `DELETE /api/v1/admin/users/<id>` - Delete user
- `POST /api/v1/admin/users/impersonate` - User impersonation

#### System Operations
- `GET /api/v1/admin/config` - System configuration (info disclosure)
- `POST /api/v1/admin/config` - Update config
- `POST /api/v1/admin/backup` - Trigger backup
- `GET /api/v1/admin/logs` - View logs (path traversal)
- `POST /api/v1/admin/execute` - Execute command (RCE)

#### Data Export
- `GET /api/v1/admin/export/users` - Export users (data exfiltration)
- `GET /api/v1/admin/export/transactions` - Export transactions
- `GET /api/v1/admin/export/audit` - Export audit logs
- `POST /api/v1/admin/reports/generate` - Generate reports

## Vulnerabilities

### Intentional Security Flaws

The application contains 50+ types of vulnerabilities for testing:

#### Authentication & Authorization
- **SQL Injection**: Login bypass via `' OR '1'='1`
- **JWT None Algorithm**: Token signature bypass
- **Session Fixation**: Predictable session IDs
- **Weak Passwords**: No complexity requirements
- **User Enumeration**: Different responses for valid/invalid users
- **Privilege Escalation**: Role manipulation
- **IDOR**: Direct object references without authorization

#### Input Validation
- **XSS**: Reflected and stored XSS in multiple endpoints
- **XXE**: XML external entity injection
- **LDAP Injection**: In authentication queries
- **Command Injection**: OS command execution
- **Path Traversal**: File system access
- **SSRF**: Server-side request forgery
- **Mass Assignment**: Overwrite protected attributes

#### Business Logic
- **Race Conditions**: Double-spend vulnerabilities
- **Integer Overflow**: Balance calculations
- **Price Manipulation**: Negative quantities
- **Discount Stacking**: Multiple coupon application
- **Time-based Attacks**: TOCTOU vulnerabilities

#### Data Exposure
- **PHI Leakage**: Unprotected medical records
- **PII Exposure**: Customer data in responses
- **Debug Information**: Stack traces in production
- **Configuration Disclosure**: Sensitive settings exposed
- **Log Injection**: Malicious log entries

### Testing Vulnerabilities

#### Quick Vulnerability Tests
```bash
# SQL Injection
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin'\'' OR '\''1'\''='\''1","password":"any"}'

# XSS in search
curl "http://localhost:8080/api/v1/healthcare/records/search?q=<script>alert('XSS')</script>"

# Path Traversal
curl "http://localhost:8080/api/v1/admin/logs?file=../../../../etc/passwd"

# Command Injection
curl -X POST http://localhost:8080/api/v1/admin/execute \
  -H "Content-Type: application/json" \
  -d '{"command":"ls; cat /etc/passwd"}'

# JWT None Algorithm
curl -H "Authorization: Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoiYWRtaW4ifQ."
```

## Testing

### Test Organization

```
tests/
├── unit/                    # Component tests
│   ├── test_dal.py
│   ├── test_validators.py
│   ├── test_responses.py
│   ├── test_auth_helpers.py
│   ├── test_auth_routes.py
│   ├── test_banking_routes.py
│   ├── test_healthcare_routes.py
│   ├── test_government_routes.py
│   ├── test_saas_routes.py
│   ├── test_insurance_routes.py
│   ├── test_telecom_routes.py
│   ├── test_energy_utilities_routes.py
│   └── test_admin_routes.py
└── integration/             # Optional/expanding integration suite
```

### Running Tests

```bash
# Full suite
make test

# Unit tests (with coverage)
make test-unit

# Quick tests
make test-quick

# Integration tests
make test-integration

# Vulnerability & smoke tests
make test-vulnerability
make test-smoke

# Coverage gate (80%)
make test-coverage

# HTML report
make test-report

# Specific test file
make test-file FILE=tests/unit/test_auth_routes.py
```

### Test Coverage

Coverage is enforced at 80% for unit tests. Run `make test-coverage` or `make test-unit` for current stats.

## Development

### Adding New Endpoints

1. **Create Blueprint** (if new domain):
```python
# app/blueprints/newdomain/routes.py
from flask import Blueprint, request, jsonify
from app.utils.responses import success_response, error_response
from app.utils.validators import validate_input

newdomain_bp = Blueprint('newdomain', __name__)

@newdomain_bp.route('/api/v1/newdomain/endpoint', methods=['POST'])
def new_endpoint():
    # Validation (optional for vulnerable endpoints)
    errors = validate_input(request.json, {
        'field': {'required': True, 'type': 'string'}
    })
    if errors:
        return error_response(errors, 400)

    # Business logic
    result = process_request(request.json)

    return success_response(result)
```

2. **Register Blueprint**:
```python
# app/__init__.py
from app.blueprints.newdomain.routes import newdomain_bp
app.register_blueprint(newdomain_bp)
```

3. **Add Tests**:
```python
# tests/unit/test_newdomain_routes.py
def test_new_endpoint(client):
    response = client.post('/api/v1/newdomain/endpoint',
                          json={'field': 'value'})
    assert response.status_code == 200
```

### Adding Vulnerabilities

To add intentional vulnerabilities:

```python
# Skip validation for vulnerable endpoints
from app.models.dal import DataAccessLayer

# Vulnerable: No validation
dal = DataAccessLayer()
result = dal.find('users', {'username': request.args.get('user')},
                  skip_validation=True)

# Vulnerable: SQL injection simulation
query = f"SELECT * FROM users WHERE name = '{request.args.get('name')}'"

# Vulnerable: Command injection
import os
os.system(f"echo {request.json.get('input')}")

# Vulnerable: XSS
return f"<html><body>Hello {request.args.get('name')}</body></html>"
```

### Security Controls

For testing different WAF behaviors:

```python
# app/utils/security.py

# Rate limiting
from flask_limiter import Limiter
limiter = Limiter(key_func=lambda: request.remote_addr)

# Input sanitization (can be bypassed)
def sanitize_input(data, bypass=False):
    if bypass or request.headers.get('X-Bypass-Security'):
        return data
    # Sanitization logic
    return clean_data

# Audit logging
def audit_log(action, user, details):
    logger.info(f"AUDIT: {action} by {user}: {details}")
```

## Configuration

### Environment Variables

```bash
# Flask configuration
FLASK_ENV=development|production
FLASK_DEBUG=0|1
SECRET_KEY=your-secret-key

# Security settings
ENABLE_VULNERABILITIES=true|false
BYPASS_VALIDATION=true|false
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR

# Database (future)
DATABASE_URL=sqlite:///app.db
REDIS_URL=redis://localhost:6379

# Performance
GUNICORN_WORKERS=4
WORKER_CLASS=gevent
WORKER_CONNECTIONS=1000
```

### Gunicorn Configuration

```python
# gunicorn.conf.py
import os

workers = int(os.getenv('GUNICORN_WORKERS', '4'))
worker_class = 'gevent'  # CRITICAL: Use async workers for handling concurrent requests
worker_connections = 1000  # Each worker can handle 1000 concurrent connections
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
```

**Important**: The application uses `gevent` workers for async handling. This provides:
- 4,000 total concurrent connections (4 workers × 1000 connections)
- Non-blocking I/O for better performance
- Proper handling of traffic generation (100+ RPS)
- Support for concurrent attack simulation

Never change to `sync` workers as this would limit the application to only 4 concurrent requests total, causing immediate failure under load.

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev

COPY app/ /app/app/
COPY app.py /app/app.py
COPY static /app/static

EXPOSE 80
ENV PORT=80
CMD ["uv", "run", "python", "app.py"]
```

## Deployment

### With WAF Demo

```bash
# Start as default backend
./waf-demo --sites=demo start

# Access through WAF
curl -H 'Host: demo.site' http://localhost:8880/api/v1/auth/login
```

### Standalone Container

```bash
# Build
docker build -t api-demo ./api-demo

# Run
docker run -d \
  --name api-demo \
  -p 8080:80 \
  -e ENABLE_VULNERABILITIES=true \
  api-demo

# Test
curl http://localhost:8080/api/v1/auth/login
```

### Production Considerations

⚠️ **WARNING**: This application contains intentional vulnerabilities. **NEVER deploy to production or expose to the internet.**

For demo environments:
1. Run only in isolated networks
2. Use WAF protection
3. Monitor all access
4. Regular cleanup/reset
5. Access control lists

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process
lsof -i :5000
# Kill process
kill $(lsof -t -i:5000)
```

#### Import Errors
```bash
# Ensure in api-demo directory
cd api-demo
# Install dependencies
uv sync --extra dev --frozen
```

#### Test Failures
```bash
# Clean pytest cache
rm -rf .pytest_cache
# Run with verbose output
uv run pytest -vv tests/unit/test_auth_routes.py
```

#### Memory Issues
```bash
# Limit worker connections
export WORKER_CONNECTIONS=100
# Reduce workers
export GUNICORN_WORKERS=2
```

## Quick Reference

### Essential Commands
```bash
# Start locally
uv run python app.py

# Run tests
make test

# Test specific vulnerability
curl "http://localhost:8080/api/v1/auth/login" \
  -d '{"username":"admin'\'' OR '\''1'\''='\''1","password":"x"}'

# Check health
curl http://localhost:8080/health

# View logs
docker logs demo-waf-site
```

### Key Files
- `app.py` - Main application entry point
- `app/models/dal.py` - Data access layer
- `app/blueprints/*/routes.py` - Endpoint implementations
- `tests/unit/*.py` - Unit tests
- `pyproject.toml` - Dependencies
- `uv.lock` - Locked dependency graph
- `gunicorn.conf.py` - Server configuration

### Useful Endpoints for Testing
```bash
# Auth bypass
/api/v1/auth/login

# Data exposure
/api/v1/healthcare/records
/api/v1/admin/export/users

# Command injection
/api/v1/admin/execute

# Path traversal
/api/v1/admin/logs?file=../../etc/passwd

# XSS
/api/v1/healthcare/records/search?q=<script>alert(1)</script>
```

## Support

For issues or questions:
1. Check this documentation
2. Review test files for examples
3. Check logs: `docker logs demo-waf-site`
4. Report issues: [GitHub Issues](https://github.com/chimera/demo-targets/issues)

---

**Last Updated**: January 6, 2026
**Version**: 2.1
**Total Endpoints**: 450+
**Vulnerabilities**: 50+ types
